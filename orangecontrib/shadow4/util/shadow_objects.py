
import os, copy, numpy, platform
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
        self._oe_number = oe_number
        self._input_beam = input_beam
        self._shadow_source_start = shadow_source_start
        self._shadow_source_end = shadow_source_end
        self._shadow_oe_start = shadow_oe_start
        self._shadow_oe_end = shadow_oe_end
        self._widget_class_name = widget_class_name

    def duplicate(self):
        return ShadowOEHistoryItem(oe_number=self._oe_number,
                                   input_beam=self._input_beam,
                                   shadow_source_start=self._shadow_source_start,
                                   shadow_source_end=self._shadow_source_end,
                                   shadow_oe_start=self._shadow_oe_start,
                                   shadow_oe_end=self._shadow_oe_end,
                                   widget_class_name=self._widget_class_name)


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

        def get_scanned_variable_name(self):
            return self.__scanned_variable_name

        def get_scanned_variable_value(self):
            return self.__scanned_variable_value

        def get_scanned_variable_display_name(self):
            return self.__scanned_variable_display_name

        def get_scanned_variable_um(self):
            return self.__scanned_variable_um

        def has_additional_parameter(self, name):
            return name in self.__additional_parameters.keys()

        def get_additional_parameter(self, name):
            return self.__additional_parameters[name]

    def __new__(cls, oe_number=0, beam=None, number_of_rays=0, beamline=None):
        __shadow_beam = super().__new__(cls)
        __shadow_beam._oe_number = oe_number
        if (beam is None):
            if number_of_rays > 0: __shadow_beam._beam = Beam(number_of_rays)
            else:                  __shadow_beam._beam = Beam()
        else:
            __shadow_beam._beam = beam

        __shadow_beam.history = []
        __shadow_beam.scanned_variable_data = None
        __shadow_beam.__initial_flux = None
        __shadow_beam._beamline = beamline  # added by srio

        return __shadow_beam

    def get_beamline(self):
        return self._beamline

    def set_initial_flux(self, initial_flux):
        self.__initial_flux = initial_flux

    def get_initial_flux(self):
        return self.__initial_flux

    def get_flux(self, nolost=1):
        if not self._beam is None and not self.__initial_flux is None:
            return (self._beam.intensity(nolost) / self.get_number_of_rays(0)) * self.get_initial_flux()
        else:
            return None

    def get_number_of_rays(self, nolost=0):
        if not hasattr(self._beam, "rays"): return 0
        if nolost==0:     return self._beam.rays.shape[0]
        elif nolost==1:   return self._beam.rays[numpy.where(self._beam.rays[:, 9] > 0)].shape[0]
        elif nolost == 2: return self._beam.rays[numpy.where(self._beam.rays[:, 9] < 0)].shape[0]
        else: raise ValueError("nolost flag value not valid")

    def setBeam(self, beam):
        self._beam = beam

    def setScanningData(self, scanned_variable_data=ScanningData(None, None, None, None)):
        self.scanned_variable_data=scanned_variable_data

    def loadFromFile(self, file_name):
        if not self._beam is None:
            if os.path.exists(file_name):
                self._beam.load(file_name)
            else:
                raise Exception("File " + file_name + " not existing")

    def writeToFile(self, file_name):
        if not self._beam is None:
            self._beam.write(file_name)

    def duplicate(self, copy_rays=True, history=True):
        beam = Beam()
        if copy_rays: beam.rays = copy.deepcopy(self._beam.rays)

        new_shadow_beam = ShadowBeam(self._oe_number, beam)
        new_shadow_beam.setScanningData(self.scanned_variable_data)
        new_shadow_beam.set_initial_flux(self.get_initial_flux())

        if history:
            for historyItem in self.history: new_shadow_beam.history.append(historyItem)

        return new_shadow_beam

    @classmethod
    def mergeBeams(cls, beam_1, beam_2, which_flux=3, merge_history=1):
        if beam_1 and beam_2:
            rays_1 = None
            rays_2 = None

            if len(getattr(beam_1._beam, "rays", numpy.zeros(0))) > 0:
                rays_1 = copy.deepcopy(beam_1._beam.rays)
            if len(getattr(beam_2._beam, "rays", numpy.zeros(0))) > 0:
                rays_2 = copy.deepcopy(beam_2._beam.rays)

            #if len(rays_2) != len(rays_1): raise ValueError("The two beams must have the same amount of rays for merging")

            merged_beam = beam_1.duplicate(copy_rays=False, history=True)

            merged_beam._oe_number = beam_1._oe_number
            merged_beam._beam.rays = numpy.append(rays_1, rays_2, axis=0)

            merged_beam._beam.rays[:, 11] = numpy.arange(1, len(merged_beam._beam.rays) + 1, 1) # ray_index

            if which_flux==1:
                if not beam_1.get_initial_flux() is None:
                    merged_beam.set_initial_flux(beam_1.get_initial_flux())
            elif which_flux==2:
                if not beam_2.get_initial_flux() is None:
                    merged_beam.set_initial_flux(beam_2.get_initial_flux())
            else:
                if not beam_1.get_initial_flux() is None and not beam_2.get_initial_flux() is None:
                    merged_beam.set_initial_flux(beam_1.get_initial_flux() + beam_2.get_initial_flux())

            if merge_history > 0:
                if beam_1.history and beam_2.history:
                    if len(beam_1.history) == len(beam_2.history):
                        for index in range(1, beam_1._oe_number + 1):
                            history_element_1 =  beam_1.getOEHistory(index)
                            history_element_2 =  beam_2.getOEHistory(index)

                            merged_history_element = merged_beam.getOEHistory(index)
                            if merge_history == 1:
                                merged_history_element._input_beam = ShadowBeam.mergeBeams(history_element_1._input_beam, history_element_2._input_beam, which_flux, merge_history=False)
                            else:
                                merged_history_element._input_beam = ShadowBeam.mergeBeams(history_element_1._input_beam, history_element_2._input_beam, which_flux, merge_history=True)
                    else:
                        raise ValueError("Histories must have the same path to be merged")
                else:
                    raise ValueError("Both beams must have a history to be merged")

            return merged_beam
        else:
            raise Exception("Both input beams should provided for merging")

    @classmethod
    def traceFromSource(cls, shadow_src, write_begin_file=0, write_start_file=0, write_end_file=0, history=True, widget_class_name=None):
        __shadow_beam = cls.__new__(ShadowBeam, beam=Beam())

        shadow_src.self_repair()

        shadow_source_start = shadow_src.duplicate()

        if write_start_file == 1:
            shadow_src.src.write("start.00")

        __shadow_beam._beam.genSource(shadow_src.src)

        shadow_src.self_repair()

        if write_begin_file:
            __shadow_beam.writeToFile("begin.dat")

        if write_end_file == 1:
            shadow_src.src.write("end.00")

        shadow_source_end = shadow_src.duplicate()

        if history:
            __shadow_beam.history.append(ShadowOEHistoryItem(shadow_source_start=shadow_source_start,
                                                    shadow_source_end=shadow_source_end,
                                                    widget_class_name=widget_class_name))

        return __shadow_beam

    @classmethod
    def traceFromOE(cls, input_beam, shadow_oe, write_start_file=0, write_end_file=0, history=True, widget_class_name=None):
        __shadow_beam = cls.initializeFromPreviousBeam(input_beam)

        shadow_oe.self_repair()

        if history: history_shadow_oe_start = shadow_oe.duplicate()
        if write_start_file == 1: shadow_oe._oe.write("start.%02d"%__shadow_beam._oe_number)

        __shadow_beam._beam.traceOE(shadow_oe._oe, __shadow_beam._oe_number)

        shadow_oe.self_repair()

        if write_end_file == 1: shadow_oe._oe.write("end.%02d"%__shadow_beam._oe_number)

        if history:
            history_shadow_oe_end = shadow_oe.duplicate()

            #N.B. history[0] = Source
            if not __shadow_beam._oe_number == 0:
                if len(__shadow_beam.history) - 1 < __shadow_beam._oe_number:
                    __shadow_beam.history.append(ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                     input_beam=input_beam.duplicate(),
                                                                     shadow_oe_start=history_shadow_oe_start,
                                                                     shadow_oe_end=history_shadow_oe_end,
                                                                     widget_class_name=widget_class_name))
                else:
                    __shadow_beam.history[__shadow_beam._oe_number]=ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                      input_beam=input_beam.duplicate(),
                                                                      shadow_oe_start=history_shadow_oe_start,
                                                                      shadow_oe_end=history_shadow_oe_end,
                                                                      widget_class_name=widget_class_name)

        return __shadow_beam

    @classmethod
    def traceIdealLensOE(cls, input_beam, shadow_oe, history=True, widget_class_name=None):
        __shadow_beam = cls.initializeFromPreviousBeam(input_beam)

        shadow_oe.self_repair()

        if history: history_shadow_oe_start = shadow_oe.duplicate()

        __shadow_beam._beam.traceIdealLensOE(shadow_oe._oe, __shadow_beam._oe_number)

        shadow_oe.self_repair()

        if history:
            history_shadow_oe_end = shadow_oe.duplicate()

            #N.B. history[0] = Source
            if not __shadow_beam._oe_number == 0:
                if len(__shadow_beam.history) - 1 < __shadow_beam._oe_number:
                    __shadow_beam.history.append(ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                     input_beam=input_beam.duplicate(),
                                                                     shadow_oe_start=history_shadow_oe_start,
                                                                     shadow_oe_end=history_shadow_oe_end,
                                                                     widget_class_name=widget_class_name))
                else:
                    __shadow_beam.history[__shadow_beam._oe_number]=ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                                        input_beam=input_beam.duplicate(),
                                                                                        shadow_oe_start=history_shadow_oe_start,
                                                                                        shadow_oe_end=history_shadow_oe_end,
                                                                                        widget_class_name=widget_class_name)

        return __shadow_beam

    @classmethod
    def traceFromCompoundOE(cls,
                            input_beam,
                            shadow_oe,
                            write_start_files=0,
                            write_end_files=0,
                            write_star_files=0,
                            write_mirr_files=0,
                            history=True,
                            widget_class_name=None):
        __shadow_beam = cls.initializeFromPreviousBeam(input_beam)

        shadow_oe.self_repair()

        if history: history_shadow_oe_start = shadow_oe.duplicate()

        __shadow_beam._beam.traceCompoundOE(shadow_oe._oe,
                                            from_oe=__shadow_beam._oe_number,
                                            write_start_files=write_start_files,
                                            write_end_files=write_end_files,
                                            write_star_files=write_star_files,
                                            write_mirr_files=write_mirr_files)

        shadow_oe.self_repair()

        if history:
            history_shadow_oe_end = shadow_oe.duplicate()

            # N.B. history[0] = Source
            if not __shadow_beam._oe_number == 0:
                if len(__shadow_beam.history) - 1 < __shadow_beam._oe_number:
                    __shadow_beam.history.append(ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                     input_beam=input_beam.duplicate(),
                                                                     shadow_oe_start=history_shadow_oe_start,
                                                                     shadow_oe_end=history_shadow_oe_end,
                                                                     widget_class_name=widget_class_name))
                else:
                    __shadow_beam.history[__shadow_beam._oe_number] = ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                                          input_beam=input_beam.duplicate(),
                                                                                          shadow_oe_start=history_shadow_oe_start,
                                                                                          shadow_oe_end=history_shadow_oe_end,
                                                                                          widget_class_name=widget_class_name)

        return __shadow_beam

    @classmethod
    def initializeFromPreviousBeam(cls, input_beam):
        __shadow_beam = input_beam.duplicate()
        __shadow_beam._oe_number = input_beam._oe_number + 1

        return __shadow_beam

    def getOEHistory(self, oe_number=None):
        if oe_number is None:
            return self.history
        else:
            return self.history[oe_number]

    def historySize(self):
        return len(self.history)

