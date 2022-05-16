import numpy
import sys
import time

from orangewidget import gui
from orangewidget import widget
from PyQt5.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream, TTYGrabber
from oasys.util.oasys_util import EmittingStream


from orangecontrib.shadow4.widgets.gui.ow_electron_beam import OWElectronBeam
from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
from orangecontrib.shadow4.util.shadow_objects import ShadowBeam



from syned.beamline.beamline import Beamline
from syned.storage_ring.magnetic_structures.undulator import Undulator
from syned.widget.widget_decorator import WidgetDecorator

from shadow4.sources.undulator.s4_undulator import S4Undulator
from shadow4.sources.undulator.s4_undulator_light_source import S4UndulatorLightSource

from shadow4.syned.element_coordinates import ElementCoordinates



class OWMirror(GenericElement, WidgetDecorator):

    name = "Generic mirror"
    description = "Shadow Mirror"
    icon = "icons/mirror.png"
    priority = 5

    inputs = []
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Beam4",
                "type":ShadowBeam,
                "doc":"",}]

    # xxx=Setting(4.0)
    # energy=Setting(15000.0)
    # delta_e=Setting(1500.0)
    # number_of_rays=Setting(5000)
    # seed=Setting(5676561)

    #########################################################
    # Position
    #########################################################
    source_plane_distance               = Setting(1.0)
    image_plane_distance                = Setting(0.0)
    angles_respect_to                   = Setting(0)
    incidence_angle_deg                 = Setting(88.8)
    incidence_angle_mrad                = Setting(0.0)
    reflection_angle_deg                = Setting(85.0)
    reflection_angle_mrad               = Setting(0.0)
    mirror_orientation_angle            = Setting(1)
    mirror_orientation_angle_user_value = Setting(0.0)

    #########################################################
    # surface shape
    #########################################################
    surface_shape_type = Setting(0)
    surface_shape_parameters                = Setting(0)
    focii_and_continuation_plane            = Setting(0)
    object_side_focal_distance              = Setting(0.0)
    image_side_focal_distance               = Setting(0.0)
    incidence_angle_respect_to_normal_type  = Setting(0)
    incidence_angle_respect_to_normal       = Setting(0.0)
    focus_location                          = Setting(0)
    toroidal_mirror_pole_location           = Setting(0)

    spherical_radius                     = Setting(1.0)
    torus_major_radius                   = Setting(1.0)
    torus_minor_radius                   = Setting(1.0)
    ellipse_hyperbola_semi_major_axis    = Setting(1.0)
    ellipse_hyperbola_semi_minor_axis    = Setting(1.0)
    angle_of_majax_and_pole              = Setting(1.0)
    paraboloid_parameter                 = Setting(1.0)

    surface_curvature    = Setting(0)
    is_cylinder          = Setting(1)
    cylinder_orientation = Setting(0)

    reflectivity_type             = Setting(0)
    file_prerefl                  = Setting("<none>")
    reflectivity_compound_name    = Setting("Rh")
    reflectivity_compound_density = Setting(12.41)

    INNER_BOX_WIDTH_L3=322
    INNER_BOX_WIDTH_L2=335
    INNER_BOX_WIDTH_L1=358
    INNER_BOX_WIDTH_L0=375


    def __init__(self):
        super().__init__()

        #
        # main buttons
        #
        self.runaction = widget.OWAction("Run Shadow4/Trace", self)
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

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        #
        # tabs
        #
        self.tabs_control_area = oasysgui.tabWidget(self.controlArea)
        self.tabs_control_area.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_control_area.setFixedWidth(self.CONTROL_AREA_WIDTH-5)



        tab_position = oasysgui.createTabPage(self.tabs_control_area, "Position")

        tab_basic_settings = oasysgui.createTabPage(self.tabs_control_area, "Basic Settings")
        tabs_basic_setting = oasysgui.tabWidget(tab_basic_settings)
        subtab_surface_shape = oasysgui.createTabPage(tabs_basic_setting, "Surface Shape")
        subtab_reflectivity = oasysgui.createTabPage(tabs_basic_setting, "Reflectivity")
        subtab_dimensions = oasysgui.createTabPage(tabs_basic_setting, "Dimensions")

        tab_advanced_settings = oasysgui.createTabPage(self.tabs_control_area, "Advanced Settings")
        tabs_advanced_settings = oasysgui.tabWidget(tab_advanced_settings)
        subtab_modified_surface = oasysgui.createTabPage(tabs_advanced_settings, "Modified Surface")
        subtab_oe_movement= oasysgui.createTabPage(tabs_advanced_settings, "O.E. Movement")
        # subtab_source_movement = oasysgui.createTabPage(tabs_advanced_settings, "Source Movement")
        # subtab_output_files = oasysgui.createTabPage(tabs_advanced_settings, "Output Files")

        #
        # widgets
        #

        #########################################################
        # Position
        #########################################################
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(self.orientation_box, self, "angles_respect_to", label="Angles in [deg] with respect to the",
                     labelWidth=250,
                     items=["Normal", "Surface"],
                     callback=self.set_angles_respect_to,
                     sendSelectedValue=False, orientation="horizontal")

        self.incidence_angle_deg_le = oasysgui.lineEdit(self.orientation_box, self, "incidence_angle_deg",
                                                        "Incident Angle\nwith respect to the Normal [deg]",
                                                        labelWidth=220, callback=self.calculate_incidence_angle_mrad,
                                                        valueType=float, orientation="horizontal")
        self.incidence_angle_rad_le = oasysgui.lineEdit(self.orientation_box, self, "incidence_angle_mrad",
                                                        "Incident Angle\nwith respect to the surface [mrad]",
                                                        labelWidth=220, callback=self.calculate_incidence_angle_deg,
                                                        valueType=float, orientation="horizontal")
        self.reflection_angle_deg_le = oasysgui.lineEdit(self.orientation_box, self, "reflection_angle_deg",
                                                         "Reflection Angle\nwith respect to the Normal [deg]",
                                                         labelWidth=220, callback=self.calculate_reflection_angle_mrad,
                                                         valueType=float, orientation="horizontal")
        self.reflection_angle_rad_le = oasysgui.lineEdit(self.orientation_box, self, "reflection_angle_mrad",
                                                         "Reflection Angle\nwith respect to the surface [mrad]",
                                                         labelWidth=220, callback=self.calculate_reflection_angle_deg,
                                                         valueType=float, orientation="horizontal")

        self.set_angles_respect_to()

        self.calculate_incidence_angle_mrad()
        self.calculate_reflection_angle_mrad()

        if True: # self.graphical_options.is_mirror:
            self.reflection_angle_deg_le.setEnabled(False)
            self.reflection_angle_rad_le.setEnabled(False)

        gui.comboBox(self.orientation_box, self, "mirror_orientation_angle", label="O.E. Orientation Angle [deg]",
                     labelWidth=390,
                     items=[0, 90, 180, 270, "Other value..."],
                     valueType=float,
                     sendSelectedValue=False, orientation="horizontal", callback=self.mirror_orientation_angle_user, )
        self.mirror_orientation_angle_user_value_le = oasysgui.widgetBox(self.orientation_box, "", addSpace=False,
                                                                         orientation="vertical")
        oasysgui.lineEdit(self.mirror_orientation_angle_user_value_le, self, "mirror_orientation_angle_user_value",
                          "O.E. Orientation Angle [deg]",
                          labelWidth=220,
                          valueType=float, orientation="horizontal")

        self.mirror_orientation_angle_user()


        #########################################################
        # Surface Shape
        #########################################################
        box_1 = oasysgui.widgetBox(subtab_surface_shape, "Surface Shape", addSpace=True, orientation="vertical")

        gui.comboBox(box_1, self, "surface_shape_type", label="Figure",
                     labelWidth=390,
                     items=["Plane", "Sphere", "Ellipsoid", "Hyperboloid", "Paraboloid", "Toroid"],
                     valueType=int,
                     sendSelectedValue=False, orientation="horizontal", callback=self.surface_shape_focusing_visibility, )

        #########
        ######### Focusing parameters
        #########
        box_1 = oasysgui.widgetBox(subtab_surface_shape, "Surface Shape Parameter", addSpace=True, orientation="vertical")

        self.focusing_box = oasysgui.widgetBox(box_1, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.focusing_box, self, "surface_shape_parameters", label="Type",
                     items=["internal/calculated", "external/user_defined"], labelWidth=240,
                     callback=self.surface_shape_focusing_visibility, sendSelectedValue=False, orientation="horizontal")

        #
        #internal focusing parameters
        #
        self.focusing_internal_box = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical", height=150)

        gui.comboBox(self.focusing_internal_box, self, "focii_and_continuation_plane", label="Focii and Continuation Plane",
                     labelWidth=280,
                     items=["Coincident", "Different"], callback=self.surface_shape_focusing_visibility, sendSelectedValue=False,
                     orientation="horizontal")


        self.object_side_focal_distance_box = oasysgui.widgetBox(self.focusing_internal_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.object_side_focal_distance_box, self,
                                                              "object_side_focal_distance",
                                                              "Object Side Focal Distance", labelWidth=260,
                                                              valueType=float, orientation="horizontal")

        self.image_side_focal_distance_box = oasysgui.widgetBox(self.focusing_internal_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.image_side_focal_distance_box, self, "image_side_focal_distance",
                                                             "Image Side Focal Distance", labelWidth=260,
                                                             valueType=float, orientation="horizontal")

        gui.comboBox(self.image_side_focal_distance_box, self, "incidence_angle_respect_to_normal_type", label="Incidence Angle",
                     labelWidth=260,
                     items=["Copied from position",
                            "User value"],
                     sendSelectedValue=False, orientation="horizontal", callback=self.surface_shape_focusing_visibility)


        self.incidence_angle_respect_to_normal_box = oasysgui.widgetBox(self.focusing_internal_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.incidence_angle_respect_to_normal_box, self,
                                                                     "incidence_angle_respect_to_normal",
                                                                     "Incidence Angle Respect to Normal [deg]",
                                                                     labelWidth=290, valueType=float,
                                                                     orientation="horizontal")

        self.focus_location_box = oasysgui.widgetBox(self.focusing_internal_box, "", addSpace=False, orientation="vertical")
        gui.comboBox(self.focus_location_box, self, "focus_location", label="Focus location", labelWidth=220,
                     items=["Image is at Infinity", "Source is at Infinity"], sendSelectedValue=False,
                     orientation="horizontal")

        #
        # external focusing parameters
        #


        # sphere
        self.focusing_external_sphere = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_spherical_radius = oasysgui.lineEdit(self.focusing_external_sphere, self, "spherical_radius",
                                                     "Spherical Radius", labelWidth=260, valueType=float,
                                                     orientation="horizontal")
        # ellipsoid or hyperboloid
        self.focusing_external_ellipsoir_or_hyperboloid = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_ellipse_hyperbola_semi_major_axis = oasysgui.lineEdit(self.focusing_external_ellipsoir_or_hyperboloid, self,
                                                                      "ellipse_hyperbola_semi_major_axis",
                                                                      "Ellipse/Hyperbola semi-major Axis",
                                                                      labelWidth=260, valueType=float,
                                                                      orientation="horizontal")
        self.le_ellipse_hyperbola_semi_minor_axis = oasysgui.lineEdit(self.focusing_external_ellipsoir_or_hyperboloid, self,
                                                                      "ellipse_hyperbola_semi_minor_axis",
                                                                      "Ellipse/Hyperbola semi-minor Axis",
                                                                      labelWidth=260, valueType=float,
                                                                      orientation="horizontal")
        oasysgui.lineEdit(self.focusing_external_ellipsoir_or_hyperboloid, self, "angle_of_majax_and_pole",
                          "Angle of MajAx and Pole [CCW, deg]", labelWidth=260, valueType=float,
                          orientation="horizontal")

        # paraboloid
        self.focusing_external_paraboloid = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_paraboloid_parameter = oasysgui.lineEdit(self.focusing_external_paraboloid, self, "paraboloid_parameter",
                                                         "Paraboloid parameter", labelWidth=260, valueType=float,
                                                         orientation="horizontal")

        # toroid
        self.focusing_external_toroid = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_torus_major_radius = oasysgui.lineEdit(self.focusing_external_toroid, self, "torus_major_radius",
                                                       "Torus Major Radius", labelWidth=260, valueType=float,
                                                       orientation="horizontal")
        self.le_torus_minor_radius = oasysgui.lineEdit(self.focusing_external_toroid, self, "torus_minor_radius",
                                                       "Torus Minor Radius", labelWidth=260, valueType=float,
                                                       orientation="horizontal")


        gui.comboBox(self.focusing_external_toroid, self, "toroidal_mirror_pole_location", label="Torus pole location",
                     labelWidth=145,
                     items=["lower/outer (concave/concave)",
                            "lower/inner (concave/convex)",
                            "upper/inner (convex/concave)",
                            "upper/outer (convex/convex)"],
                     sendSelectedValue=False, orientation="horizontal")

        #
        #
        #
        gui.comboBox(self.focusing_box, self, "surface_curvature", label="Surface Curvature",
                     items=["Concave", "Convex"], labelWidth=280, sendSelectedValue=False, orientation="horizontal")

        #
        #
        #
        gui.comboBox(self.focusing_box, self, "is_cylinder", label="Cylindrical", items=["No", "Yes"], labelWidth=350,
                     callback=self.surface_shape_focusing_visibility, sendSelectedValue=False, orientation="horizontal")

        self.cylinder_orientation_box = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.cylinder_orientation_box, self, "cylinder_orientation",
                     label="Cylinder Orientation (deg) [CCW from X axis]", labelWidth=350,
                     items=[0, 90],
                     valueType=float,
                     sendSelectedValue=False, orientation="horizontal")


        #########################################################
        # Reflectivity
        #########################################################

        box_1 = oasysgui.widgetBox(subtab_reflectivity, "Reflectivity Parameter", addSpace=True, orientation="vertical")

        gui.comboBox(box_1, self, "reflectivity_type", label="Reflectivity", labelWidth=150,
                     items=["Not considered", "From preprocessor PREREFL file", "Internal calculation"],
                     callback=self.reflectivity_type_visibility, sendSelectedValue=False, orientation="horizontal")


        self.file_prerefl_box = oasysgui.widgetBox(box_1, "", addSpace=False, orientation="horizontal", height=25)
        self.le_file_prerefl = oasysgui.lineEdit(self.file_prerefl_box, self, "file_prerefl", "File Name", labelWidth=100,
                                                 valueType=str, orientation="horizontal")
        gui.button(self.file_prerefl_box, self, "...", callback=self.selectFilePrerefl)

        self.reflectivity_compound_box = oasysgui.widgetBox(box_1, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.reflectivity_compound_box, self, "reflectivity_compound_name", "Compound Name",
                                                 labelWidth=230, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.reflectivity_compound_box, self, "reflectivity_compound_density", "Compound Density [g/cm^3]",
                                                 labelWidth=230, valueType=float, orientation="horizontal")


        #########################################################
        # Dimensions
        #########################################################


        #
        #
        #
        self.surface_shape_focusing_visibility()
        self.reflectivity_type_visibility()
        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

        # self.shape_box = oasysgui.widgetBox(self.tab_bas, "Boundary Shape", addSpace=True, orientation="vertical")

    #
    #         gui.comboBox(self.shape_box, self, "shape", label="Boundary Shape", labelWidth=350,
    #                      items=["Rectangle", "Circle", "Ellipse"],
    #                      callback=self.set_Shape,
    #                      sendSelectedValue=False, orientation="horizontal")
    #
    #         oasysgui.lineEdit(self.shape_box, self, "horizontal_shift", "Horizontal Shift [m]", labelWidth=260,
    #                           valueType=float, orientation="horizontal")
    #         oasysgui.lineEdit(self.shape_box, self, "vertical_shift", "Vertical Shift [m]", labelWidth=260, valueType=float,
    #                           orientation="horizontal")
    #
    #         self.rectangle_box = oasysgui.widgetBox(self.shape_box, "", addSpace=False, orientation="vertical", height=60)
    #
    #         oasysgui.lineEdit(self.rectangle_box, self, "width", "Width [m]", labelWidth=260, valueType=float,
    #                           orientation="horizontal")
    #         oasysgui.lineEdit(self.rectangle_box, self, "height", "Height [m]", labelWidth=260, valueType=float,
    #                           orientation="horizontal")
    #
    #         self.circle_box = oasysgui.widgetBox(self.shape_box, "", addSpace=False, orientation="vertical", height=60)
    #
    #         oasysgui.lineEdit(self.circle_box, self, "radius", "Radius [m]", labelWidth=260, valueType=float,
    #                           orientation="horizontal")
    #
    #         self.ellipse_box = oasysgui.widgetBox(self.shape_box, "", addSpace=False, orientation="vertical", height=60)
    #
    #         oasysgui.lineEdit(self.ellipse_box, self, "min_ax", "Axis a [m]", labelWidth=260, valueType=float,
    #                           orientation="horizontal")
    #         oasysgui.lineEdit(self.ellipse_box, self, "maj_ax", "Axis b [m]", labelWidth=260, valueType=float,
    #                           orientation="horizontal")
    #
    #         self.set_Shape()
    #
    #
    # def set_Shape(self):
    #     self.rectangle_box.setVisible(self.shape == 0)
    #     self.circle_box.setVisible(self.shape == 1)
    #     self.ellipse_box.setVisible(self.shape == 2)
    #
    #
    # def get_boundary_shape(self):
    #     if self.shape == 0:
    #         boundary_shape = Rectangle(x_left=-0.5 * self.width + self.horizontal_shift,
    #                                    x_right=0.5 * self.width + self.horizontal_shift,
    #                                    y_bottom=-0.5 * self.height + self.vertical_shift,
    #                                    y_top=0.5 * self.height + self.vertical_shift)
    #
    #     elif self.shape == 1:
    #         boundary_shape = Circle(self.radius,
    #                                 x_center=self.horizontal_shift,
    #                                 y_center=self.vertical_shift)
    #     elif self.shape == 2:
    #         boundary_shape = Ellipse(a_axis_min=-0.5 * self.min_ax + self.horizontal_shift,
    #                                  a_axis_max=0.5 * self.min_ax + self.horizontal_shift,
    #                                  b_axis_min=-0.5 * self.maj_ax + self.vertical_shift,
    #                                  b_axis_max=0.5 * self.maj_ax + self.vertical_shift)
    #
    #     return boundary_shape


    #########################################################
    # Position Methods
    #########################################################
    def set_angles_respect_to(self):
        label_1 = self.incidence_angle_deg_le.parent().layout().itemAt(0).widget()
        label_2 = self.reflection_angle_deg_le.parent().layout().itemAt(0).widget()

        if self.angles_respect_to == 0:
            label_1.setText("Incident Angle\nwith respect to the normal [deg]")
            label_2.setText("Reflection Angle\nwith respect to the normal [deg]")
        else:
            label_1.setText("Incident Angle\nwith respect to the surface [deg]")
            label_2.setText("Reflection Angle\nwith respect to the surface [deg]")

        self.calculate_incidence_angle_mrad()
        self.calculate_reflection_angle_mrad()

    def calculate_incidence_angle_mrad(self):
        digits = 7

        if self.angles_respect_to == 0: self.incidence_angle_mrad = round(numpy.radians(90-self.incidence_angle_deg)*1000, digits)
        else:                           self.incidence_angle_mrad = round(numpy.radians(self.incidence_angle_deg)*1000, digits)

        # if self.graphical_options.is_curved and not self.graphical_options.is_conic_coefficients:
        #     if self.incidence_angle_respect_to_normal_type == 0:
        #         if self.angles_respect_to == 0: self.incidence_angle_respect_to_normal = self.incidence_angle_deg
        #         else:                           self.incidence_angle_respect_to_normal = round(90 - self.incidence_angle_deg, 10)
        #
        if True: # self.graphical_options.is_mirror:
            self.reflection_angle_deg  = self.incidence_angle_deg
            self.reflection_angle_mrad = self.incidence_angle_mrad

    def calculate_reflection_angle_mrad(self):
        digits = 7

        if self.angles_respect_to == 0: self.reflection_angle_mrad = round(numpy.radians(90 - self.reflection_angle_deg)*1000, digits)
        else:                           self.reflection_angle_mrad = round(numpy.radians(self.reflection_angle_deg)*1000, digits)

    def calculate_incidence_angle_deg(self):
        digits = 10

        if self.angles_respect_to == 0: self.incidence_angle_deg = round(numpy.degrees(0.5 * numpy.pi - (self.incidence_angle_mrad / 1000)), digits)
        else:                           self.incidence_angle_deg = round(numpy.degrees(self.incidence_angle_mrad / 1000), digits)

        if True: #self.graphical_options.is_mirror:
            self.reflection_angle_deg = self.incidence_angle_deg
            self.reflection_angle_mrad = self.incidence_angle_mrad
        #
        # if self.graphical_options.is_curved and not self.graphical_options.is_conic_coefficients:
        #     if self.incidence_angle_respect_to_normal_type == 0:
        #         if self.angles_respect_to == 0: self.incidence_angle_respect_to_normal = self.incidence_angle_deg
        #         else:                           self.incidence_angle_respect_to_normal = round(90 - self.incidence_angle_deg, digits)

    def calculate_reflection_angle_deg(self):
        digits = 10

        if self.angles_respect_to == 0: self.reflection_angle_deg = round(numpy.degrees(0.5*numpy.pi-(self.reflection_angle_mrad/1000)), digits)
        else:                           self.reflection_angle_deg = round(numpy.degrees(self.reflection_angle_mrad/1000), digits)

    def mirror_orientation_angle_user(self):

        if self.mirror_orientation_angle < 4:
            self.mirror_orientation_angle_user_value_le.setVisible(False)
        else:
            self.mirror_orientation_angle_user_value_le.setVisible(True)

    def get_element_coordinates(self):
        if self.mirror_orientation_angle == 0:
            angle_azimuthal=0
        elif self.mirror_orientation_angle == 1:
            angle_azimuthal=90
        elif self.mirror_orientation_angle == 2:
            angle_azimuthal=180
        elif self.mirror_orientation_angle == 3:
            angle_azimuthal=270
        elif self.mirror_orientation_angle == 4:
            angle_azimuthal=self.mirror_orientation_angle_user

        print(">> angle_radial [deg]: ", self.incidence_angle_deg)
        print(">> angle_azimuthal [deg]: ", angle_azimuthal)
        ele_coor =  ElementCoordinates(
                p=self.source_plane_distance,
                q=self.image_plane_distance,
                angle_radial=numpy.radians(self.incidence_angle_deg),
                angle_azimuthal=numpy.radians(angle_azimuthal),
                )
        print(ele_coor.info())
        return ele_coor

    #########################################################
    # Surface Shape Methods
    #########################################################
    def surface_shape_focusing_visibility(self):

        self.focusing_box.setVisible(False)

        self.focusing_internal_box.setVisible(False)
        self.object_side_focal_distance_box.setVisible(False)
        self.image_side_focal_distance_box.setVisible(False)
        self.incidence_angle_respect_to_normal_box.setVisible(False)
        self.focus_location_box.setVisible(False)


        self.focusing_external_sphere.setVisible(False)
        self.focusing_external_ellipsoir_or_hyperboloid.setVisible(False)
        self.focusing_external_paraboloid.setVisible(False)
        self.focusing_external_toroid.setVisible(False)

        self.cylinder_orientation_box.setVisible(False)

        if self.surface_shape_type > 0: # not plane
            self.focusing_box.setVisible(True)

            if self.surface_shape_parameters == 0:
                self.focusing_internal_box.setVisible(True)
                if self.focii_and_continuation_plane == 0:
                    pass
                else:
                    self.object_side_focal_distance_box.setVisible(True)
                    self.image_side_focal_distance_box.setVisible(True)
                    if self.incidence_angle_respect_to_normal_type == 1:
                        self.incidence_angle_respect_to_normal_box.setVisible(True)

            else:
                if self.surface_shape_type == 0: # plane
                    pass
                elif self.surface_shape_type == 1: # sphere
                    self.focusing_external_sphere.setVisible(True)
                elif self.surface_shape_type == 2: # ellipsoid
                    self.focusing_external_ellipsoir_or_hyperboloid.setVisible(True)
                elif self.surface_shape_type == 3: # hyperboloid
                    self.focusing_external_ellipsoir_or_hyperboloid.setVisible(True)
                elif self.surface_shape_type == 4: # paraboloid
                    self.focusing_external_paraboloid.setVisible(True)
                elif self.surface_shape_type == 5: # toroid
                    self.focusing_external_toroid.setVisible(True)

            if self.is_cylinder:
                self.cylinder_orientation_box.setVisible(True)

    #########################################################
    # Reflectvity Methods
    #########################################################
    def reflectivity_type_visibility(self):
        if self.reflectivity_type == 1:
            self.file_prerefl_box.setVisible(True)
        else:
            self.file_prerefl_box.setVisible(False)

        if self.reflectivity_type == 2:
            self.reflectivity_compound_box.setVisible(True)
        else:
            self.reflectivity_compound_box.setVisible(False)


    def selectFilePrerefl(self):
        self.le_file_prerefl.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl, "Select File Prerefl")) #, file_extension_filter="Data Files (*.dat)"))



    # def get_mirror_element(self):
    #         pass
    #         # mirror1 = S4ConicMirrorElement(optical_element=S4ConicMirror(name="M1",
    #         #                                                    conic_coefficients=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0],
    #         #                                                    boundary_shape=boundary_shape),
    #         #                           coordinates=coordinates_syned)
    #
    #
    #
    # def set_IntExt_Parameters(self):
    #     self.surface_box_int.setVisible(self.surface_shape_parameters == 0)
    #     self.surface_box_ext.setVisible(self.surface_shape_parameters == 1)
    #     if self.surface_shape_parameters == 0: self.set_FociiCont_Parameters()
    #
    #     # if not self.graphical_options.is_toroidal:
    #     #     self.render_surface_button.setEnabled(self.surface_shape_parameters == 0)
    #
    # def set_FociiCont_Parameters(self):
    #     self.surface_box_int_2.setVisible(self.focii_and_continuation_plane == 1)
    #     self.surface_box_int_2_empty.setVisible(self.focii_and_continuation_plane == 0)
    #
    # def set_incidenceAngleRespectToNormal(self):
    #     self.surface_box_int_3.setVisible(self.incidence_angle_respect_to_normal_type==1)
    #     self.surface_box_int_3_empty.setVisible(self.incidence_angle_respect_to_normal_type==0)
    #
    #     self.calculate_incidence_angle_mrad()
    #
    # def set_isCyl_Parameters(self):
    #     self.surface_box_cyl.setVisible(self.is_cylinder == 1)
    #     self.surface_box_cyl_empty.setVisible(self.is_cylinder == 0)
    #

