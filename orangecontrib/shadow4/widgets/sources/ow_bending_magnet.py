import sys
import time
import numpy

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget import gui as orangegui

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.widgets.gui.ow_electron_beam import OWElectronBeam
from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D


from syned.beamline.beamline import Beamline
from shadow4.beamline.s4_beamline import S4Beamline

from syned.storage_ring.magnetic_structures.bending_magnet import BendingMagnet
from syned.widget.widget_decorator import WidgetDecorator

from shadow4.sources.bending_magnet.s4_bending_magnet import S4BendingMagnet
from shadow4.sources.bending_magnet.s4_bending_magnet_light_source import S4BendingMagnetLightSource
from shadow4.tools.logger import set_verbose

from orangecontrib.shadow4.util.shadow4_util import TriggerToolsDecorator
from oasys.util.oasys_util import TriggerIn


class OWBendingMagnet(OWElectronBeam, WidgetDecorator, TriggerToolsDecorator):

    name = "Bending Magnet"
    description = "Shadow Source: Bending Magnet"
    icon = "icons/bending_magnet.png"
    priority = 3

    inputs = []
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Shadow Data",
                "type":ShadowData,
                "doc":"",}]

    TriggerToolsDecorator.append_trigger_input_for_sources(inputs)
    TriggerToolsDecorator.append_trigger_output(outputs)

    number_of_rays = Setting(5000)
    seed = Setting(5676561)


    magnetic_field         = Setting(-1.26754)
    divergence             = Setting(69e-3)
    emin                   = Setting(1000.0)  # Photon energy scan from energy (in eV)
    emax                   = Setting(1000.1)  # Photon energy scan to energy (in eV)
    ng_e                   = Setting(100)     # Photon energy scan number of points

    plot_bm_graph = 1


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


        # bm adv settings
        tab_advanced = oasysgui.createTabPage(self.tabs_control_area, "Advanced Setting")

        box_3 = oasysgui.widgetBox(tab_advanced, "Advanced settings", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_3, self, "ng_e", "Spectrum number of points", tooltip="ng_e", labelWidth=250, valueType=int, orientation="horizontal")

        self.add_specific_bm_plots()

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)


    def add_specific_bm_plots(self):
        bm_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

        self.main_tabs.insertTab(1, bm_plot_tab, "BM Plots")

        view_box = oasysgui.widgetBox(bm_plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.bm_view_type_combo = orangegui.comboBox(view_box_1, self,
                                            "plot_bm_graph",
                                                          label="Plot Graphs?",
                                                          labelWidth=220,
                                                          items=["No", "Yes"],
                                                          callback=self.refresh_specific_bm_plots,
                                                          sendSelectedValue=False,
                                                          orientation="horizontal")

        self.bm_tab = []
        self.bm_tabs = oasysgui.tabWidget(bm_plot_tab)

        current_tab = self.bm_tabs.currentIndex()

        size = len(self.bm_tab)
        indexes = range(0, size)
        for index in indexes:
            self.bm_tabs.removeTab(size-1-index)

        self.bm_tab = [
            orangegui.createTabPage(self.bm_tabs, "BM Spectrum"),
            orangegui.createTabPage(self.bm_tabs, "BM Spectral power")
        ]

        for tab in self.bm_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.bm_plot_canvas = [None, None]

        self.bm_tabs.setCurrentIndex(current_tab)

    def refresh_specific_bm_plots(self, lightsource=None, e=None, f=None, w=None):

        if self.plot_bm_graph == 0:
            for bm_plot_slot_index in range(6):
                current_item = self.bm_tab[bm_plot_slot_index].layout().itemAt(0)
                self.bm_tab[bm_plot_slot_index].layout().removeItem(current_item)
                plot_widget_id = oasysgui.QLabel() # TODO: is there a better way to clean this??????????????????????
                self.bm_tab[bm_plot_slot_index].layout().addWidget(plot_widget_id)
        else:

            if lightsource is None: return

            self.plot_widget_item(e,f,0,
                                  title="BM spectrum (current = %5.1f)"%self.ring_current,
                                  xtitle="Photon energy [eV]",ytitle=r"Photons/s/0.1%bw")

            self.plot_widget_item(e,w,1,
                                  title="BM spectrum (current = %5.1f)"%self.ring_current,
                                  xtitle="Photon energy [eV]",ytitle="Spectral power [W/eV]")

    def plot_widget_item(self,x,y,bm_plot_slot_index,title="",xtitle="",ytitle=""):

        self.bm_tab[bm_plot_slot_index].layout().removeItem(self.bm_tab[bm_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_data1D(x.copy(),y.copy(),title=title,xtitle=xtitle,ytitle=ytitle,symbol='.')
        self.bm_tab[bm_plot_slot_index].layout().addWidget(plot_widget_id)


    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")

    def get_lightsource(self):
        # syned electron beam
        electron_beam = self.get_electron_beam()
        print("\n\n***** electron_beam info: ", electron_beam.info())

        if self.type_of_properties == 3:
            flag_emittance = 0
        else:
            flag_emittance = 1

        magnetic_radius = numpy.abs(S4BendingMagnet.calculate_magnetic_radius(self.magnetic_field, electron_beam.energy()))
        length = numpy.abs(self.divergence * magnetic_radius)

        print(">>> calculated magnetic_radius = S4BendingMagnet.calculate_magnetic_radius(%f, %f) = %f" %\
              (self.magnetic_field, electron_beam.energy(), magnetic_radius))

        print(">>> calculated BM length = divergence * magnetic_radius = %f " % length)

        bm = S4BendingMagnet(magnetic_radius,
                             self.magnetic_field,
                             length,
                             emin=self.emin,  # Photon energy scan from energy (in eV)
                             emax=self.emax,  # Photon energy scan to energy (in eV)
                             ng_e=self.ng_e,  # Photon energy scan number of points
                             flag_emittance=flag_emittance,  # when sampling rays: Use emittance (0=No, 1=Yes)
                             )

        print("\n\n***** BM info: ", bm.info())


        # S4UndulatorLightSource
        try:    name = self.getNode().title
        except: name = "Bending Magnet"

        lightsource = S4BendingMagnetLightSource(name=name,
                                             electron_beam=electron_beam,
                                             magnetic_structure=bm,
                                             nrays=self.number_of_rays,
                                             seed=self.seed)

        print("\n\n***** S4BendingMagnetLightSource info: ", lightsource.info())

        return lightsource

    def run_shadow4(self):
        try:
            set_verbose()
            self.shadow_output.setText("")
            sys.stdout = EmittingStream(textWritten=self._write_stdout)

            self._set_plot_quality()

            self.progressBarInit()

            light_source = self.get_lightsource()


            #
            # script
            #
            script = light_source.to_python_code()
            script += "\n\n# test plot\nfrom srxraylib.plot.gol import plot_scatter"
            script += "\nrays = beam.get_rays()"
            script += "\nplot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 2], title='(X,Z) in microns')"
            self.shadow4_script.set_code(script)

            self.progressBarSet(5)

            # run shadow4

            t00 = time.time()
            print("***** starting calculation...")
            output_beam = light_source.get_beam()
            photon_energy, flux, spectral_power = light_source.calculate_spectrum()
            t11 = time.time() - t00
            print("***** time for %d rays: %f s, %f min, " % (self.number_of_rays, t11, t11 / 60))

            #
            # beam plots
            #
            self._plot_results(output_beam, None, progressBarValue=80)

            self.refresh_specific_bm_plots(light_source, photon_energy, flux, spectral_power)

            self.progressBarFinished()

            #
            # send beam and trigger
            #
            self.send("Shadow Data", ShadowData(beam=output_beam,
                                               number_of_rays=self.number_of_rays,
                                               beamline=S4Beamline(light_source=light_source)))
            self.send("Trigger", TriggerIn(new_object=True))
        except Exception as exception:
            try:    self._initialize_tabs()
            except: pass
            self.prompt_exception(exception)

    def receive_syned_data(self, data):
        if data is not None:
            if isinstance(data, Beamline):
                if data.get_light_source() is not None:
                    light_source = data.get_light_source()
                    # electron parameters
                    if light_source.get_electron_beam() is not None:
                        self.populate_fields_from_electron_beam(light_source.get_electron_beam())

                    if isinstance(data.get_light_source().get_magnetic_structure(), BendingMagnet):
                        light_source = data.get_light_source()
                    else:
                        self.type_of_properties = 0 # if not ID defined, use electron moments instead of sigmas
                        self.set_TypeOfProperties()
                else:
                    raise ValueError("Syned data not correct: light source not present")
            else:
                raise ValueError("Syned data not correct: it must be Beamline()")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWBendingMagnet()
    ow.show()
    a.exec_()
    ow.saveSettings()
