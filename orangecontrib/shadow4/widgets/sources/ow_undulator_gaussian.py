import sys
import time


from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.widgets.gui.ow_electron_beam import OWElectronBeam
from orangecontrib.shadow4.util.shadow4_objects import ShadowData


from syned.beamline.beamline import Beamline
from shadow4.beamline.s4_beamline import S4Beamline

from syned.storage_ring.magnetic_structures.undulator import Undulator
from syned.widget.widget_decorator import WidgetDecorator

from shadow4.sources.undulator.s4_undulator import S4Undulator
from shadow4.sources.undulator.s4_undulator_light_source import S4UndulatorLightSource

class OWUndulatorGaussian(OWElectronBeam, WidgetDecorator):

    name = "Undulator Gaussian"
    description = "Shadow Source: Undulator Gaussian"
    icon = "icons/ugaussian.png"
    priority = 5

    inputs = []
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Shadow Data",
                "type":ShadowData,
                "doc":"",}]

    undulator_length = Setting(4.0)
    energy = Setting(15000.0)
    delta_e = Setting(1500.0)
    number_of_rays = Setting(5000)
    seed = Setting(5676561)


    def __init__(self):
        super().__init__()

        tab_bas = oasysgui.createTabPage(self.tabs_control_area, "Undulator Setting")

        #
        box_1 = oasysgui.widgetBox(tab_bas, "Undulator Parameters", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_1, self, "undulator_length", "Undulator Length [m]", labelWidth=250, tooltip="Undulator Length [m]", valueType=float, orientation="horizontal")
        #
        box_2 = oasysgui.widgetBox(tab_bas, "Sampling rays", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_2, self, "energy", "Set resonance at energy [eV]", tooltip="Set resonance at energy [eV]", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "delta_e", "Delta Energy [eV]", tooltip="Delta Energy [eV]", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "number_of_rays", "Number of Rays", tooltip="Number of Rays", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "seed", "Seed", tooltip="Seed (0=clock)", labelWidth=250, valueType=int, orientation="horizontal")

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)


    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
        self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
        self.delta_e = congruence.checkPositiveNumber(self.delta_e, "Delta Energy")
        self.undulator_length = congruence.checkPositiveNumber(self.undulator_length, "Undulator Length")

    def get_lightsource(self):
        # syned electron beam
        electron_beam = self.get_electron_beam()
        print("\n\n>>>>>> electron_beam info: ", electron_beam.info())

        if self.type_of_properties == 3:
            flag_emittance = 0
        else:
            flag_emittance = 1

        sourceundulator = S4Undulator(
            # K_vertical=1.0,  # syned Undulator parameter
            period_length=self.undulator_length/100,  # syned Undulator parameter
            number_of_periods=100,  # syned Undulator parameter
            emin=self.energy - 0.5 * self.delta_e,  # Photon energy scan from energy (in eV)
            emax=self.energy + 0.5 * self.delta_e,  # Photon energy scan to energy (in eV)
            # ng_e=11,  # Photon energy scan number of points
            # maxangle=50e-6,  # Maximum radiation semiaperture in RADIANS
            # ng_t=31,  # Number of points in angle theta
            # ng_p=21,  # Number of points in angle phi
            # ng_j=20,  # Number of points in electron trajectory (per period) for internal calculation only
            # code_undul_phot="internal",  # internal, pysru, srw
            flag_emittance=flag_emittance,  # when sampling rays: Use emittance (0=No, 1=Yes)
            # flag_size=0,  # when sampling rays: 0=point,1=Gaussian,2=FT(Divergences)
            use_gaussian_approximation=1,
        )

        print("\n\n>>>>>> Undulator info: ", sourceundulator.info())

        if self.delta_e == 0:
            sourceundulator.set_energy_monochromatic(self.energy)
        else:
            sourceundulator.set_energy_box(self.energy-0.5*self.delta_e, self.energy+0.5*self.delta_e,)

        # S4UndulatorLightSource
        lightsource = S4UndulatorLightSource(name='GaussianUndulator',
                                             electron_beam=electron_beam,
                                             magnetic_structure=sourceundulator,
                                             nrays=self.number_of_rays,
                                             seed=self.seed)

        print("\n\n>>>>>> S4UndulatorLightSource info: ", lightsource.info())

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
        # script += "\n\n\n# run shadow4"
        # script += "\nbeam = light_source.get_beam(NRAYS=%d, SEED=%d)" % (self.number_of_rays, self.seed)
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
                    if isinstance(data.get_light_source().get_magnetic_structure(), Undulator):
                        light_source = data.get_light_source()

                        self.energy =  round(light_source.get_magnetic_structure().resonance_energy(light_source.get_electron_beam().gamma()), 3)
                        self.delta_e = 0.0
                        self.undulator_length = light_source.get_magnetic_structure().length()

                        self.populate_fields_from_electron_beam(light_source.get_electron_beam())

                    else:
                        raise ValueError("Syned light source not congruent")
                else:
                    raise ValueError("Syned data not correct: light source not present")
            else:
                raise ValueError("Syned data not correct")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWUndulatorGaussian()
    ow.show()
    a.exec_()
    ow.saveSettings()
