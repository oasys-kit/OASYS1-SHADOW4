
import os, copy, numpy
from shadow4.beam.s4_beam import S4Beam

class ShadowData:
    class ScanningData(object):
        def __init__(self,
                     scanned_variable_name,
                     scanned_variable_value,
                     scanned_variable_display_name,
                     scanned_variable_um,
                     additional_parameters={}):
            self.__scanned_variable_name = scanned_variable_name
            self.__scanned_variable_value = scanned_variable_value
            self.__scanned_variable_display_name = scanned_variable_display_name
            self.__scanned_variable_um = scanned_variable_um
            self.__additional_parameters=additional_parameters

        @property
        def scanned_variable_name(self):
            return self.__scanned_variable_name

        @property
        def scanned_variable_value(self):
            return self.__scanned_variable_value

        @property
        def scanned_variable_display_name(self):
            return self.__scanned_variable_display_name

        @property
        def scanned_variable_um(self):
            return self.__scanned_variable_um

        def has_additional_parameter(self, name):
            return name in self.__additional_parameters.keys()

        def get_additional_parameter(self, name):
            return self.__additional_parameters[name]

    def __init__(self, beam=None, footprint=None, number_of_rays=0, beamline=None):
        if (beam is None):
            if number_of_rays > 0: self.__beam = S4Beam(number_of_rays)
            else:                  self.__beam = S4Beam()
            self.__footprint = None
        else:
            self.__beam      = beam
            self.__footprint = footprint

        self.__scanning_data = None
        self.__initial_flux  = None
        self.__beamline      = beamline  # added by srio

    @property
    def beam(self):
        return self.__beam

    @beam.setter
    def beam(self, beam):
        self.__beam = beam

    @property
    def footprint(self):
        return self.__footprint

    @footprint.setter
    def footprint(self, footprint):
        self._footprint = footprint

    @property
    def beamline(self):
        return self.__beamline

    @beamline.setter
    def beamline(self, beamline):
        self.__beamline = beamline

    @property
    def initial_flux(self):
        return self.__initial_flux

    @initial_flux.setter
    def initial_flux(self, initial_flux):
        self.__initial_flux = initial_flux

    @property
    def scanning_data(self):
        return self.__scanning_data

    @scanning_data.setter
    def scanning_data(self, scanning_data : ScanningData):
        self.__scanning_data = scanning_data

    def get_flux(self, nolost=1):
        if not self.__beam is None and not self.__initial_flux is None:
            return (self.__beam.intensity(nolost) / self.get_number_of_rays(0)) * self.get_initial_flux()
        else:
            return None

    def get_number_of_rays(self, nolost=0):
        if not hasattr(self.__beam, "rays"): return 0
        if nolost == 0:   return self.__beam.rays.shape[0]
        elif nolost == 1: return self.__beam.rays[numpy.where(self.__beam.rays[:, 9] > 0)].shape[0]
        elif nolost == 2: return self.__beam.rays[numpy.where(self.__beam.rays[:, 9] < 0)].shape[0]
        else: raise ValueError("nolost flag value not valid")

    def load_from_file(self, file_name):
        if not self.__beam is None:
            if os.path.exists(file_name): self.__beam.load_h5(file_name)
            else: raise Exception("File " + file_name + " not existing")

    def write_to_file(self, file_name):
        if not self.__beam is None:
            self.__beam.write_h5(file_name)

    def duplicate(self, copy_rays=True):
        beam = S4Beam()
        if copy_rays: beam.rays = copy.deepcopy(self.beam.rays)

        new_shadow_beam = ShadowData(beam=beam)
        new_shadow_beam.scanning_data = self.__scanning_data
        new_shadow_beam.initial_flux  = self.__initial_flux
        new_shadow_beam.beamline = self.__beamline.duplicate()

        return new_shadow_beam

    @classmethod
    def merge_beams(cls, beam_1, beam_2, which_flux=3, merge_history=1):
        if beam_1 and beam_2:
            rays_1 = None
            rays_2 = None

            if len(getattr(beam_1.beam, "rays", numpy.zeros(0))) > 0: rays_1 = copy.deepcopy(beam_1.beam.rays)
            if len(getattr(beam_2.beam, "rays", numpy.zeros(0))) > 0: rays_2 = copy.deepcopy(beam_2.beam.rays)

            merged_beam = beam_1.duplicate(copy_rays=False, history=True)

            merged_beam.oe_number = beam_1.oe_number
            merged_beam.beam.rays = numpy.append(rays_1, rays_2, axis=0)

            merged_beam.beam.rays[:, 11] = numpy.arange(1, len(merged_beam.beam.rays) + 1, 1) # ray_index

            if which_flux ==1 :
                if not beam_1.initial_flux is None:
                    merged_beam.initial_flux = beam_1.initial_flux
            elif which_flux == 2:
                if not beam_2.initial_flux is None:
                    merged_beam.initial_flux = beam_2.initial_flux
            else:
                if not beam_1.initial_flux is None and not beam_2.initial_flux is None:
                    merged_beam.initial_flux = beam_1.initial_flux + beam_2.initial_flux

            if merge_history > 0:
                if beam_1.history and beam_2.history:
                    if len(beam_1.history) == len(beam_2.history):
                        for index in range(1, beam_1.oe_number + 1):
                            history_element_1 =  beam_1.get_oe_history(index)
                            history_element_2 =  beam_2.get_oe_history(index)

                            merged_history_element = merged_beam.get_oe_history(index)
                            merged_history_element.input_data = ShadowData.merge_beams(history_element_1.input_data, history_element_2.input_data, which_flux, merge_history=(merge_history != 1))
                    else:
                        raise ValueError("Histories must have the same path to be merged")
                else:
                    raise ValueError("Both beams must have a history to be merged")

            return merged_beam
        else:
            raise Exception("Both input beams should provided for merging")

    @classmethod
    def initialize_from_beam(cls, input_beam):
        return input_beam.duplicate()


