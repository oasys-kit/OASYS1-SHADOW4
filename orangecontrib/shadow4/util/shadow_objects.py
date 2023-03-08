
import os, copy, numpy
from shadow4.beam.beam import Beam


class ShadowOEHistoryItem(object):
    def __init__(self,
                 oe_number=0,
                 input_beam=None,
                 shadow_source_start=None,
                 shadow_source_end=None,
                 shadow_oe_start=None,
                 shadow_oe_end=None,
                 widget_class_name=None):
        self.__oe_number = oe_number
        self.__input_beam = input_beam
        self.__shadow_source_start = shadow_source_start
        self.__shadow_source_end = shadow_source_end
        self.__shadow_oe_start = shadow_oe_start
        self.__shadow_oe_end = shadow_oe_end
        self.__widget_class_name = widget_class_name

    def duplicate(self):
        return ShadowOEHistoryItem(oe_number=self.__oe_number,
                                   input_beam=self.__input_beam,
                                   shadow_source_start=self.__shadow_source_start,
                                   shadow_source_end=self.__shadow_source_end,
                                   shadow_oe_start=self.__shadow_oe_start,
                                   shadow_oe_end=self.__shadow_oe_end,
                                   widget_class_name=self.__widget_class_name)

    @property
    def oe_number(self):
        return self.__oe_number

    @property
    def input_beam(self):
        return self.__input_beam

    @property
    def shadow_source_start(self):
        return self.__shadow_source_start

    @property
    def shadow_source_end(self):
        return self.__shadow_source_end

    @property
    def shadow_oe_start(self):
        return self.__shadow_oe_start

    @property
    def shadow_oe_end(self):
        return self.__shadow_oe_end

    @property
    def widget_class_name(self):
        return self.__widget_class_name

class ShadowBeam:
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

    def __init__(self, oe_number=0, beam=None, number_of_rays=0, beamline=None):
        self.__oe_number = oe_number
        if (beam is None):
            if number_of_rays > 0: self.__beam = Beam(number_of_rays)
            else:                  self.__beam = Beam()
        else:
            self.__beam = beam

        self.__history       = []
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
    def oe_number(self):
        return self.__oe_number

    @oe_number.setter
    def oe_number(self, oe_number):
        self.__oe_number = oe_number

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

    @property
    def history(self):
        return self.__history
    
    @history.setter
    def history(self, history):
        self.__history = history
        
    def get_oe_history(self, oe_number):
        return self.__history[oe_number]

    def history_size(self):
        return len(self.__history)

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

    def duplicate(self, copy_rays=True, history=True):
        beam = Beam()
        if copy_rays: beam.rays = copy.deepcopy(self.beam.rays)

        new_shadow_beam = ShadowBeam(self.__oe_number, beam)
        new_shadow_beam.scanning_data = self.__scanning_data
        new_shadow_beam.initial_flux  = self.__initial_flux
        new_shadow_beam.beamline = self.__beamline.duplicate()

        if history: 
            for history_item in self.__history: new_shadow_beam.history.append(history_item)

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
                            merged_history_element.input_beam = ShadowBeam.merge_beams(history_element_1.input_beam, history_element_2.input_beam, which_flux, merge_history=(merge_history!=1))
                    else:
                        raise ValueError("Histories must have the same path to be merged")
                else:
                    raise ValueError("Both beams must have a history to be merged")

            return merged_beam
        else:
            raise Exception("Both input beams should provided for merging")

    @classmethod
    def initialize_from_beam(cls, input_beam):
        shadow_beam = input_beam.duplicate()
        shadow_beam.oe_number = input_beam.oe_number + 1

        return shadow_beam

