import sys
import time
import numpy

from PyQt5.QtGui import QPalette, QColor, QFont


from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement

from shadow4.beamline.s4_beamline import S4Beamline
from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
from shadow4.tools.logger import set_verbose

from syned.widget.widget_decorator import WidgetDecorator

from orangecontrib.shadow4.util.shadow4_util import TriggerToolsDecorator
from oasys.util.oasys_util import TriggerIn


class OWGeometrical(GenericElement, WidgetDecorator, TriggerToolsDecorator):

    name = "Geometrical Source"
    description = "Shadow Source: Geometrical Source"
    icon = "icons/geometrical.png"
    priority = 1

    inputs = []
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Shadow Data",
                "type":ShadowData,
                "doc":"",}]

    TriggerToolsDecorator.append_trigger_input_for_sources(inputs)
    TriggerToolsDecorator.append_trigger_output(outputs)

    number_of_rays = Setting(5000)
    seed = Setting(5676561)

    spatial_type = Setting(1)

    rect_width = Setting(0.1)
    rect_height = Setting(0.2)
    ell_semiaxis_x = Setting(0.1)
    ell_semiaxis_z = Setting(0.2)
    gauss_sigma_x = Setting(0.001)
    gauss_sigma_z = Setting(0.001)

    angular_distribution = Setting(0)

    horizontal_div_x_plus = Setting(5.0e-7)
    horizontal_div_x_minus = Setting(5.0e-7)
    vertical_div_z_plus = Setting(5.0e-6)
    vertical_div_z_minus = Setting(5.0e-6)

    angular_distribution_limits = Setting(0)

    horizontal_lim_x_plus = Setting(1.0e-5)
    horizontal_lim_x_minus = Setting(1.0e-5)
    vertical_lim_z_plus = Setting(1.0e-5)
    vertical_lim_z_minus = Setting(1.0e-5)
    horizontal_sigma_x = Setting(0.001)
    vertical_sigma_z = Setting(0.0001)

    cone_internal_half_aperture = Setting(0.001)
    cone_external_half_aperture = Setting(0.002)

    depth = Setting(0)

    source_depth_y = Setting(0.002)
    sigma_y = Setting(0.001)

    photon_energy_distribution = Setting(0)

    units=Setting(0)

    single_line_value = Setting(1000.0)
    single_line_value = Setting(1000.0)
    number_of_lines = Setting(0)

    line_value_1 = Setting(1000.0)
    line_value_2 = Setting(1010.0)
    line_value_3 = Setting(0.0)
    line_value_4 = Setting(0.0)
    line_value_5 = Setting(0.0)
    line_value_6 = Setting(0.0)
    line_value_7 = Setting(0.0)
    line_value_8 = Setting(0.0)
    line_value_9 = Setting(0.0)
    line_value_10 = Setting(0.0)

    uniform_minimum = Setting(1000.0)
    uniform_maximum = Setting(1010.0)

    line_int_1 = Setting(0.0)
    line_int_2 = Setting(0.0)
    line_int_3 = Setting(0.0)
    line_int_4 = Setting(0.0)
    line_int_5 = Setting(0.0)
    line_int_6 = Setting(0.0)
    line_int_7 = Setting(0.0)
    line_int_8 = Setting(0.0)
    line_int_9 = Setting(0.0)
    line_int_10 = Setting(0.0)

    gaussian_central_value = Setting(0.0)
    gaussian_sigma = Setting(0.0)
    gaussian_minimum = Setting(0.0)
    gaussian_maximum = Setting(0.0)

    user_defined_file = Setting("energy_spectrum.dat")
    user_defined_minimum = Setting(0.0)
    user_defined_maximum = Setting(0.0)
    user_defined_spectrum_binning = Setting(10000)
    user_defined_refining_factor  = Setting(5)

    # polarization = Setting(1)
    coherent_beam = Setting(0)
    phase_diff = Setting(0.0)
    polarization_degree = Setting(1.0)

    optimize_source=Setting(0)
    optimize_file_name = Setting("NONESPECIFIED")
    max_number_of_rejected_rays = Setting(10000000)


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
        # MONTECARLO

        left_box_1 = oasysgui.widgetBox(tab_basic, "Montecarlo", addSpace=True, orientation="vertical", height=100)

        gui.separator(left_box_1)

        self.sample_box_1 = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.sample_box_1, self, "number_of_rays", "Number of Random Rays", labelWidth=260,
                          valueType=int, orientation="horizontal", tooltip="number_of_rays")
        oasysgui.lineEdit(self.sample_box_1, self, "seed", "Seed (0=clock)", labelWidth=260, valueType=int,
                          orientation="horizontal", tooltip="seed")

        ##############################
        # GEOMETRY

        left_box_2 = oasysgui.widgetBox(tab_geometry, "", addSpace=True, orientation="vertical", height=550)

        gui.separator(left_box_2)

        ######

        spatial_type_box = oasysgui.widgetBox(left_box_2, "Spatial Type", addSpace=True, orientation="vertical",
                                              height=120)

        items = SourceGeometrical.spatial_type_list() # ["Point", "Rectangle", "Ellipse", "Gaussian"]
        gui.comboBox(spatial_type_box, self, "spatial_type", label="Spatial Type", labelWidth=355,
                     items=items, orientation="horizontal",
                     callback=self.set_SpatialType, tooltip="spatial_type")

        gui.separator(spatial_type_box)

        self.spatial_type_box_1 = oasysgui.widgetBox(spatial_type_box, "", addSpace=False, orientation="vertical")

        self.le_rect_width = oasysgui.lineEdit(self.spatial_type_box_1, self, "rect_width", "Width X [m]", labelWidth=260,
                                               valueType=float, orientation="horizontal",
                                                  tooltip="rect_width")
        self.le_rect_height = oasysgui.lineEdit(self.spatial_type_box_1, self, "rect_height", "Height Z [m]", labelWidth=260,
                                                valueType=float, orientation="horizontal",
                                                  tooltip="rect_height")

        self.spatial_type_box_2 = oasysgui.widgetBox(spatial_type_box, "", addSpace=False, orientation="vertical")

        self.le_ell_semiaxis_x = oasysgui.lineEdit(self.spatial_type_box_2, self, "ell_semiaxis_x", "Semi-Axis X [m]",
                                                   labelWidth=260, valueType=float, orientation="horizontal",
                                                  tooltip="ell_semiaxis_x")
        self.le_ell_semiaxis_z = oasysgui.lineEdit(self.spatial_type_box_2, self, "ell_semiaxis_z", "Semi-Axis Z [m]",
                                                   labelWidth=260, valueType=float, orientation="horizontal",
                                                  tooltip="ell_semiaxis_z")

        self.spatial_type_box_3 = oasysgui.widgetBox(spatial_type_box, "", addSpace=False, orientation="vertical")

        self.le_gauss_sigma_x = oasysgui.lineEdit(self.spatial_type_box_3, self, "gauss_sigma_x", "Sigma X [m]",
                                                  labelWidth=260, valueType=float, orientation="horizontal",
                                                  tooltip="gauss_sigma_x")
        self.le_gauss_sigma_z = oasysgui.lineEdit(self.spatial_type_box_3, self, "gauss_sigma_z", "Sigma Z [m]",
                                                  labelWidth=260, valueType=float, orientation="horizontal",
                                                  tooltip="gauss_sigma_z")

        self.set_SpatialType()

        angular_distribution_box = oasysgui.widgetBox(left_box_2, "Angular Distribution", addSpace=True,
                                                      orientation="vertical", height=260)

        items = SourceGeometrical.angular_distribution_list() # ["Flat", "Uniform", "Gaussian", "Cone","Collimated"]
        gui.comboBox(angular_distribution_box, self, "angular_distribution", label="Angular Distribution",
                     labelWidth=355, items=items, orientation="horizontal", callback=self.set_AngularDistribution,
                     tooltip="angular_distribution")

        gui.separator(angular_distribution_box)

        self.angular_distribution_box_1 = oasysgui.widgetBox(angular_distribution_box, "", addSpace=False,
                                                             orientation="vertical")

        oasysgui.lineEdit(self.angular_distribution_box_1, self, "horizontal_div_x_plus",
                          "Horizontal Divergence X(+) [rad]", labelWidth=260, valueType=float, orientation="horizontal",
                          tooltip="horizontal_div_x_plus")
        oasysgui.lineEdit(self.angular_distribution_box_1, self, "horizontal_div_x_minus",
                          "Horizontal Divergence X(-) [rad]", labelWidth=260, valueType=float, orientation="horizontal",
                          tooltip="horizontal_div_x_minus")
        oasysgui.lineEdit(self.angular_distribution_box_1, self, "vertical_div_z_plus",
                          "Vertical Divergence Z(+) [rad]", labelWidth=260, valueType=float, orientation="horizontal",
                          tooltip="vertical_div_z_plus")
        oasysgui.lineEdit(self.angular_distribution_box_1, self, "vertical_div_z_minus",
                          "Vertical Divergence Z(-) [rad]", labelWidth=260, valueType=float, orientation="horizontal",
                          tooltip="vertical_div_z_minus")

        self.angular_distribution_box_2 = oasysgui.widgetBox(angular_distribution_box, "", addSpace=False,
                                                             orientation="vertical")

        if False: # No Gaussian limits for the moment (code kept just in case we want that in the future)
            gui.comboBox(self.angular_distribution_box_2, self, "angular_distribution_limits",
                         label="Angular Distribution Limits", labelWidth=355,
                         items=["No Limits", "Horizontal", "Vertical", "Both"], orientation="horizontal",
                         callback=self.set_AngularDistributionLimits)

            self.le_horizontal_lim_x_plus = oasysgui.lineEdit(self.angular_distribution_box_2, self,
                                                              "horizontal_lim_x_plus", "Horizontal Limit X(+) [rad]",
                                                              labelWidth=260, valueType=float, orientation="horizontal",
                                                              tooltip="horizontal_lim_x_plus")
            self.le_horizontal_lim_x_minus = oasysgui.lineEdit(self.angular_distribution_box_2, self,
                                                               "horizontal_lim_x_minus", "Horizontal Limit X(-) [rad]",
                                                               labelWidth=260, valueType=float, orientation="horizontal",
                                                               tooltip="horizontal_lim_x_minus")
            self.le_vertical_lim_z_plus = oasysgui.lineEdit(self.angular_distribution_box_2, self, "vertical_lim_z_plus",
                                                            "Vertical Limit Z(+) [rad]", labelWidth=260, valueType=float,
                                                            orientation="horizontal", tooltip="vertical_lim_z_plus")
            self.le_vertical_lim_z_minus = oasysgui.lineEdit(self.angular_distribution_box_2, self, "vertical_lim_z_minus",
                                                             "Vertical Limit Z(-) [rad]", labelWidth=260, valueType=float,
                                                             orientation="horizontal", tooltip="vertical_lim_z_minus")

        oasysgui.lineEdit(self.angular_distribution_box_2, self, "horizontal_sigma_x", "Horizontal Sigma (X) [rad]",
                          labelWidth=260, valueType=float, orientation="horizontal", tooltip="horizontal_sigma_x")
        oasysgui.lineEdit(self.angular_distribution_box_2, self, "vertical_sigma_z", "Vertical Sigma (Z) [rad]",
                          labelWidth=260, valueType=float, orientation="horizontal", tooltip="vertical_sigma_z")

        self.angular_distribution_box_3 = oasysgui.widgetBox(angular_distribution_box, "", addSpace=False,
                                                             orientation="vertical")

        oasysgui.lineEdit(self.angular_distribution_box_3, self, "cone_internal_half_aperture",
                          "Cone Internal Half-Aperture [rad]", labelWidth=260, valueType=float,
                          orientation="horizontal", tooltip="cone_internal_half_aperture")
        oasysgui.lineEdit(self.angular_distribution_box_3, self, "cone_external_half_aperture",
                          "Cone External Half-Aperture [rad]", labelWidth=260, valueType=float,
                          orientation="horizontal", tooltip="cone_external_half_aperture")

        self.set_AngularDistribution()

        depth_box = oasysgui.widgetBox(left_box_2, "Depth", addSpace=True, orientation="vertical", height=100)

        gui.comboBox(depth_box, self, "depth", label="Depth", labelWidth=355,
                     items=["Off", "Uniform", "Gaussian"], orientation="horizontal", callback=self.set_Depth,
                     tooltip="depth")

        gui.separator(depth_box, 1)

        self.depth_box_1 = oasysgui.widgetBox(depth_box, "", addSpace=False, orientation="vertical")

        self.le_source_depth_y = oasysgui.lineEdit(self.depth_box_1, self, "source_depth_y", "Source Depth (Y) [m]",
                                                   labelWidth=260, valueType=float, orientation="horizontal",
                                                   tooltip="source_depth_y")

        self.depth_box_2 = oasysgui.widgetBox(depth_box, "", addSpace=False, orientation="vertical")

        self.le_sigma_y = oasysgui.lineEdit(self.depth_box_2, self, "sigma_y", "Sigma Y [m]", labelWidth=260,
                                            valueType=float, orientation="horizontal", tooltip="sigma_y")

        self.set_Depth()

        ##############################
        # ENERGY

        left_box_3 = oasysgui.widgetBox(tab_energy, "", addSpace=False, orientation="vertical", height=640)

        ######

        energy_wavelength_box = oasysgui.widgetBox(left_box_3, "Energy/Wavelength", addSpace=False,
                                                   orientation="vertical", height=430)

        items = SourceGeometrical.energy_distribution_list() # ["Single Line", "Several Lines", "Uniform", "Relative Intensities", "Gaussian", "User Defined"]

        gui.comboBox(energy_wavelength_box, self, "photon_energy_distribution", label="Photon Energy Distribution",
                     labelWidth=260, items=items, orientation="horizontal", callback=self.set_PhotonEnergyDistribution,
                     tooltip="photon_energy_distribution")

        gui.comboBox(energy_wavelength_box, self, "units", label="Units", labelWidth=260,
                     items=["Energy/eV", "Wavelength/Å"], orientation="horizontal",
                     callback=self.set_PhotonEnergyDistribution, tooltip="units")

        self.ewp_box_5 = oasysgui.widgetBox(energy_wavelength_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.ewp_box_5, self, "number_of_lines", label="Number of Lines", labelWidth=330,
                     items=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], orientation="horizontal",
                     callback=self.set_NumberOfLines, tooltip="number_of_lines")

        container = oasysgui.widgetBox(energy_wavelength_box, "", addSpace=False, orientation="horizontal")
        self.container_left = oasysgui.widgetBox(container, "", addSpace=False, orientation="vertical")
        self.container_right = oasysgui.widgetBox(container, "", addSpace=False, orientation="vertical")

        self.ewp_box_1 = oasysgui.widgetBox(self.container_left, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.ewp_box_1, self, "single_line_value", "Value", labelWidth=260, valueType=float,
                          orientation="horizontal", tooltip="single_line_value")

        self.ewp_box_2 = oasysgui.widgetBox(self.container_left, "Values", addSpace=False, orientation="vertical")

        self.le_line_value_1 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_1", "Line 1", valueType=float,
                                                 orientation="horizontal", tooltip="line_value_1")
        self.le_line_value_2 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_2", "Line 2", valueType=float,
                                                 orientation="horizontal", tooltip="line_value_2")
        self.le_line_value_3 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_3", "Line 3", valueType=float,
                                                 orientation="horizontal", tooltip="line_value_3")
        self.le_line_value_4 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_4", "Line 4", valueType=float,
                                                 orientation="horizontal", tooltip="line_value_4")
        self.le_line_value_5 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_5", "Line 5", valueType=float,
                                                 orientation="horizontal", tooltip="line_value_5")
        self.le_line_value_6 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_6", "Line 6", valueType=float,
                                                 orientation="horizontal", tooltip="line_value_6")
        self.le_line_value_7 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_7", "Line 7", valueType=float,
                                                 orientation="horizontal", tooltip="line_value_7")
        self.le_line_value_8 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_8", "Line 8", valueType=float,
                                                 orientation="horizontal", tooltip="line_value_8")
        self.le_line_value_9 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_9", "Line 9", valueType=float,
                                                 orientation="horizontal", tooltip="line_value_9")
        self.le_line_value_10 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_10", "Line 10", valueType=float,
                                                  orientation="horizontal", tooltip="line_value_10")

        self.ewp_box_3 = oasysgui.widgetBox(self.container_left, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.ewp_box_3, self, "uniform_minimum", "Minimum Energy/Wavelength", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="uniform_minimum")
        oasysgui.lineEdit(self.ewp_box_3, self, "uniform_maximum", "Maximum Energy/Wavelength", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="uniform_maximum")

        self.ewp_box_4 = oasysgui.widgetBox(self.container_right, "Relative Intensities", addSpace=False,
                                            orientation="vertical", tooltip="Relative Intensities")

        self.le_line_int_1 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_1", "Int 1", labelWidth=100,
                                               valueType=float, orientation="horizontal", tooltip="line_int_1")
        self.le_line_int_2 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_2", "Int 2", labelWidth=100,
                                               valueType=float, orientation="horizontal", tooltip="line_int_2")
        self.le_line_int_3 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_3", "Int 3", labelWidth=100,
                                               valueType=float, orientation="horizontal", tooltip="line_int_3")
        self.le_line_int_4 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_4", "Int 4", labelWidth=100,
                                               valueType=float, orientation="horizontal", tooltip="line_int_4")
        self.le_line_int_5 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_5", "Int 5", labelWidth=100,
                                               valueType=float, orientation="horizontal", tooltip="line_int_5")
        self.le_line_int_6 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_6", "Int 6", labelWidth=100,
                                               valueType=float, orientation="horizontal", tooltip="line_int_6")
        self.le_line_int_7 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_7", "Int 7", labelWidth=100,
                                               valueType=float, orientation="horizontal", tooltip="line_int_7")
        self.le_line_int_8 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_8", "Int 8", labelWidth=100,
                                               valueType=float, orientation="horizontal", tooltip="line_int_8")
        self.le_line_int_9 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_9", "Int 9", labelWidth=100,
                                               valueType=float, orientation="horizontal", tooltip="line_int_9")
        self.le_line_int_10 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_10", "Int 10", labelWidth=100,
                                                valueType=float, orientation="horizontal", tooltip="line_int_10")

        self.ewp_box_6 = oasysgui.widgetBox(energy_wavelength_box, "Gaussian", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.ewp_box_6, self, "gaussian_central_value", "Central Value", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="gaussian_central_value")
        oasysgui.lineEdit(self.ewp_box_6, self, "gaussian_sigma", "Sigma", labelWidth=260, valueType=float,
                          orientation="horizontal", tooltip="gaussian_sigma")

        if False: # not yet implemented... Is that useful?
            gui.separator(self.ewp_box_6)

            oasysgui.lineEdit(self.ewp_box_6, self, "gaussian_minimum", "Minimum Energy/Wavelength", labelWidth=260,
                              valueType=float, orientation="horizontal", tooltip="gaussian_minimum")
            oasysgui.lineEdit(self.ewp_box_6, self, "gaussian_maximum", "Maximum Energy/Wavelength", labelWidth=260,
                              valueType=float, orientation="horizontal", tooltip="gaussian_maximum")

        self.ewp_box_7 = oasysgui.widgetBox(energy_wavelength_box, "User Defined", addSpace=False,
                                            orientation="vertical")

        file_box = oasysgui.widgetBox(self.ewp_box_7, "", addSpace=True, orientation="horizontal", height=25)

        self.le_user_defined_file = oasysgui.lineEdit(file_box, self, "user_defined_file", "Spectrum File",
                                                      labelWidth=100, valueType=str, orientation="horizontal",
                                                      tooltip="user_defined_file")

        gui.button(file_box, self, "...", callback=self.selectFile)

        if False: # why this?
            gui.separator(self.ewp_box_7)

            oasysgui.lineEdit(self.ewp_box_7, self, "user_defined_minimum", "Minimum Energy/Wavelength", labelWidth=260,
                              valueType=float, orientation="horizontal", tooltip="user_defined_minimum")
            oasysgui.lineEdit(self.ewp_box_7, self, "user_defined_maximum", "Maximum Energy/Wavelength", labelWidth=260,
                              valueType=float, orientation="horizontal", tooltip="user_defined_maximum")
            oasysgui.lineEdit(self.ewp_box_7, self, "user_defined_spectrum_binning",
                              "Minimum Nr. of Bins of Input Spectrum", labelWidth=260, valueType=int,
                              orientation="horizontal", tooltip="user_defined_spectrum_binning")
            oasysgui.lineEdit(self.ewp_box_7, self, "user_defined_refining_factor", "Refining Factor", labelWidth=260,
                              valueType=int, orientation="horizontal", tooltip="user_defined_refining_factor")

        self.set_PhotonEnergyDistribution()

        polarization_box = oasysgui.widgetBox(left_box_3, "Polarization", addSpace=False, orientation="vertical")

        # gui.comboBox(polarization_box, self, "polarization", label="Polarization", labelWidth=310,
        #              items=["No", "Yes"], orientation="horizontal", callback=self.set_Polarization)

        self.ewp_box_8 = oasysgui.widgetBox(polarization_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.ewp_box_8, self, "polarization_degree", "Polarization Degree [cos_s/(cos_s+sin_s)]",
                          tooltip="polarization_degree", labelWidth=310, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ewp_box_8, self, "phase_diff", "Phase Difference [deg,0=linear,+90=ell/right]",
                          tooltip="phase_diff",labelWidth=310, valueType=float, orientation="horizontal")
        gui.comboBox(self.ewp_box_8, self, "coherent_beam", label="Phase of the sigma field", labelWidth=310,
                     tooltip="coherent_beam",
                     items=["Random (incoherent)", "Constant (coherent)"], orientation="horizontal")
        self.ewp_box_8.setVisible(True)

        # self.set_Polarization()

        ##############################

        if False: # TODO implement
            left_box_4 = oasysgui.widgetBox(tab_basic, "Reject Rays", addSpace=True, orientation="vertical", height=130)

            gui.comboBox(left_box_4, self, "optimize_source", label="Optimize Source",
                         items=["No", "Using file with phase/space volume)", "Using file with slit/acceptance"],
                         tooltip="optimize_source",
                         labelWidth=120, callback=self.set_OptimizeSource, orientation="horizontal")
            self.optimize_file_name_box = oasysgui.widgetBox(left_box_4, "", addSpace=False, orientation="vertical")

            file_box = oasysgui.widgetBox(self.optimize_file_name_box, "", addSpace=True, orientation="horizontal",
                                          height=25)

            self.le_optimize_file_name = oasysgui.lineEdit(file_box, self, "optimize_file_name", "File Name",
                                                           tooltip="optimize_file_name",
                                                           labelWidth=100, valueType=str, orientation="horizontal")

            gui.button(file_box, self, "...", callback=self.selectOptimizeFile)

            oasysgui.lineEdit(self.optimize_file_name_box, self, "max_number_of_rejected_rays",
                              "Max number of rejected rays (set 0 for infinity)",
                              tooltip="max_number_of_rejected_rays", labelWidth=280, valueType=int,
                              orientation="horizontal")

            self.set_OptimizeSource()


        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def is_scanning_enabled(self):
        return True

    def call_reset_settings(self):
        super().call_reset_settings()

        self.set_Sampling()
        self.set_SpatialType()
        self.set_AngularDistribution()
        self.set_Depth()
        self.set_PhotonEnergyDistribution()
        # self.set_Polarization()

    def set_OptimizeSource(self):
        self.optimize_file_name_box.setVisible(self.optimize_source != 0)

    def set_SpatialType(self):
        self.spatial_type_box_1.setVisible(self.spatial_type == 1)
        self.spatial_type_box_2.setVisible(self.spatial_type == 2)
        self.spatial_type_box_3.setVisible(self.spatial_type == 3)

    def set_AngularDistributionLimits(self):
        if False:
            self.le_horizontal_lim_x_plus.setEnabled(self.angular_distribution_limits != 0 and self.angular_distribution_limits != 2)
            self.le_horizontal_lim_x_minus.setEnabled(self.angular_distribution_limits != 0 and self.angular_distribution_limits != 2)
            self.le_vertical_lim_z_plus.setEnabled(self.angular_distribution_limits != 0 and self.angular_distribution_limits != 1)
            self.le_vertical_lim_z_minus.setEnabled(self.angular_distribution_limits != 0 and self.angular_distribution_limits != 1)

    def set_AngularDistribution(self):
        self.angular_distribution_box_1.setVisible(self.angular_distribution == 0 or self.angular_distribution == 1)
        self.angular_distribution_box_2.setVisible(self.angular_distribution == 2)
        self.angular_distribution_box_3.setVisible(self.angular_distribution == 3)

        if self.angular_distribution == 2:
            self.set_AngularDistributionLimits()

    def set_Depth(self):
        self.depth_box_1.setVisible(self.depth == 1)
        self.depth_box_2.setVisible(self.depth == 2)

    def set_PhotonEnergyDistribution(self):
        self.ewp_box_1.setVisible(self.photon_energy_distribution == 0)
        self.ewp_box_2.setVisible(self.photon_energy_distribution == 1 or self.photon_energy_distribution == 3)
        self.ewp_box_3.setVisible(self.photon_energy_distribution == 2)
        self.ewp_box_4.setVisible(self.photon_energy_distribution == 3)
        self.ewp_box_5.setVisible(self.photon_energy_distribution == 1 or self.photon_energy_distribution == 3)
        self.ewp_box_6.setVisible(self.photon_energy_distribution == 4)
        self.ewp_box_7.setVisible(self.photon_energy_distribution == 5)

        if self.photon_energy_distribution == 3:
            self.le_line_value_1.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_2.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_3.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_4.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_5.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_6.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_7.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_8.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_9.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_10.parentWidget().children()[1].setFixedWidth(100)
        else:
            self.le_line_value_1.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_2.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_3.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_4.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_5.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_6.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_7.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_8.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_9.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_10.parentWidget().children()[1].setFixedWidth(260)

        self.container_right.setVisible(self.photon_energy_distribution == 3)

        self.set_NumberOfLines()

    def set_NumberOfLines(self):
        self.le_line_value_2.parentWidget().setVisible(self.number_of_lines >= 1)
        self.le_line_int_2.parentWidget().setVisible(self.number_of_lines >= 1)
        self.le_line_value_3.parentWidget().setVisible(self.number_of_lines >= 2)
        self.le_line_int_3.parentWidget().setVisible(self.number_of_lines >= 2)
        self.le_line_value_4.parentWidget().setVisible(self.number_of_lines >= 3)
        self.le_line_int_4.parentWidget().setVisible(self.number_of_lines >= 3)
        self.le_line_value_5.parentWidget().setVisible(self.number_of_lines >= 4)
        self.le_line_int_5.parentWidget().setVisible(self.number_of_lines >= 4)
        self.le_line_value_6.parentWidget().setVisible(self.number_of_lines >= 5)
        self.le_line_int_6.parentWidget().setVisible(self.number_of_lines >= 5)
        self.le_line_value_7.parentWidget().setVisible(self.number_of_lines >= 6)
        self.le_line_int_7.parentWidget().setVisible(self.number_of_lines >= 6)
        self.le_line_value_8.parentWidget().setVisible(self.number_of_lines >= 7)
        self.le_line_int_8.parentWidget().setVisible(self.number_of_lines >= 7)
        self.le_line_value_9.parentWidget().setVisible(self.number_of_lines >= 8)
        self.le_line_int_9.parentWidget().setVisible(self.number_of_lines >= 8)
        self.le_line_value_10.parentWidget().setVisible(self.number_of_lines == 9)
        self.le_line_int_10.parentWidget().setVisible(self.number_of_lines == 9)

    # def set_Polarization(self):
    #     self.ewp_box_8.setVisible(self.polarization==1)

    def selectFile(self):
        self.le_user_defined_file.setText(oasysgui.selectFileFromDialog(self, self.user_defined_file, "Open Spectrum File", file_extension_filter="Data Files (*.dat *.txt)"))

    def selectOptimizeFile(self):
        self.le_optimize_file_name.setText(oasysgui.selectFileFromDialog(self, self.optimize_file_name, "Open Optimize Source Parameters File"))


    def checkFields(self):
        # TODO: complete?
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
        self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
        self.delta_e = congruence.checkPositiveNumber(self.delta_e, "Delta Energy")
        self.undulator_length = congruence.checkPositiveNumber(self.undulator_length, "Undulator Length")


    def get_lightsource(self):

        try:    name = self.getNode().title
        except: name = "Geometrcal Source"

        gs = SourceGeometrical(name=name, nrays=self.number_of_rays, seed=self.seed)

        if self.spatial_type == 0: # point
            gs.set_spatial_type_point()
        elif self.spatial_type == 1: # rectangle
            gs.set_spatial_type_rectangle(width=self.rect_width,
                                          height=self.rect_height,
                                          )
        elif self.spatial_type == 2: # ellipse
            gs.set_spatial_type_ellipse(width=2*self.ell_semiaxis_x,
                                        height=2*self.ell_semiaxis_z,
                                        )
        elif self.spatial_type == 3: # Gaussian
            gs.set_spatial_type_gaussian(sigma_h=self.gauss_sigma_x,
                                         sigma_v=self.gauss_sigma_z,
                                         )

        if self.depth == 0:
            gs.set_depth_distribution_off()
        elif self.depth == 1:
            gs.set_depth_distribution_uniform(self.source_depth_y)
        elif self.depth == 2:
            gs.set_depth_distribution_gaussian(self.sigma_y)


        if self.angular_distribution == 0: # flat
            gs.set_angular_distribution_flat(hdiv1=-self.horizontal_div_x_minus,
                                             hdiv2=self.horizontal_div_x_plus,
                                             vdiv1=-self.vertical_div_z_minus,
                                             vdiv2=self.vertical_div_z_plus,
                                               )
        elif self.angular_distribution == 1: # Uniform
            gs.set_angular_distribution_uniform(hdiv1=-self.horizontal_div_x_minus,
                                                hdiv2=self.horizontal_div_x_plus,
                                                vdiv1=-self.vertical_div_z_minus,
                                                vdiv2=self.vertical_div_z_plus,
                                               )
        elif self.angular_distribution == 2:  # Gaussian
            gs.set_angular_distribution_gaussian(sigdix=self.horizontal_sigma_x,
                                                 sigdiz=self.vertical_sigma_z,
                                                 )
        elif self.angular_distribution == 3:  # cone
            gs.set_angular_distribution_cone(cone_max=self.cone_external_half_aperture,
                                             cone_min=self.cone_internal_half_aperture,
                                             )

        elif self.angular_distribution == 4:  # Zero (collimated) - New in shadow4
            gs.set_angular_distribution_collimated()


        # photon energy
        values = [self.line_value_1,
                  self.line_value_2,
                  self.line_value_3,
                  self.line_value_4,
                  self.line_value_5,
                  self.line_value_6,
                  self.line_value_7,
                  self.line_value_8,
                  self.line_value_9,
                  self.line_value_10,
                  ]

        weights = [self.line_int_1,
                  self.line_int_2,
                  self.line_int_3,
                  self.line_int_4,
                  self.line_int_5,
                  self.line_int_6,
                  self.line_int_7,
                  self.line_int_8,
                  self.line_int_9,
                  self.line_int_10,
                  ]

        values = values[0:(self.number_of_lines+1)]
        weights = weights[0:(self.number_of_lines+1)]
        unit = ['eV','A'][self.units]

        if self.photon_energy_distribution == 0: # "Single line":
            gs.set_energy_distribution_singleline(self.single_line_value, unit=unit)
        elif self.photon_energy_distribution == 1: #"Several lines":
            gs.set_energy_distribution_severallines(values=values, unit=unit)
        elif self.photon_energy_distribution == 2: # "Uniform":
            gs.set_energy_distribution_uniform(value_min=self.uniform_minimum,value_max=self.uniform_maximum,unit=unit)
        elif self.photon_energy_distribution == 3: # "Relative intensities":
            gs.set_energy_distribution_relativeintensities(values=values,weights=weights,unit=unit)
        elif self.photon_energy_distribution == 4: # "Gaussian":
            gs.set_energy_distribution_gaussian(center=self.gaussian_central_value,sigma=self.gaussian_sigma,unit=unit)
        elif self.photon_energy_distribution == 5: # "User defined":
            a = numpy.loadtxt(self.user_defined_file)
            gs.set_energy_distribution_userdefined(a[:,0],a[:,1],unit=unit)


        # polarization / coherence
        gs.set_polarization(polarization_degree=self.polarization_degree,
                            phase_diff=numpy.radians(self.phase_diff),
                            coherent_beam=self.coherent_beam)

        return gs

    def run_shadow4(self):
        try:
            set_verbose()
            self.shadow_output.setText("")
            sys.stdout = EmittingStream(textWritten=self._write_stdout)

            self._set_plot_quality()

            self.progressBarInit()

            light_source = self.get_lightsource()

            # script
            script = light_source.to_python_code()
            script += "\n\n# test plot\nfrom srxraylib.plot.gol import plot_scatter"
            script += "\nrays = beam.get_rays()"
            script += "\nplot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 2], title='(X,Z) in microns')"
            self.shadow4_script.set_code(script)


            print(light_source.info())

            print(light_source.get_info())

            self.progressBarSet(5)

            # run shadow4
            t00 = time.time()
            # beam = light_source.get_beam(NRAYS=self.number_of_rays, SEED=self.seed)
            output_beam = light_source.get_beam()
            t11 = time.time() - t00
            print("***** time for %d rays: %f s, %f min, " % (self.number_of_rays, t11, t11 / 60))

            #
            # beam plots
            #
            self._plot_results(output_beam, None, progressBarValue=80)



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

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWGeometrical()
    ow.show()
    a.exec_()
    ow.saveSettings()