# TODO: review all preprocessor data

# class ShadowPreProcessorData:
#     NONE = "None"
#
#     def __init__(self,
#                  bragg_data_file=NONE,
#                  m_layer_data_file_dat=NONE,
#                  m_layer_data_file_sha=NONE,
#                  prerefl_data_file=NONE,
#                  error_profile_data_file=NONE,
#                  error_profile_x_dim=0.0,
#                  error_profile_y_dim=0.0,
#                  error_profile_x_slope=0.0,
#                  error_profile_y_slope=0.0):
#         super().__init__()
#
#         self.bragg_data_file = bragg_data_file
#         self.m_layer_data_file_dat = m_layer_data_file_dat
#         self.m_layer_data_file_sha = m_layer_data_file_sha
#         self.prerefl_data_file = prerefl_data_file
#         self.error_profile_data_file = error_profile_data_file
#         self.error_profile_x_dim = error_profile_x_dim
#         self.error_profile_y_dim = error_profile_y_dim
#         self.error_profile_x_slope = error_profile_x_slope
#         self.error_profile_y_slope = error_profile_y_slope

class MLayerPreProcessorData:
    NONE = "None"
    def __init__(self,
                 mlayer_data_file=NONE,
                 ):
        super().__init__()
        self.mlayer_data_file = mlayer_data_file

class PreReflPreProcessorData:
    NONE = "None"
    def __init__(self,
                 prerefl_data_file=NONE,
                 ):
        super().__init__()
        self.prerefl_data_file = prerefl_data_file


class BraggPreProcessorData:
    NONE = "None"
    def __init__(self,
                 bragg_data_file=NONE):
        super().__init__()

        self.bragg_data_file = bragg_data_file


class VlsPgmPreProcessorData:
    def __init__(self,
                 shadow_coeff_0=0.0,
                 shadow_coeff_1=0.0,
                 shadow_coeff_2=0.0,
                 shadow_coeff_3=0.0,
                 d_source_plane_to_mirror=0.0,
                 d_mirror_to_grating=0.0,
                 d_grating_to_exit_slits=0.0,
                 alpha=0.0,
                 beta=0.0):
        self.shadow_coeff_0 = shadow_coeff_0
        self.shadow_coeff_1 = shadow_coeff_1
        self.shadow_coeff_2 = shadow_coeff_2
        self.shadow_coeff_3 = shadow_coeff_3
        self.d_source_plane_to_mirror = d_source_plane_to_mirror
        self.d_mirror_to_grating = d_mirror_to_grating
        self.d_grating_to_exit_slits = d_grating_to_exit_slits
        self.alpha = alpha
        self.beta = beta

