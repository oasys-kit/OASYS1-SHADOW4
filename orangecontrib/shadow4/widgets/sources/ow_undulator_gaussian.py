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
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D, plot_data2D, plot_data3D, plot_multi_data1D

from orangewidget import gui as orangegui

from syned.beamline.beamline import Beamline
from shadow4.beamline.s4_beamline import S4Beamline

from syned.storage_ring.magnetic_structures.undulator import Undulator
from syned.widget.widget_decorator import WidgetDecorator

from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian
from shadow4.sources.undulator.s4_undulator_gaussian_light_source import S4UndulatorGaussianLightSource

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

    plot_undulator_graph = Setting(1)

    # energy spread...
    harmonic_number = Setting(1)
    period_length = Setting(0.020)

    flux_peak = Setting('1e10')
    plot_npoints = Setting(100)
    plot_emin = Setting(1000.0)
    plot_emax = Setting(10000.0)

    # beam_out = None
    lightsource = None # store lightsource after calculation

    def __init__(self):
        super().__init__(show_energy_spread=True)

        tab_bas = oasysgui.createTabPage(self.tabs_control_area, "Undulator Setting")

        #
        box_1 = oasysgui.widgetBox(tab_bas, "Undulator Parameters", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_1, self, "undulator_length", "Undulator Length [m]", labelWidth=250, tooltip="undulator_length", valueType=float, orientation="horizontal")
        self.box_energy_spread_local = oasysgui.widgetBox(box_1, orientation="vertical")
        oasysgui.lineEdit(self.box_energy_spread_local, self, "period_length", "ID period [m]", labelWidth=260, tooltip="period_length", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_energy_spread_local, self, "harmonic_number", "Harmonic in use [odd]", labelWidth=250, tooltip="harmonic_number", valueType=int, orientation="horizontal")


        #
        box_2 = oasysgui.widgetBox(tab_bas, "Sampling rays", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_2, self, "energy", "Set resonance at energy [eV]", tooltip="energy", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "delta_e", "Delta Energy [eV]", tooltip="delta_e", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "number_of_rays", "Number of Rays", tooltip="number_of_rays", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "seed", "Seed", tooltip="seed", labelWidth=250, valueType=int, orientation="horizontal")

        #
        # advanced settings
        #
        tab_advanced = oasysgui.createTabPage(self.tabs_control_area, "Advanced Setting")
        # arrays
        left_box_11 = oasysgui.widgetBox(tab_advanced, "Flux normalization", addSpace=False, orientation="vertical")
        # define as string to allow scientific notation (e.g. 2e11)
        oasysgui.lineEdit(left_box_11, self, "flux_peak", "Set flux to [photons/s/0.1%bw]", tooltip="flux_peak",
                          labelWidth=250, valueType=str, orientation="horizontal")


        left_box_11 = oasysgui.widgetBox(tab_advanced, "Specific parameters for undulator plots", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_11, self, "plot_npoints", "Number of energy points", tooltip="plot_npoints",
                          labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "plot_emin", "Min photon energy [eV]", tooltip="plot_emin",
                          labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "plot_emax", "Max photon energy [eV]", tooltip="plot_emax",
                          labelWidth=250, valueType=float, orientation="horizontal")


        # undulator plots
        self.add_specific_undulator_plots()

        self.set_visibility()

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def set_visibility_energy_spread(self): # to be filled in the upper class
        print(">>>>>>>>> local set_visibility_energy_spread", self.flag_energy_spread)
        try: # avoir error when calling this method from the base class
            self.box_energy_spread_local.setVisible(self.flag_energy_spread == 1)
        except:
            pass
    def set_visibility(self):
        self.set_visibility_energy_spread()

        # self.box_photon_energy_min_max.setVisible( self.set_at_resonance == 0 and self.is_monochromatic == 0)
        # self.box_photon_energy_center.setVisible(  self.set_at_resonance == 0 and self.is_monochromatic == 1)
        # self.box_photon_energy_width.setVisible(   self.set_at_resonance == 1 and self.is_monochromatic == 0)
        # self.box_photon_energy_harmonic.setVisible(self.set_at_resonance == 1)
        # self.box_maxangle.setVisible(              self.set_at_resonance == 0)
        #
        # self.box_backpropagation_internal_wofry.setVisible(self.flag_size == 2 and self.code_undul_phot <= 1)
        # self.box_backpropagation_srw.setVisible(self.flag_size == 2 and self.code_undul_phot == 2)
        #
        # self.box_backpropagation_internal_wofry_weight_vaue.setVisible(self.flag_backprop_weight == 1) # self.flag_size == 2 and
        #                                                               # self.code_undul_phot == 2 and
        #                                                               # self.flag_backprop_weight == 1)

    def add_specific_undulator_plots(self):

        undulator_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

        self.main_tabs.insertTab(1, undulator_plot_tab, "Undulator Plots")

        view_box = oasysgui.widgetBox(undulator_plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.undulator_view_type_combo = orangegui.comboBox(view_box_1, self,
                                            "plot_undulator_graph",
                                                          label="Plot Graphs?",
                                                          labelWidth=220,
                                                          items=["No", "Yes"],
                                                          callback=self.refresh_specific_undulator_plots,
                                                          sendSelectedValue=False,
                                                          orientation="horizontal")

        self.undulator_tab = []
        self.undulator_tabs = oasysgui.tabWidget(undulator_plot_tab)

        current_tab = self.undulator_tabs.currentIndex()

        size = len(self.undulator_tab)
        indexes = range(0, size)
        for index in indexes:
            self.undulator_tabs.removeTab(size-1-index)

        self.undulator_tab = [
            orangegui.createTabPage(self.undulator_tabs, "Flux spectrum"),
            orangegui.createTabPage(self.undulator_tabs, "Spectral Power"),
            orangegui.createTabPage(self.undulator_tabs, "photon beam sizes"),
            orangegui.createTabPage(self.undulator_tabs, "photon beam divergences"),
        ]

        self.undulator_plot_canvas = [None, None, None, None]

        for tab in self.undulator_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.undulator_tabs.setCurrentIndex(current_tab)

    def plot_undulator_item1D(self, undulator_plot_slot_index, x, y, title="", xtitle="", ytitle="", symbol='.'):
        self.undulator_tab[undulator_plot_slot_index].layout().removeItem(self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_data1D(x.copy(), y.copy(), title=title, xtitle=xtitle, ytitle=ytitle, symbol=symbol)
        self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)

    def plot_undulator_multi_data1D(self, undulator_plot_slot_index, x, y, title="", xtitle="", ytitle="", ytitles=[""], symbol='.'):
        self.undulator_tab[undulator_plot_slot_index].layout().removeItem(self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_multi_data1D(x, y, title=title, xtitle=xtitle, ytitle=ytitle, ytitles=ytitles) #, symbol=symbol)
        self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)

    def refresh_specific_undulator_plots(self):
        if self.lightsource is None: return

        if self.plot_undulator_graph == 0:
            for undulator_plot_slot_index in range(len(self.undulator_plot_canvas)):
                current_item = self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0)
                self.undulator_tab[undulator_plot_slot_index].layout().removeItem(current_item)
                plot_widget_id = oasysgui.QLabel() # TODO: is there a better way to clean this??????????????????????
                self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)
        else:
            # spectra
            e, f, w = self.lightsource.calculate_spectrum()
            self.plot_undulator_item1D(0, e, f,
                                  title="Undulator spectrum", xtitle="Photon energy [eV]", ytitle=r"Photons/s/0.1%bw")

            self.plot_undulator_item1D(1, e, w,
                                  title="Undulator spectral power",
                                  xtitle="Photon energy [eV]", ytitle="Spectral power [W/eV]")

            ener = numpy.linspace(self.plot_emin, self.plot_emax, self.plot_npoints)
            Sx, Spx, Sz, Spz = self.lightsource.get_scans_for_plots(ener)

            self.plot_undulator_multi_data1D(2, ener, [1e6 * Sx, 1e6 * Sz],
                                  title="Undulator sizes", xtitle="Photon energy [eV]", ytitle=r"Size RMS [um]",
                                  ytitles=["Horizontal", "Vertical"])

            self.plot_undulator_multi_data1D(3, ener, [1e6 * Spx, 1e6 * Spz],
                                  title="Undulator divergences", xtitle="Photon energy [eV]", ytitle=r"Divergence angle RMS [urad]",
                                  ytitles=["Horizontal", "Vertical"])

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

        sourceundulator = S4UndulatorGaussian(
            period_length=self.period_length,  # syned Undulator parameter
            number_of_periods=self.undulator_length / self.period_length,  # syned Undulator parameter
            photon_energy=self.energy,
            delta_e=self.delta_e,
            # ng_e=11,  # Photon energy scan number of points
            flag_emittance=flag_emittance,  # when sampling rays: Use emittance (0=No, 1=Yes)
            flag_energy_spread=self.flag_energy_spread,
            harmonic_number=self.harmonic_number,
            flux_peak=float(self.flux_peak),
        )

        print("\n\n>>>>>> Undulator info: ", sourceundulator.info())

        if self.delta_e == 0:
            sourceundulator.set_energy_monochromatic(self.energy)
        else:
            sourceundulator.set_energy_box(self.energy-0.5*self.delta_e, self.energy+0.5*self.delta_e,)

        # S4UndulatorLightSource
        lightsource = S4UndulatorGaussianLightSource(name='GaussianUndulator',
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
        self.progressBarSet(5)

        # run shadow4
        t00 = time.time()
        print(">>>> starting calculation...")
        output_beam = light_source.get_beam()
        t11 = time.time() - t00
        print(">>>> time for %d rays: %f s, %f min, " % (self.number_of_rays, t11, t11 / 60))

        self.lightsource = light_source

        #
        # beam plots
        #
        self._plot_results(output_beam, None, progressBarValue=80)

        self.refresh_specific_undulator_plots()

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

                        self.energy =  round(light_source.get_magnetic_structure().resonance_energy(light_source.get_electron_beam().gamma()))
                        self.delta_e = 0.0
                        self.undulator_length = light_source.get_magnetic_structure().length()
                        self.period_length = light_source.get_magnetic_structure().period_length()


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
