import sys
import time

from orangecontrib.shadow4.widgets.gui.ow_electron_beam import OWElectronBeam
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D
from orangecontrib.shadow4.util.shadow4_objects import ShadowData

from oasys.widgets import gui as oasysgui

from oasys.util.oasys_util import EmittingStream

from syned.beamline.beamline import Beamline
from syned.storage_ring.magnetic_structures.insertion_device import InsertionDevice
from syned.widget.widget_decorator import WidgetDecorator

from orangewidget import gui as orangegui
from orangewidget.settings import Setting


from shadow4.sources.undulator.s4_undulator import S4Undulator
from shadow4.sources.undulator.s4_undulator_light_source import S4UndulatorLightSource

from shadow4.beamline.s4_beamline import S4Beamline

class OWUndulator(OWElectronBeam, WidgetDecorator):

    name = "Undulator Light Source"
    description = "Undulator Light Source"
    icon = "icons/undulator.png"
    priority = 50

    inputs = []
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Shadow Data",
                "type":ShadowData,
                "doc":"",}]

    # undulator parameters
    K_vertical = Setting(0.25)  # syned Undulator parameter
    period_length = Setting(0.032)  # syned Undulator parameter
    number_of_periods = Setting(50)  # syned Undulator parameter

    # photon energy
    emin = Setting(10490.0)  # Photon energy scan from energy (in eV)
    emax = Setting(10510.0)  # Photon energy scan to energy (in eV)
    maxangle = Setting(0.015)  # Maximum radiation semiaperture in RADIANS

    # other parameters
    ng_e = Setting(3)  # Photon energy scan number of points
    ng_t = Setting(100)  # Number of points in angle theta
    ng_p = Setting(11)  # Number of points in angle phi
    ng_j = Setting(20)  # Number of points in electron trajectory (per period) for internal calculation only
    code_undul_phot = Setting(0) # "internal",  # internal, pysru, srw
    flag_emittance = Setting(0)  # when sampling rays: Use emittance (0=No, 1=Yes)
    flag_size = Setting(2)  # when sampling rays: 0=point,1=Gaussian,2=FT(Divergences)

    # sampling rays
    number_of_rays = Setting(500)
    seed = Setting(5676561)


    plot_undulator_graph = 1

    beam_out = None


    def __init__(self):
        super().__init__()

        tab_undulator = oasysgui.createTabPage(self.tabs_control_area, "Undulator Setting")

        # undulator parameters box
        left_box_3 = oasysgui.widgetBox(tab_undulator, "Undulator Parameters", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_3, self, "K_vertical", "K value", labelWidth=260, tooltip="K_vertical", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "period_length", "ID period [m] [m]", labelWidth=260, tooltip="period_length", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "number_of_periods", "Number of Periods", labelWidth=260, tooltip="number_of_periods", valueType=int, orientation="horizontal")



        # photon energy Box
        left_box_10 = oasysgui.widgetBox(tab_undulator, "Sampling intervals", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_10, self, "emin", "Min photon energy [eV]", labelWidth=260, tooltip="emin", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_10, self, "emax", "Max photon energy [eV]", labelWidth=260, tooltip="emax", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_10, self, "maxangle", "Max elevation angle for radiation theta [rad]", labelWidth=260, tooltip="maxangle", valueType=float, orientation="horizontal")


        # internal parameters
        left_box_11 = oasysgui.widgetBox(tab_undulator, "Internal calculation parameters", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_11, self, "ng_e", "Points in Photon energy (if polychromatic)", tooltip="ng_e", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "ng_t", "Points in theta [elevation]", tooltip="ng_t", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "ng_p", "Points in phi [azimuthal]", tooltip="ng_p", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "ng_j", "Points in electron trajectory", tooltip="ng_j", labelWidth=250, valueType=int, orientation="horizontal")
        orangegui.comboBox(left_box_11, self, "code_undul_phot", label="Use code",
                           items=["internal", "pysru", "srw"], labelWidth=260, orientation="horizontal")
        orangegui.comboBox(left_box_11, self, "flag_size", label="Size sampling in real space",
                           items=["point", "Gaussian", "FT(Divergences)"], labelWidth=260, orientation="horizontal")

        # sampling
        left_box_12 = oasysgui.widgetBox(tab_undulator, "Sampling rays", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_12, self, "number_of_rays", "Number of rays", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_12, self, "seed", "Seed", tooltip="Seed (0=clock)", labelWidth=250, valueType=int, orientation="horizontal")


        # undulator plots
        self.add_specific_undulator_plots()

        self.set_visibility()

        orangegui.rubber(self.controlArea)


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

        if self.emin == self.emax:
            self.undulator_tab = [
                orangegui.createTabPage(self.undulator_tabs, "Radiation intensity (polar)"),
                orangegui.createTabPage(self.undulator_tabs, "Polarization (polar)"),
                orangegui.createTabPage(self.undulator_tabs, "Radiation intensity (cartesian - interpolated)"),
                orangegui.createTabPage(self.undulator_tabs, "Photon source size"),
            ]

            self.undulator_plot_canvas = [None,None,None,None,]
        else:
            self.undulator_tab = [
                orangegui.createTabPage(self.undulator_tabs, "Radiation (polar)"),
                orangegui.createTabPage(self.undulator_tabs, "Polarization (polar)"),
                orangegui.createTabPage(self.undulator_tabs, "Radiation (interpolated)"),
                orangegui.createTabPage(self.undulator_tabs, "Photon source size"),
                orangegui.createTabPage(self.undulator_tabs, "Power Density (interpolated)"),
                orangegui.createTabPage(self.undulator_tabs, "Flux"),
                orangegui.createTabPage(self.undulator_tabs, "Spectral Power"),
            ]

            self.undulator_plot_canvas = [None,None,None,None,None,None,None,]

        for tab in self.undulator_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)
        # self.undulator_plot_canvas = [None, None, None, None, None, None]

        self.undulator_tabs.setCurrentIndex(current_tab)



    def set_visibility(self):
        pass
        # self.conventional_sinusoidal_box.setVisible(self.magnetic_field_source == 0)
        # self.b_from_file_box.setVisible(self.magnetic_field_source == 1)
        # self.b_from_harmonics_box.setVisible(self.magnetic_field_source == 2)

    # def select_file_with_B_vs_Y(self):
    #     self.le_file_with_b_vs_y.setText(oasysgui.selectFileFromDialog(self, self.file_with_b_vs_y, "Open File With B vs Y"))
    #
    # def select_file_with_harmonics(self):
    #     self.le_file_with_harmonics.setText(oasysgui.selectFileFromDialog(self, self.file_with_harmonics, "Open File With Harmonics"))
    #
    # def set_shift_X_flag(self):
    #     self.shift_x_value_box.setVisible(self.shift_x_flag==5)
    #     self.shift_x_value_box_hidden.setVisible(self.shift_x_flag!=5)
    #
    # def set_shift_beta_X_flag(self):
    #     self.shift_betax_value_box.setVisible(self.shift_betax_flag==5)
    #     self.shift_betax_value_box_hidden.setVisible(self.shift_betax_flag!=5)

    def get_lightsource(self):
        # syned
        electron_beam = self.get_electron_beam()
        print("\n\n>>>>>> ElectronBeam info: ", electron_beam.info(), type(electron_beam))

        ng_j = 501 # trajectory points

        if self.type_of_properties == 3:
            flag_emittance = 0
        else:
            flag_emittance = 1
        # S4undulator

        code_undul_phot = ["internal", "pysru", "srw"][self.code_undul_phot]

        sourceundulator = S4Undulator(
            K_vertical=self.K_vertical,                # syned Undulator parameter
            period_length=self.period_length,          # syned Undulator parameter
            number_of_periods=self.number_of_periods,  # syned Undulator parameter
            emin=self.emin,  # Photon energy scan from energy (in eV)
            emax=self.emax,  # Photon energy scan to energy (in eV)
            ng_e=self.ng_e,  # Photon energy scan number of points
            maxangle=self.maxangle,  # Maximum radiation semiaperture in RADIANS
            ng_t=self.ng_t,  # Number of points in angle theta
            ng_p=self.ng_p,  # Number of points in angle phi
            ng_j=self.ng_j,  # Number of points in electron trajectory (per period) for internal calculation only
            code_undul_phot=code_undul_phot,  # internal, pysru, srw
            flag_emittance=self.flag_emittance,  # when sampling rays: Use emittance (0=No, 1=Yes)
            flag_size=self.flag_size,  # when sampling rays: 0=point,1=Gaussian,2=FT(Divergences)
            )

        print(">>>>>> \n\n S4Undulator info: ", sourceundulator.info())


        # S4undulatorLightSource
        lightsource = S4UndulatorLightSource(name='undulator',
                                           electron_beam=electron_beam,
                                           magnetic_structure=sourceundulator,
                                           nrays=self.number_of_rays,
                                           seed=self.seed)

        print("\n\n>>>>>> S4undulatorLightSource info: ", lightsource.info())

        return lightsource


    def run_shadow4(self):

        sys.stdout = EmittingStream(textWritten=self._write_stdout)

        self._set_plot_quality()

        self.progressBarInit()

        light_source = self.get_lightsource()

        self.progressBarSet(5)
        #
        # run shadow4
        #
        t00 = time.time()
        print(">>>> starting calculation...")
        output_beam = light_source.get_beam()
        # todo:
        # photon_energy, flux, spectral_power = light_source.calculate_spectrum()
        t11 = time.time() - t00
        print(">>>> time for %d rays: %f s, %f min, " % (self.number_of_rays, t11, t11 / 60))


        #
        # plots
        #
        self._plot_results(output_beam, None, progressBarValue=80)
        #todo:
        # self.refresh_specific_undulator_plots(light_source, photon_energy, flux, spectral_power)


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

    def refresh_specific_undulator_plots(self, lightsource=None, e=None, f=None, w=None):
        pass

        # if self.plot_undulator_graph == 0:
        #     for undulator_plot_slot_index in range(6):
        #         current_item = self.wiggler_tab[wiggler_plot_slot_index].layout().itemAt(0)
        #         self.wiggler_tab[wiggler_plot_slot_index].layout().removeItem(current_item)
        #         plot_widget_id = oasysgui.QLabel() # TODO: is there a better way to clean this??????????????????????
        #         self.wiggler_tab[wiggler_plot_slot_index].layout().addWidget(plot_widget_id)
        # else:
        #
        #     if lightsource is None: return
        #     traj, pars = lightsource.get_trajectory()
        #
        #     self.plot_widget_item(traj[1, :],traj[7, :],0,
        #                           title="Magnetic Field",xtitle="y [m]",ytitle="B [T]")
        #
        #     self.plot_widget_item(traj[1, :],traj[6, :],1,
        #                           title="Electron curvature",xtitle="y [m]",ytitle="cirvature [m^-1]")
        #
        #     self.plot_widget_item(traj[1, :],traj[3, :],2,
        #                           title="Electron velocity",xtitle="y [m]",ytitle="BetaX")
        #
        #     self.plot_widget_item(traj[1, :],traj[0, :],3,
        #                           title="Electron trajectory",xtitle="y [m]",ytitle="x [m]")
        #
        #     self.plot_widget_item(e,f,4,
        #                           title="Wiggler spectrum (current = %5.1f)"%self.ring_current,
        #                           xtitle="Photon energy [eV]",ytitle=r"Photons/s/0.1%bw")
        #
        #     self.plot_widget_item(e,w,5,
        #                           title="Wiggler spectrum (current = %5.1f)"%self.ring_current,
        #                           xtitle="Photon energy [eV]",ytitle="Spectral power [W/eV]")

    def plot_undulator_item(self,x,y,undulator_plot_slot_index,title="",xtitle="",ytitle=""):

        self.undulator_tab[undulator_plot_slot_index].layout().removeItem(self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_data1D(x.copy(),y.copy(),title=title,xtitle=xtitle,ytitle=ytitle,symbol='.')
        self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)

    def receive_syned_data(self, data):
        pass
        # sys.stdout = EmittingStream(textWritten=self.writeStdOut)
        # if data is not None:
        #     if isinstance(data, Beamline):
        #         if not data.get_light_source() is None:
        #             if isinstance(data.get_light_source().get_magnetic_structure(), InsertionDevice):
        #                 print(data.get_light_source().get_magnetic_structure(), InsertionDevice)
        #                 light_source = data.get_light_source()
        #
        #                 self.magnetic_field_source = 0
        #                 self.set_visibility()
        #
        #                 w = light_source.get_magnetic_structure()
        #                 self.number_of_periods = int(w.number_of_periods())
        #                 self.id_period = w.period_length()
        #                 self.k_value = w.K_vertical()
        #
        #                 self.populate_fields_from_electron_beam(light_source.get_electron_beam())
        #
        #             else:
        #                 raise ValueError("Syned light source not congruent")
        #         else:
        #             raise ValueError("Syned data not correct: light source not present")
        #     else:
        #         raise ValueError("Syned data not correct")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWUndulator()
    ow.show()
    a.exec_()

