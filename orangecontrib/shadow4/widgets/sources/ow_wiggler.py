import sys
import time

from orangecontrib.shadow4.widgets.gui.ow_electron_beam import OWElectronBeam
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D
from orangecontrib.shadow4.util.shadow_objects import ShadowBeam

from oasys.widgets import gui as oasysgui

from oasys.util.oasys_util import EmittingStream

from syned.beamline.beamline import Beamline
from syned.storage_ring.magnetic_structures.insertion_device import InsertionDevice
from syned.widget.widget_decorator import WidgetDecorator

from orangewidget import gui as orangegui
from orangewidget.settings import Setting


from shadow4.sources.wiggler.s4_wiggler import S4Wiggler
from shadow4.sources.wiggler.s4_wiggler_light_source import S4WigglerLightSource
from shadow4.beamline.s4_beamline import S4Beamline

class OWWiggler(OWElectronBeam, WidgetDecorator):

    name = "Wiggler Light Source"
    description = "Wiggler Light Source"
    icon = "icons/wiggler.png"
    priority = 3


    inputs = []
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Beam4",
                "type":ShadowBeam,
                "doc":"",}]

    magnetic_field_source = Setting(1)
    number_of_periods = Setting(1)
    k_value = Setting(10.0)
    id_period = Setting(0.010)
    file_with_b_vs_y = Setting("https://raw.githubusercontent.com/srio/shadow4/master/examples/sources/BM_multi.b")
    file_with_harmonics = Setting("tmp.h")

    shift_x_flag = Setting(0)
    shift_x_value =Setting(0.0)

    shift_betax_flag = Setting(0)
    shift_betax_value = Setting(0.0)

    e_min = Setting(0.4)
    e_max = Setting(0.4)
    number_of_rays = Setting(500)
    seed = Setting(5676561)

    plot_wiggler_graph = 1

    beam_out = None


    def __init__(self):
        super().__init__()

        tab_wiggler = oasysgui.createTabPage(self.tabs_control_area, "Wiggler Setting")

        # wiggler parameters box
        left_box_3 = oasysgui.widgetBox(tab_wiggler, "Wiggler Parameters", addSpace=False, orientation="vertical", height=200)

        orangegui.comboBox(left_box_3, self, "magnetic_field_source", label="Type", items=["conventional/sinusoidal", "B from file (y [m], Bz [T])", "B from harmonics"], callback=self.set_visibility, labelWidth=220, orientation="horizontal")

        oasysgui.lineEdit(left_box_3, self, "number_of_periods", "Number of Periods", labelWidth=260, tooltip="Number of Periods", valueType=int, orientation="horizontal")

        self.conventional_sinusoidal_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.conventional_sinusoidal_box, self, "k_value", "K value", labelWidth=260, tooltip="K value", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.conventional_sinusoidal_box, self, "id_period", "ID period [m]", labelWidth=260, tooltip="ID period [m]", valueType=float, orientation="horizontal")

        self.b_from_file_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.b_from_file_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_b_vs_y = oasysgui.lineEdit(file_box, self, "file_with_b_vs_y", "File/Url with B vs Y", labelWidth=150, tooltip="File/Url with B vs Y", valueType=str, orientation="horizontal")

        orangegui.button(file_box, self, "...", callback=self.select_file_with_B_vs_Y)

        self.b_from_harmonics_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.b_from_harmonics_box, self, "id_period", "ID period [m]", labelWidth=260, tooltip="ID period [m]", valueType=float, orientation="horizontal")

        file_box = oasysgui.widgetBox(self.b_from_harmonics_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_harmonics = oasysgui.lineEdit(file_box, self, "file_with_harmonics", "File/Url with harmonics", labelWidth=150, tooltip="File/Url with harmonics", valueType=str, orientation="horizontal")

        orangegui.button(file_box, self, "...", callback=self.select_file_with_harmonics)


        # Electron initial conditions Box
        left_box_10 = oasysgui.widgetBox(tab_wiggler, "Electron Initial Condition", addSpace=False, orientation="vertical", height=200)


        orangegui.comboBox(left_box_10, self, "shift_betax_flag", label="Shift Transversal Velocity", items=["No shift", "Half excursion", "Minimum", "Maximum", "Value at zero", "User value"], callback=self.set_shift_beta_X_flag, labelWidth=260, orientation="horizontal")
        self.shift_betax_value_box = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        self.shift_betax_value_box_hidden = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        oasysgui.lineEdit(self.shift_betax_value_box, self, "shift_betax_value", "Value", labelWidth=260, valueType=float, orientation="horizontal")

        orangegui.comboBox(left_box_10, self, "shift_x_flag", label="Shift Transversal Coordinate", items=["No shift", "Half excursion", "Minimum", "Maximum", "Value at zero", "User value"], callback=self.set_shift_X_flag, labelWidth=260, orientation="horizontal")
        self.shift_x_value_box = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        self.shift_x_value_box_hidden = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        oasysgui.lineEdit(self.shift_x_value_box, self, "shift_x_value", "Value [m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_shift_X_flag()
        self.set_shift_beta_X_flag()



        # Calculation Box
        left_box_11 = oasysgui.widgetBox(tab_wiggler, "Sampling rays", addSpace=False, orientation="vertical", height=200)

        oasysgui.lineEdit(left_box_11, self, "e_min", "Min photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "e_max", "Max photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "number_of_rays", "Number of rays", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "seed", "Seed", tooltip="Seed (0=clock)", labelWidth=250, valueType=int, orientation="horizontal")

        self.set_shift_X_flag()
        self.set_shift_beta_X_flag()


        # wiggler plots
        self.add_specific_wiggler_plots()

        self.set_visibility()

        orangegui.rubber(self.controlArea)


    def add_specific_wiggler_plots(self):

        wiggler_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

        self.main_tabs.insertTab(1, wiggler_plot_tab, "Wiggler Plots")

        view_box = oasysgui.widgetBox(wiggler_plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.wiggler_view_type_combo = orangegui.comboBox(view_box_1, self,
                                            "plot_wiggler_graph",
                                                          label="Plot Graphs?",
                                                          labelWidth=220,
                                                          items=["No", "Yes"],
                                                          callback=self.refresh_specific_wiggler_plots,
                                                          sendSelectedValue=False,
                                                          orientation="horizontal")

        self.wiggler_tab = []
        self.wiggler_tabs = oasysgui.tabWidget(wiggler_plot_tab)

        current_tab = self.wiggler_tabs.currentIndex()

        size = len(self.wiggler_tab)
        indexes = range(0, size)
        for index in indexes:
            self.wiggler_tabs.removeTab(size-1-index)

        self.wiggler_tab = [
            orangegui.createTabPage(self.wiggler_tabs, "Magnetic Field"),
            orangegui.createTabPage(self.wiggler_tabs, "Electron Curvature"),
            orangegui.createTabPage(self.wiggler_tabs, "Electron Velocity"),
            orangegui.createTabPage(self.wiggler_tabs, "Electron Trajectory"),
            orangegui.createTabPage(self.wiggler_tabs, "Wiggler Spectrum"),
            orangegui.createTabPage(self.wiggler_tabs, "Wiggler Spectral power")
        ]

        for tab in self.wiggler_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.wiggler_plot_canvas = [None, None, None, None, None, None]

        self.wiggler_tabs.setCurrentIndex(current_tab)


    def set_visibility(self):
        self.conventional_sinusoidal_box.setVisible(self.magnetic_field_source == 0)
        self.b_from_file_box.setVisible(self.magnetic_field_source == 1)
        self.b_from_harmonics_box.setVisible(self.magnetic_field_source == 2)

    def select_file_with_B_vs_Y(self):
        self.le_file_with_b_vs_y.setText(oasysgui.selectFileFromDialog(self, self.file_with_b_vs_y, "Open File With B vs Y"))

    def select_file_with_harmonics(self):
        self.le_file_with_harmonics.setText(oasysgui.selectFileFromDialog(self, self.file_with_harmonics, "Open File With Harmonics"))

    def set_shift_X_flag(self):
        self.shift_x_value_box.setVisible(self.shift_x_flag==5)
        self.shift_x_value_box_hidden.setVisible(self.shift_x_flag!=5)

    def set_shift_beta_X_flag(self):
        self.shift_betax_value_box.setVisible(self.shift_betax_flag==5)
        self.shift_betax_value_box_hidden.setVisible(self.shift_betax_flag!=5)

    def get_lightsource(self):
        # syned
        electron_beam = self.get_electron_beam()
        print("\n\n>>>>>> ElectronBeam info: ", electron_beam.info(), type(electron_beam))

        ng_j = 501 # trajectory points

        if self.type_of_properties == 3:
            flag_emittance = 0
        else:
            flag_emittance = 1
        # S4Wiggler
        if self.magnetic_field_source == 0:
            sourcewiggler = S4Wiggler(
                    magnetic_field_periodic  = 1,   # 0=external, 1=periodic
                    file_with_magnetic_field = "",  # useful if magnetic_field_periodic=0
                    K_vertical               = self.k_value,
                    period_length            = self.id_period,
                    number_of_periods        = self.number_of_periods, # syned Wiggler pars: useful if magnetic_field_periodic=1
                    emin                     = self.e_min,     # Photon energy scan from energy (in eV)
                    emax                     = self.e_max,     # Photon energy scan to energy (in eV)
                    ng_e                     = 100,            # Photon energy scan number of points
                    ng_j                     = ng_j ,          # Number of points in electron trajectory (per period) for internal calculation only
                    flag_emittance           = flag_emittance, # Use emittance (0=No, 1=Yes)
                    shift_x_flag             = 0,
                    shift_x_value            = 0.0,
                    shift_betax_flag         = 0,
                    shift_betax_value        = 0.0,
                    )

        elif self.magnetic_field_source == 1:
            if self.e_min == self.e_max:
                ng_e = 1
            else:
                ng_e = 10

            sourcewiggler = S4Wiggler(
                magnetic_field_periodic   = 0,
                file_with_magnetic_field  = self.file_with_b_vs_y,
                emin                      = self.e_min,
                emax                      = self.e_max,
                ng_e                      = ng_e,
                ng_j                      = ng_j,
                flag_emittance            = flag_emittance,  # Use emittance (0=No, 1=Yes)
                shift_x_flag              = 4,
                shift_x_value             = 0.0,
                shift_betax_flag          = 4,
                shift_betax_value         = 0.0,
            )
            sourcewiggler.set_electron_initial_conditions_by_label(
                position_label="value_at_zero",
                velocity_label="value_at_zero",
                )

        elif self.magnetic_field_source == 2:
            raise Exception(NotImplemented)

        if self.e_min == self.e_max:
            sourcewiggler.set_energy_monochromatic(self.e_min)

        sourcewiggler.set_electron_initial_conditions(
                        shift_x_flag=self.shift_x_flag,
                        shift_x_value=self.shift_x_value,
                        shift_betax_flag=self.shift_betax_flag,
                        shift_betax_value=self.shift_betax_value)

        print(">>>>>> \n\n S4Wiggler info: ", sourcewiggler.info())


        # S4WigglerLightSource
        lightsource = S4WigglerLightSource(name='wiggler',
                                           electron_beam=electron_beam,
                                           magnetic_structure=sourcewiggler,
                                           nrays=self.number_of_rays,
                                           seed=self.seed)

        print("\n\n>>>>>> S4WigglerLightSource info: ", lightsource.info())

        return lightsource


    def run_shadow4(self):

        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        self.set_PlotQuality()

        self.progressBarInit()

        light_source = self.get_lightsource()

        self.progressBarSet(5)
        #
        # run shadow4
        #
        t00 = time.time()
        print(">>>> starting calculation...")
        beam = light_source.get_beam()
        photon_energy, flux, spectral_power = light_source.calculate_spectrum()
        t11 = time.time() - t00
        print(">>>> time for %d rays: %f s, %f min, " % (self.number_of_rays, t11, t11 / 60))


        #
        # plots
        #
        beamline = S4Beamline(light_source=light_source)
        BEAM = ShadowBeam(beam=beam, oe_number=0, number_of_rays=self.number_of_rays, beamline=beamline)
        self.plot_results(BEAM, progressBarValue=80)
        self.refresh_specific_wiggler_plots(light_source, photon_energy, flux, spectral_power)


        #
        # script
        #
        script = light_source.to_python_code()
        script += "\n\n# test plot\nfrom srxraylib.plot.gol import plot_scatter"
        script += "\nrays = beam.get_rays()"
        script += "\nplot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 2], title='(X,Z) in microns')"

#         script_template = """
#
# # run shadow4
# beam = light_source.get_beam(NRAYS={NRAYS}, SEED={SEED})
# photon_energy, flux, spectral_power = light_source.calculate_spectrum()"""
#         script_dict = {
#             "NRAYS": self.number_of_rays,
#             "SEED": self.seed,
#         }
#
#         script += script_template.format_map(script_dict)


        self.shadow4_script.set_code(script)

        self.progressBarFinished()

        #
        # send beam
        #
        self.send("Beam4", BEAM)


    def refresh_specific_wiggler_plots(self, lightsource=None, e=None, f=None, w=None):

        if self.plot_wiggler_graph == 0:
            for wiggler_plot_slot_index in range(6):
                current_item = self.wiggler_tab[wiggler_plot_slot_index].layout().itemAt(0)
                self.wiggler_tab[wiggler_plot_slot_index].layout().removeItem(current_item)
                plot_widget_id = oasysgui.QLabel() # TODO: is there a better way to clean this??????????????????????
                self.wiggler_tab[wiggler_plot_slot_index].layout().addWidget(plot_widget_id)
        else:

            if lightsource is None: return
            traj, pars = lightsource.get_trajectory()

            self.plot_widget_item(traj[1, :],traj[7, :],0,
                                  title="Magnetic Field",xtitle="y [m]",ytitle="B [T]")

            self.plot_widget_item(traj[1, :],traj[6, :],1,
                                  title="Electron curvature",xtitle="y [m]",ytitle="cirvature [m^-1]")

            self.plot_widget_item(traj[1, :],traj[3, :],2,
                                  title="Electron velocity",xtitle="y [m]",ytitle="BetaX")

            self.plot_widget_item(traj[1, :],traj[0, :],3,
                                  title="Electron trajectory",xtitle="y [m]",ytitle="x [m]")

            self.plot_widget_item(e,f,4,
                                  title="Wiggler spectrum (current = %5.1f)"%self.ring_current,
                                  xtitle="Photon energy [eV]",ytitle=r"Photons/s/0.1%bw")

            self.plot_widget_item(e,w,5,
                                  title="Wiggler spectrum (current = %5.1f)"%self.ring_current,
                                  xtitle="Photon energy [eV]",ytitle="Spectral power [W/eV]")

    def plot_widget_item(self,x,y,wiggler_plot_slot_index,title="",xtitle="",ytitle=""):

        self.wiggler_tab[wiggler_plot_slot_index].layout().removeItem(self.wiggler_tab[wiggler_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_data1D(x.copy(),y.copy(),title=title,xtitle=xtitle,ytitle=ytitle,symbol='.')
        self.wiggler_tab[wiggler_plot_slot_index].layout().addWidget(plot_widget_id)

    def receive_syned_data(self, data):
        sys.stdout = EmittingStream(textWritten=self.writeStdOut)
        if data is not None:
            if isinstance(data, Beamline):
                if not data.get_light_source() is None:
                    if isinstance(data.get_light_source().get_magnetic_structure(), InsertionDevice):
                        print(data.get_light_source().get_magnetic_structure(), InsertionDevice)
                        light_source = data.get_light_source()

                        self.magnetic_field_source = 0
                        self.set_visibility()

                        w = light_source.get_magnetic_structure()
                        self.number_of_periods = int(w.number_of_periods())
                        self.id_period = w.period_length()
                        self.k_value = w.K_vertical()

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
    ow = OWWiggler()
    ow.show()
    a.exec_()

