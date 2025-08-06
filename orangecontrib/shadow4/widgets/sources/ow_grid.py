import sys
from PyQt5.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement

from syned.widget.widget_decorator import WidgetDecorator

from shadow4.beamline.s4_beamline import S4Beamline
from shadow4.sources.source_geometrical.source_grid_polar import SourceGridPolar
from shadow4.sources.source_geometrical.source_grid_cartesian import SourceGridCartesian
from shadow4.tools.logger import set_verbose

from orangecontrib.shadow4.util.shadow4_util import TriggerToolsDecorator
from oasys.util.oasys_util import TriggerIn


class OWGrid(GenericElement, WidgetDecorator, TriggerToolsDecorator):

    name = "Grid Source"
    description = "Shadow Source: Grid Source"
    icon = "icons/grid.png"
    priority = 2

    inputs = []
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Shadow Data",
                "type":ShadowData,
                "doc":"",}]

    TriggerToolsDecorator.append_trigger_input_for_sources(inputs)
    TriggerToolsDecorator.append_trigger_output(outputs)

    # for both grid and cartesian
    coordinates = Setting(1)

    real_space_width_x = Setting(2e-3)
    real_space_width_z = Setting(2e-3)
    real_space_center_x = Setting(0.0)
    real_space_center_z = Setting(0.0)

    direction_space_width_x = Setting(20e-3)
    direction_space_width_z = Setting(20e-3)
    direction_space_center_x = Setting(0.0)
    direction_space_center_z = Setting(0.0)

    # for grid
    real_space_points_r = Setting(2)
    real_space_points_theta = Setting(8)

    direction_space_points_r = Setting(3)
    direction_space_points_theta = Setting(359)

    # for cartesian
    direction_space_width_y = Setting(20e-3)
    real_space_points_x = Setting(10)
    real_space_points_y = Setting(10)
    real_space_points_z = Setting(10)

    direction_space_points_x = Setting(1)
    direction_space_points_z = Setting(1)


    units=Setting(0)
    single_line_value = Setting(1000.0)

    # polarization = Setting(1)
    polarization_phase_deg = Setting(0.0)
    polarization_degree = Setting(1.0)
    coherent_beam = Setting(1)


    def __init__(self):
        super().__init__(show_automatic_box=False, has_footprint=False)


        self.runaction = widget.OWAction("Run Shadow4/Source", self)
        self.runaction.triggered.connect(self.run_shadow4)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run shadow4/source", callback=self.run_shadow4)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        ################################################################################################################
        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT + 60)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH - 5)

        tab_basic = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_geometry = oasysgui.createTabPage(tabs_setting, "Geometry Setting")
        tab_energy = oasysgui.createTabPage(tabs_setting, "Energy/Polarization Setting")

        ##############################
        # BASIC

        left_box_1 = oasysgui.widgetBox(tab_basic, "Coordinates", addSpace=True, orientation="vertical")
        gui.comboBox(left_box_1, self, "coordinates", label="Coordinates", labelWidth=355,
                     items=["Cartesian", "Polar"], orientation="horizontal",
                     callback=self.set_coordinates_visibility)

        #### points
        points_box = oasysgui.widgetBox(tab_basic, "Number of points", addSpace=True,
                                                   orientation="vertical")
        ##
        self.points_polar_box = oasysgui.widgetBox(points_box, "", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.points_polar_box, self, "real_space_points_r",
                          "Real space Radial points", tooltip="real_space_points_r", labelWidth=260, valueType=int,
                          orientation="horizontal")

        oasysgui.lineEdit(self.points_polar_box, self, "real_space_points_theta",
                          "Real Space Azimuthal points", tooltip="real_space_points_theta", labelWidth=260, valueType=int,
                          orientation="horizontal")

        oasysgui.lineEdit(self.points_polar_box, self, "direction_space_points_r",
                          "Direction space Radial points", tooltip="direction_space_points_r", labelWidth=260, valueType=int,
                          orientation="horizontal")

        oasysgui.lineEdit(self.points_polar_box, self, "direction_space_points_theta",
                          "Direction space Azimuthal points", tooltip="direction_space_points_theta", labelWidth=260, valueType=int,
                          orientation="horizontal")

        ##
        self.points_cartesian_box = oasysgui.widgetBox(points_box, "", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.points_cartesian_box, self, "real_space_points_x",
                          "Real space X points", tooltip="real_space_points_x", labelWidth=260, valueType=int,
                          orientation="horizontal")

        oasysgui.lineEdit(self.points_cartesian_box, self, "real_space_points_z",
                          "Real Space Z points", tooltip="real_space_points_z", labelWidth=260, valueType=int,
                          orientation="horizontal")

        oasysgui.lineEdit(self.points_cartesian_box, self, "direction_space_points_x",
                          "Direction space X' points", tooltip="direction_space_points_x", labelWidth=260, valueType=int,
                          orientation="horizontal")

        oasysgui.lineEdit(self.points_cartesian_box, self, "direction_space_points_z",
                          "Direction space Z' points", tooltip="direction_space_points_z", labelWidth=260, valueType=int,
                          orientation="horizontal")
        ##############################
        # GEOMETRY

        left_box_2 = oasysgui.widgetBox(tab_geometry, "", addSpace=True, orientation="vertical", height=550)

        ###### real space
        real_distribution_box = oasysgui.widgetBox(left_box_2, "Real space", addSpace=True,
                                                      orientation="vertical") #, height=260)

        oasysgui.lineEdit(real_distribution_box, self, "real_space_center_x",
                          "Center in X [m]", tooltip="real_space_center_x", labelWidth=260, valueType=float,
                          orientation="horizontal")

        oasysgui.lineEdit(real_distribution_box, self, "real_space_center_z",
                          "Center in Z [m]", tooltip="real_space_center_z", labelWidth=260, valueType=float,
                          orientation="horizontal")

        oasysgui.lineEdit(real_distribution_box, self, "real_space_width_x",
                          "Width in X [m]", tooltip="real_space_width_x", labelWidth=260, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(real_distribution_box, self, "real_space_width_z",
                          "Width in Z [m]", tooltip="real_space_width_z", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(left_box_2)

        ###### direction space
        angular_distribution_box = oasysgui.widgetBox(left_box_2, "Direction space (divergences)", addSpace=True,
                                                      orientation="vertical") #, height=260)

        oasysgui.lineEdit(angular_distribution_box, self, "direction_space_center_x",
                          "Center in X' [rad]", tooltip="direction_space_center_x", labelWidth=260, valueType=float,
                          orientation="horizontal")

        oasysgui.lineEdit(angular_distribution_box, self, "direction_space_center_z",
                          "Center in Z' [rad]", tooltip="direction_space_center_z", labelWidth=260, valueType=float,
                          orientation="horizontal")

        oasysgui.lineEdit(angular_distribution_box, self, "direction_space_width_x",
                          "Width in X' [rad]", tooltip="direction_space_width_x", labelWidth=260, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(angular_distribution_box, self, "direction_space_width_z",
                          "Width in Z' [rad]", tooltip="direction_space_width_z", labelWidth=260, valueType=float, orientation="horizontal")



        gui.separator(left_box_2)


        ##############################
        # ENERGY

        left_box_3 = oasysgui.widgetBox(tab_energy, "", addSpace=False, orientation="vertical") #, height=640)

        energy_wavelength_box = oasysgui.widgetBox(left_box_3, "Energy/Wavelength", addSpace=False,
                                                   orientation="vertical")

        gui.comboBox(energy_wavelength_box, self, "units", label="Units", labelWidth=260,
                     items=["Energy/eV", "Wavelength/Å"], orientation="horizontal")

        oasysgui.lineEdit(energy_wavelength_box, self, "single_line_value", "Value", tooltip="single_line_value", labelWidth=260, valueType=float,
                          orientation="horizontal")


        polarization_box = oasysgui.widgetBox(left_box_3, "Polarization", addSpace=False, orientation="vertical")

        self.ewp_box_8 = oasysgui.widgetBox(polarization_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.ewp_box_8, self, "polarization_degree", "Polarization Degree [cos_s/(cos_s+sin_s)]",
                          tooltip="polarization_degree", labelWidth=310, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ewp_box_8, self, "polarization_phase_deg", "Phase Difference [deg,0=linear,+90=ell/right]",
                          tooltip="polarization_phase_deg", labelWidth=310, valueType=float, orientation="horizontal")
        gui.comboBox(self.ewp_box_8, self, "coherent_beam", label="Phase of the sigma field", labelWidth=310,
                     tooltip="coherent_beam",items=["Random (incoherent)", "Constant (coherent)"], orientation="horizontal")

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

        self.set_coordinates_visibility()

    def is_scanning_enabled(self):
        return True

    def set_coordinates_visibility(self):
        self.points_cartesian_box.setVisible(self.coordinates == 0)
        self.points_polar_box.setVisible(self.coordinates == 1)

    def get_lightsource(self):
        import scipy.constants as codata
        if self.units == 0:
            wavelength = codata.h * codata.c / codata.e / self.single_line_value
        else:
            wavelength = self.single_line_value * 1e-10

        if self.coordinates == 0:
            gs =  SourceGridCartesian(
                real_space_width = [self.real_space_width_x, 0.0, self.real_space_width_z],
                real_space_center=[self.real_space_center_x, 0.0, self.real_space_center_z],
                real_space_points=[self.real_space_points_x, 1, self.real_space_points_z],
                direction_space_width = [self.direction_space_width_x, self.direction_space_width_z],
                direction_space_center = [self.direction_space_center_x, self.direction_space_center_z],
                direction_space_points=[self.direction_space_points_x, self.direction_space_points_z],
                wavelength=wavelength,
                polarization_degree=self.polarization_degree,
                polarization_phase_deg=self.polarization_phase_deg,
                coherent_beam=self.coherent_beam,
                name = "Grid Source (Cartesian)")
        else:
            gs =  SourceGridPolar(
                real_space_width = [self.real_space_width_x, 0.0, self.real_space_width_z],
                real_space_center=[self.real_space_center_x, 0.0, self.real_space_center_z],
                real_space_points = [self.real_space_points_r, self.real_space_points_theta],
                direction_space_width = [self.direction_space_width_x, self.direction_space_width_z],
                direction_space_center=[self.direction_space_center_x, self.direction_space_center_z],
                direction_space_points = [self.direction_space_points_r, self.direction_space_points_theta],
                wavelength=wavelength,
                polarization_degree=self.polarization_degree,
                polarization_phase_deg=self.polarization_phase_deg,
                coherent_beam=self.coherent_beam,
                name = "Grid Source (Polar)")

        return gs

    def run_shadow4(self):
        try:
            set_verbose()
            self.shadow_output.setText("")
            sys.stdout = EmittingStream(textWritten=self._write_stdout)

            self._set_plot_quality()

            self.progressBarInit()

            light_source = self.get_lightsource()

            self.progressBarSet(5)

            # run shadow4

            output_beam = light_source.get_beam()

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
            # send beam and trigger
            #
            self.send("Shadow Data", ShadowData(beam=output_beam,
                                               number_of_rays=output_beam.get_number_of_rays(),
                                               beamline=S4Beamline(light_source=light_source)))
            self.send("Trigger", TriggerIn(new_object=True))
        except Exception as exception:
            try:    self._initialize_tabs()
            except: pass
            self.prompt_exception(exception)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWGrid()
    ow.show()
    a.exec_()
    ow.saveSettings()