#     def checkFields(self):
#         self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
#         self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
#         self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
#         self.delta_e = congruence.checkPositiveNumber(self.delta_e, "Delta Energy")
#         self.undulator_length = congruence.checkPositiveNumber(self.undulator_length, "Undulator Length")
#
#     def get_lightsource(self):
#         # syned electron beam
#         electron_beam, script_electron_beam = self.get_syned_electron_beam()
#         print(">>>>>> electron_beam info: ", electron_beam.info())
#         script = script_electron_beam
#
#         script += "\n\n# Gaussian undulator"
#
#         if self.type_of_properties == 3:
#             flag_emittance = 0
#         else:
#             flag_emittance = 1
#
#         sourceundulator = S4Undulator(
#             # K_vertical=1.0,  # syned Undulator parameter
#             period_length=self.undulator_length/100,  # syned Undulator parameter
#             number_of_periods=100,  # syned Undulator parameter
#             emin=self.energy - 0.5 * self.delta_e,  # Photon energy scan from energy (in eV)
#             emax=self.energy + 0.5 * self.delta_e,  # Photon energy scan to energy (in eV)
#             # ng_e=11,  # Photon energy scan number of points
#             # maxangle=50e-6,  # Maximum radiation semiaperture in RADIANS
#             # ng_t=31,  # Number of points in angle theta
#             # ng_p=21,  # Number of points in angle phi
#             # ng_j=20,  # Number of points in electron trajectory (per period) for internal calculation only
#             # code_undul_phot="internal",  # internal, pysru, srw
#             flag_emittance=flag_emittance,  # when sampling rays: Use emittance (0=No, 1=Yes)
#             # flag_size=0,  # when sampling rays: 0=point,1=Gaussian,2=FT(Divergences)
#         )
#
#         script_template = """
# from shadow4.sources.undulator.s4_undulator import S4Undulator
# sourceundulator = S4Undulator(
#     period_length     = {period_length},
#     number_of_periods = 100,
#     emin              = {emin},
#     emax              = {emax},
#     flag_emittance    = {flag_emittance},  # Use emittance (0=No, 1=Yes)
#     )"""
#
#         script_dict = {
#             "period_length"     : self.undulator_length / 100,
#             "number_of_periods" : 100,
#             "emin"              : self.energy - 0.5 * self.delta_e,
#             "emax"              : self.energy + 0.5 * self.delta_e,
#             "flag_emittance"    : flag_emittance,
#             }
#
#         script += script_template.format_map(script_dict)
#
#         if self.delta_e == 0:
#             sourceundulator.set_energy_monochromatic(self.energy)
#             script += "\nsourceundulator.set_energy_monochromatic(%g)" % self.energy
#         else:
#             sourceundulator.set_energy_box(self.energy-0.5*self.delta_e, self.energy+0.5*self.delta_e,)
#             script += "\nsourceundulator.set_energy_box(%g,%g)" % (self.energy-0.5*self.delta_e, self.energy+0.5*self.delta_e)
#
#         # S4UndulatorLightSource
#         lightsource = S4UndulatorLightSource(name='GaussianUndulator', electron_beam=electron_beam,
#                                            undulator_magnetic_structure=sourceundulator)
#         script += "\n\nfrom shadow4.sources.undulator.s4_undulator_light_source import S4UndulatorLightSource"
#         script += "\nlightsource = S4UndulatorLightSource(name='GaussianUndulator', electron_beam=electron_beam, undulator_magnetic_structure=sourceundulator)"
#         print(">>>>>> S4UndulatorLightSource info: ", lightsource.info())
#
#         return lightsource, script
#
    def run_shadow4(self):
        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        ele_coor = self.get_element_coordinates()
        self.set_PlotQuality()

        self.progressBarInit()
        self.progressBarFinished()
