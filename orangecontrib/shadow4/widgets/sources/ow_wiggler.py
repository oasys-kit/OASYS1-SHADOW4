import sys
import time
# from syned.storage_ring.magnetic_structures.wiggler import Wiggler
#
# from orangecontrib.shadow4.widgets.gui.ow_light_source import OWLightSource
# # from orangecontrib.syned.widgets.gui.ow_light_source import OWLightSource
# # from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
# from orangecontrib.shadow4.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow4.widgets.gui.ow_electron_beam import OWElectronBeam
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D

from oasys.widgets import gui as oasysgui
from orangewidget import gui as orangegui
from orangewidget.settings import Setting

# from syned.storage_ring.electron_beam import ElectronBeam
from shadow4.syned.magnetic_structure_1D_field import MagneticStructure1DField
from syned.storage_ring.magnetic_structures.wiggler import Wiggler

from shadow4.sources.wiggler.source_wiggler import SourceWiggler
from shadow4.compatibility.beam3 import Beam3
from srxraylib.sources.srfunc import wiggler_spectrum


# for the moment, use ShadowOui beam...
from orangecontrib.shadow.util.shadow_objects import ShadowBeam


class OWWiggler(OWElectronBeam):

    name = "Wiggler Light Source"
    description = "Wiggler Light Source"
    icon = "icons/wiggler.png"
    priority = 3


    # inputs = [("Trigger", TriggerOut, "sendNewBeam")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"}]


    magnetic_field_source = Setting(0)
    number_of_periods = Setting(1)
    k_value = Setting(10.0)
    id_period = Setting(0.010)
    file_with_b_vs_y = Setting("/Users/srio/Oasys/BM_multi7.b")
    file_with_harmonics = Setting("tmp.h")

    shift_x_flag = Setting(4)
    shift_x_value =Setting(0.0)

    shift_betax_flag = Setting(4)
    shift_betax_value = Setting(0.0)

    e_min = Setting(0.1)
    e_max = Setting(0.1)
    n_rays = Setting(100)

    plot_wiggler_graph = 1

    workspace_units_to_cm = 1.0

    shadowoui_neam = None

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

        orangegui.button(file_box, self, "...", callback=self.selectFileWithBvsY)

        self.b_from_harmonics_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.b_from_harmonics_box, self, "id_period", "ID period [m]", labelWidth=260, tooltip="ID period [m]", valueType=float, orientation="horizontal")

        file_box = oasysgui.widgetBox(self.b_from_harmonics_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_harmonics = oasysgui.lineEdit(file_box, self, "file_with_harmonics", "File/Url with harmonics", labelWidth=150, tooltip="File/Url with harmonics", valueType=str, orientation="horizontal")

        orangegui.button(file_box, self, "...", callback=self.selectFileWithHarmonics)


        # Electron Box
        left_box_10 = oasysgui.widgetBox(tab_wiggler, "Electron Initial Condition", addSpace=False, orientation="vertical", height=200)


        orangegui.comboBox(left_box_10, self, "shift_betax_flag", label="Shift Transversal Velocity", items=["No shift", "Half excursion", "Minimum", "Maximum", "Value at zero", "User value"], callback=self.set_ShiftBetaXFlag, labelWidth=260, orientation="horizontal")
        self.shift_betax_value_box = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        self.shift_betax_value_box_hidden = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        oasysgui.lineEdit(self.shift_betax_value_box, self, "shift_betax_value", "Value", labelWidth=260, valueType=float, orientation="horizontal")

        orangegui.comboBox(left_box_10, self, "shift_x_flag", label="Shift Transversal Coordinate", items=["No shift", "Half excursion", "Minimum", "Maximum", "Value at zero", "User value"], callback=self.set_ShiftXFlag, labelWidth=260, orientation="horizontal")
        self.shift_x_value_box = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        self.shift_x_value_box_hidden = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        oasysgui.lineEdit(self.shift_x_value_box, self, "shift_x_value", "Value [m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_ShiftXFlag()
        self.set_ShiftBetaXFlag()



        # Calculation Box
        left_box_11 = oasysgui.widgetBox(tab_wiggler, "Sampling rays", addSpace=False, orientation="vertical", height=200)

        oasysgui.lineEdit(left_box_11, self, "e_min", "Min photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "e_max", "Max photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "n_rays", "Number of rays", labelWidth=260, valueType=int, orientation="horizontal")

        self.set_ShiftXFlag()
        self.set_ShiftBetaXFlag()


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
                                            callback=self.plot_widget_all,
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

    def set_PlotGraphs(self):
        pass

    def set_visibility(self):
        self.conventional_sinusoidal_box.setVisible(self.magnetic_field_source == 0)
        self.b_from_file_box.setVisible(self.magnetic_field_source == 1)
        self.b_from_harmonics_box.setVisible(self.magnetic_field_source == 2)


    def selectFileWithBvsY(self):
        self.le_file_with_b_vs_y.setText(oasysgui.selectFileFromDialog(self, self.file_with_b_vs_y, "Open File With B vs Y"))

    def selectFileWithHarmonics(self):
        self.le_file_with_harmonics.setText(oasysgui.selectFileFromDialog(self, self.file_with_harmonics, "Open File With Harmonics"))


    def set_ShiftXFlag(self):
        self.shift_x_value_box.setVisible(self.shift_x_flag==5)
        self.shift_x_value_box_hidden.setVisible(self.shift_x_flag!=5)

    def set_ShiftBetaXFlag(self):
        self.shift_betax_value_box.setVisible(self.shift_betax_flag==5)
        self.shift_betax_value_box_hidden.setVisible(self.shift_betax_flag!=5)


    # def get_magnetic_structure(self):
    #     return Wiggler(K_horizontal=self.K_horizontal,
    #                    K_vertical=self.K_vertical,
    #                    period_length=self.period_length,
    #                    number_of_periods=self.number_of_periods)
    #
    # def check_magnetic_structure_instance(self, magnetic_structure):
    #     if not isinstance(magnetic_structure, Wiggler):
    #         raise ValueError("Magnetic Structure is not a Wiggler")
    #
    # def populate_magnetic_structure(self, magnetic_structure):
    #     if not isinstance(magnetic_structure, Wiggler):
    #         raise ValueError("Magnetic Structure is not a Wiggler")
    #
    #     self.K_horizontal = magnetic_structure._K_horizontal
    #     self.K_vertical = magnetic_structure._K_vertical
    #     self.period_length = magnetic_structure._period_length
    #     self.number_of_periods = magnetic_structure._number_of_periods

    def run_shadow4(self):


        nTrajPoints = 501


        #
        # syned
        #


        syned_electron_beam = self.get_syned_electron_beam()

        print(syned_electron_beam.info())

        # B from file
        if self.magnetic_field_source == 0:
            syned_wiggler = Wiggler(
                K_vertical=self.k_value,
                K_horizontal=0.0,
                period_length=self.id_period,
                number_of_periods=self.number_of_periods
                )
        elif self.magnetic_field_source == 1:
            syned_wiggler = MagneticStructure1DField.initialize_from_file(self.file_with_b_vs_y)
        elif self.magnetic_field_source == 2:
            raise Exception(NotImplemented)

        print(syned_wiggler.info())
        sw = SourceWiggler()


        sourcewiggler = SourceWiggler(name="test",
                        syned_electron_beam=syned_electron_beam,
                        syned_wiggler=syned_wiggler,
                        flag_emittance=True,
                        emin=self.e_min,
                        emax=self.e_max,
                        ng_e=100,
                        ng_j=nTrajPoints)

        if self.e_min == self.e_max:
            sourcewiggler.set_energy_monochromatic(self.e_min)


        # sourcewiggler.set_electron_initial_conditions_by_label(velocity_label="value_at_zero",
        #                                                        position_label="value_at_zero",)

        sourcewiggler.set_electron_initial_conditions(
                        shift_x_flag=self.shift_x_flag,
                        shift_x_value=self.shift_x_value,
                        shift_betax_flag=self.shift_betax_flag,
                        shift_betax_value=self.shift_betax_value)

        # sourcewiggler.calculate_radiation()






        print(sourcewiggler.info())

        t00 = time.time()
        print(">>>> starting calculation...")
        rays = sourcewiggler.calculate_rays(NRAYS=self.n_rays)
        t11 = time.time() - t00
        print(">>>> time for %d rays: %f s, %f min, " % (self.n_rays, t11, t11 / 60))
        print(">>>   Results of calculate_radiation")
        print(">>>       trajectory.shape: ",sourcewiggler._result_trajectory.shape)
        print(">>>       cdf: ", sourcewiggler._result_cdf.keys())


        calculate_spectrum = True

        if calculate_spectrum:
            e, f, w = wiggler_spectrum(sourcewiggler._result_trajectory,
                                              enerMin=self.e_min,
                                              enerMax=self.e_max,
                                              nPoints=500,
                                              electronCurrent=self.ring_current,
                                              outFile="",
                                              elliptical=False)
            # from srxraylib.plot.gol import plot
            # plot(e, f, xlog=False, ylog=False, show=False,
            #      xtitle="Photon energy [eV]", ytitle="Flux [Photons/s/0.1%bw]", title="Flux")
            # plot(e, w, xlog=False, ylog=False, show=True,
            #      xtitle="Photon energy [eV]", ytitle="Spectral Power [E/eV]", title="Spectral Power")




        beam = Beam3.initialize_from_array(rays)


        #
        # wiggler plots
        #
        self.plot_widget_all(sourcewiggler,e,f,w)


        self.shadowoui_beam = ShadowBeam(oe_number = 0, beam = beam, number_of_rays = 0)

        self.plot_shadow_all()

        self.send("Beam", self.shadowoui_beam)

    def set_PlotQuality(self):
        self.plot_shadow_all()

    def plot_shadow_all(self):

        if self.view_type == 2:

            for slot_index in range(6):
                current_item = self.tab[slot_index].layout().itemAt(0)
                self.tab[slot_index].layout().removeItem(current_item)
                tmp = oasysgui.QLabel() # TODO: is there a better way to clean this??????????????????????
                self.tab[slot_index].layout().addWidget(tmp)


        elif self.view_type == 1:
            raise Exception(NotImplemented)
        else:
            self.plot_xy(self.shadowoui_beam, 10, 1, 3, 0, "(X,Z)", "X", "Z",     xum="um", yum="um", is_footprint=False)
            self.plot_xy(self.shadowoui_beam, 10, 4, 6, 1, "(X',Z')", "X'", "Z'", xum="urad", yum="urad", is_footprint=False)
            self.plot_xy(self.shadowoui_beam, 10, 1, 4, 2, "(X,X')", "X", "X'",   xum="um", yum="urad", is_footprint=False)
            self.plot_xy(self.shadowoui_beam, 10, 3, 6, 3, "(Z,Z')", "Z", "Z'",   xum="um", yum="urad", is_footprint=False)
            self.plot_histo(self.shadowoui_beam,10,11,4,"Photon energy","Photon energy [eV]","Intensity [a.u.]",xum="eV")


    def plot_widget_all(self,sourcewiggler=None,e=None,f=None,w=None):

        print(">>>>>>>>>>> ",sourcewiggler)
        import numpy

        if self.plot_wiggler_graph == 0:
            for wiggler_plot_slot_index in range(6):
                current_item = self.wiggler_tab[wiggler_plot_slot_index].layout().itemAt(0)
                self.wiggler_tab[wiggler_plot_slot_index].layout().removeItem(current_item)
                plot_widget_id = oasysgui.QLabel() # TODO: is there a better way to clean this??????????????????????
                self.wiggler_tab[wiggler_plot_slot_index].layout().addWidget(plot_widget_id)
        else:

            if sourcewiggler is None: return

            self.plot_widget_item(sourcewiggler._result_trajectory[1, :],sourcewiggler._result_trajectory[7, :],0,
                                  title="Magnetic Field",xtitle="y [m]",ytitle="B [T]")

            self.plot_widget_item(sourcewiggler._result_trajectory[1, :],sourcewiggler._result_trajectory[6, :],1,
                                  title="Electron curvature",xtitle="y [m]",ytitle="cirvature [m^-1]")

            self.plot_widget_item(sourcewiggler._result_trajectory[1, :],sourcewiggler._result_trajectory[3, :],2,
                                  title="Electron velocity",xtitle="y [m]",ytitle="BetaX")

            self.plot_widget_item(sourcewiggler._result_trajectory[1, :],sourcewiggler._result_trajectory[0, :],3,
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



if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWWiggler()
    ow.show()
    a.exec_()
    #ow.saveSettings()
