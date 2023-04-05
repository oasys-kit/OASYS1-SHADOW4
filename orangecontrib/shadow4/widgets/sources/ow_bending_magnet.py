import sys
import time
import numpy

from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.widgets.gui.ow_electron_beam import OWElectronBeam
from orangecontrib.shadow4.util.shadow4_objects import ShadowData


from syned.beamline.beamline import Beamline
from shadow4.beamline.s4_beamline import S4Beamline

from syned.storage_ring.magnetic_structures.bending_magnet import BendingMagnet
from syned.widget.widget_decorator import WidgetDecorator

from shadow4.sources.bending_magnet.s4_bending_magnet import S4BendingMagnet
from shadow4.sources.bending_magnet.s4_bending_magnet_light_source import S4BendingMagnetLightSource

class OWBendingMagnet(OWElectronBeam, WidgetDecorator):

    name = "Bending Magnet"
    description = "Shadow Source: Bending Magnet"
    icon = "icons/bending_magnet.png"
    priority = 3

    inputs = []
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Shadow Data",
                "type":ShadowData,
                "doc":"",}]


    number_of_rays = Setting(5000)
    seed = Setting(5676561)


    magnetic_field         = Setting(-1.26754)
    divergence             = Setting(69e-3)
    emin                   = Setting(1000.0)  # Photon energy scan from energy (in eV)
    emax                   = Setting(1000.1)  # Photon energy scan to energy (in eV)
    ng_e                   = Setting(100)     # Photon energy scan number of points
    ng_j                   = Setting(100) # Number of points in electron trajectory (per period) for internal calculation only


    def __init__(self):
        super().__init__()

        tab_bas = oasysgui.createTabPage(self.tabs_control_area, "Bending Magnet Setting")

        #
        box_1 = oasysgui.widgetBox(tab_bas, "Bending Magnet Parameters", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_1, self, "emin", "Minimum Energy [eV]", tooltip="emin", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_1, self, "emax", "Maximum Energy [eV]", tooltip="emax", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_1, self, "magnetic_field", "Magnetic Field [T]", tooltip="magnetic_field", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_1, self, "divergence", "Horizontal divergence (arc of radius) [rads]", tooltip="divergence", labelWidth=260, valueType=float, orientation="horizontal")

        box_2 = oasysgui.widgetBox(tab_bas, "Sampling rays", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_2, self, "number_of_rays", "Number of Rays", tooltip="Number of Rays", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "seed", "Seed", tooltip="Seed (0=clock)", labelWidth=250, valueType=int, orientation="horizontal")

        box_3 = oasysgui.widgetBox(tab_bas, "Optional parameters for internal calculation", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_3, self, "ng_e", "Spectrum number of points", tooltip="ng_e", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box_3, self, "ng_j", "Electron trajectory number of points", tooltip="ng_j", labelWidth=250, valueType=int, orientation="horizontal")

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)


    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
        # self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
        # self.delta_e = congruence.checkPositiveNumber(self.delta_e, "Delta Energy")
        # self.undulator_length = congruence.checkPositiveNumber(self.undulator_length, "Undulator Length")

    def get_lightsource(self):
        # syned electron beam
        electron_beam = self.get_electron_beam()
        print("\n\n>>>>>> electron_beam info: ", electron_beam.info())

        if self.type_of_properties == 3:
            flag_emittance = 0
        else:
            flag_emittance = 1

        magnetic_radius = S4BendingMagnet.calculate_magnetic_radius(self.magnetic_field, electron_beam.energy())
        length = numpy.abs(self.divergence * magnetic_radius)

        print(">>> calculated magnetic_radius = S4BendingMagnet.calculate_magnetic_radius(%f, %f) = %f" %\
              (self.magnetic_field, electron_beam.energy(), magnetic_radius))

        print(">>> calculated BM length = divergence * magnetic_radius = %f " % length)

        bm = S4BendingMagnet(magnetic_radius,self.magnetic_field,length,
                             emin=self.emin,  # Photon energy scan from energy (in eV)
                             emax=self.emax,  # Photon energy scan to energy (in eV)
                             ng_e=self.ng_e,  # Photon energy scan number of points
                             ng_j=self.ng_j,
                             # Number of points in electron trajectory (per period) for internal calculation only
                             flag_emittance=flag_emittance,  # when sampling rays: Use emittance (0=No, 1=Yes)
                             )


        # bm = S4BendingMagnet.initialize_from_magnetic_field_divergence_and_electron_energy(
        #     magnetic_field=self.magnetic_field,
        #     divergence=self.divergence,
        #     electron_energy_in_GeV=electron_beam.energy(),
        #     emin=self.emin,# Photon energy scan from energy (in eV)
        #     emax=self.emax,# Photon energy scan to energy (in eV)
        #     ng_e=self.ng_e,# Photon energy scan number of points
        #     ng_j=self.ng_j,# Number of points in electron trajectory (per period) for internal calculation only
        #     flag_emittance=flag_emittance,# when sampling rays: Use emittance (0=No, 1=Yes)
        #     )


        print("\n\n>>>>>> BM info: ", bm.info())


        # S4UndulatorLightSource
        lightsource = S4BendingMagnetLightSource(name='BendingMagnet',
                                             electron_beam=electron_beam,
                                             magnetic_structure=bm,
                                             nrays=self.number_of_rays,
                                             seed=self.seed)

        print("\n\n>>>>>> S4BendingMagnetLightSource info: ", lightsource.info())

        return lightsource

    def run_shadow4(self):

        sys.stdout = EmittingStream(textWritten=self._write_stdout)

        self._set_plot_quality()

        self.progressBarInit()

        light_source = self.get_lightsource()

        self.progressBarSet(5)


        # run shadow4

        t00 = time.time()
        print(">>>> starting calculation...")
        output_beam = light_source.get_beam()
        # todo:
        # photon_energy, flux, spectral_power = light_source.calculate_spectrum()
        t11 = time.time() - t00
        print(">>>> time for %d rays: %f s, %f min, " % (self.number_of_rays, t11, t11 / 60))


        #
        # beam plots
        #
        self._plot_results(output_beam, None, progressBarValue=80)

        #
        # script
        #
        script = light_source.to_python_code()
        script += "\n\n# test plot\nfrom srxraylib.plot.gol import plot_scatter"
        script += "\nrays = beam.get_rays()"
        script += "\nplot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 2], title='(X,Z) in microns')"
        self.shadow4_script.set_code(script)

        self.progressBarFinished()

        #
        # send beam
        #
        self.send("Shadow Data", ShadowData(beam=output_beam,
                                           number_of_rays=self.number_of_rays,
                                           beamline=S4Beamline(light_source=light_source)))


    def receive_syned_data(self, data):
        if data is not None:
            if isinstance(data, Beamline):
                if not data.get_light_source() is None:
                    if isinstance(data.get_light_source().get_magnetic_structure(), BendingMagnet):
                        light_source = data.get_light_source()

                        # self.energy =  round(light_source.get_magnetic_structure().resonance_energy(light_source.get_electron_beam().gamma()), 3)
                        # self.delta_e = 0.0
                        # self.undulator_length = light_source.get_magnetic_structure().length()

                        self.populate_fields_from_syned_electron_beam(light_source.get_electron_beam())

                    else:
                        raise ValueError("Syned light source not congruent")
                else:
                    raise ValueError("Syned data not correct: light source not present")
            else:
                raise ValueError("Syned data not correct")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWBendingMagnet()
    ow.show()
    a.exec_()
    ow.saveSettings()