#
#         sys.stdout = EmittingStream(textWritten=self.writeStdOut)
#
#         self.set_PlotQuality()
#
#         self.progressBarInit()
#
#         lightsource, script = self.get_lightsource()
#
#         self.progressBarSet(5)
#         #
#         # run shadow4
#         #
#         t00 = time.time()
#         print(">>>> starting calculation...")
#         beam = lightsource.get_beam_in_gaussian_approximation(NRAYS=self.number_of_rays, SEED=self.seed)
#         t11 = time.time() - t00
#         print(">>>> time for %d rays: %f s, %f min, " % (self.number_of_rays, t11, t11 / 60))
#
#
#         script +="\n\nbeam = lightsource.get_beam_in_gaussian_approximation(NRAYS=%d, SEED=%d)" % \
#                  (self.number_of_rays, self.seed)
#
#         #
#         # beam plots
#         #
#         BEAM = ShadowBeam(beam=beam, oe_number=0, number_of_rays=self.number_of_rays)
#         self.plot_results(BEAM, progressBarValue=80)
#
#         #
#         # script
#         #
#         self.shadow4_script.set_code(script)
#
#         self.progressBarFinished()
#
#         #
#         # send beam
#         #
#         self.send("Beam4", ShadowBeam())
#
#
#     def receive_syned_data(self, data):
#         if data is not None:
#             if isinstance(data, Beamline):
#                 if not data.get_light_source() is None:
#                     if isinstance(data.get_light_source().get_magnetic_structure(), Undulator):
#                         light_source = data.get_light_source()
#
#                         self.energy =  round(light_source.get_magnetic_structure().resonance_energy(light_source.get_electron_beam().gamma()), 3)
#                         self.delta_e = 0.0
#                         self.undulator_length = light_source.get_magnetic_structure().length()
#
#                         self.populate_fields_from_syned_electron_beam(light_source.get_electron_beam())
#
#                     else:
#                         raise ValueError("Syned light source not congruent")
#                 else:
#                     raise ValueError("Syned data not correct: light source not present")
#             else:
#                 raise ValueError("Syned data not correct")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWMirror()
    ow.show()
    a.exec_()
    ow.saveSettings()
