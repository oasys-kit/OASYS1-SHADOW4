import numpy
import sys

from PyQt5.QtGui import QPalette, QColor, QFont

from orangewidget import widget
from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import EmittingStream

from syned.widget.widget_decorator import WidgetDecorator

from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.shape import Rectangle
from syned.beamline.shape import Ellipse

from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
from orangecontrib.shadow4.util.shadow_objects import ShadowData
from orangecontrib.shadow4.util.shadow_util import ShadowCongruence

from orangecanvas.resources import icon_loader
from orangecanvas.scheme.node import SchemeNode

class OWOpticalElementWithSurfaceShape(GenericElement, WidgetDecorator):
    inputs = [("Shadow Data", ShadowData, "set_shadow_data")]
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Shadow Data",
                "type":ShadowData,
                "doc":"",}]

    #########################################################
    # Position
    #########################################################
    source_plane_distance           = Setting(1.0)
    image_plane_distance            = Setting(1.0)
    angles_respect_to               = Setting(0)
    incidence_angle_deg             = Setting(88.8)
    incidence_angle_mrad            = Setting(0.0)
    reflection_angle_deg            = Setting(85.0)
    reflection_angle_mrad           = Setting(0.0)
    oe_orientation_angle            = Setting(1)
    oe_orientation_angle_user_value = Setting(0.0)

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

    spherical_radius                        = Setting(1.0)
    torus_major_radius                      = Setting(1.0)
    torus_minor_radius                      = Setting(1.0)
    ellipse_hyperbola_semi_major_axis       = Setting(1.0)
    ellipse_hyperbola_semi_minor_axis       = Setting(1.0)
    angle_of_majax_and_pole                 = Setting(1.0)
    paraboloid_parameter                    = Setting(1.0)

    surface_curvature                       = Setting(0)
    is_cylinder                             = Setting(1)
    cylinder_orientation                    = Setting(0)

    conic_coefficient_0 = Setting(0.0)
    conic_coefficient_1 = Setting(0.0)
    conic_coefficient_2 = Setting(0.0)
    conic_coefficient_3 = Setting(0.0)
    conic_coefficient_4 = Setting(0.0)
    conic_coefficient_5 = Setting(0.0)
    conic_coefficient_6 = Setting(0.0)
    conic_coefficient_7 = Setting(0.0)
    conic_coefficient_8 = Setting(-1.0)
    conic_coefficient_9 = Setting(0.0)

    #########################################################
    # dimensions
    #########################################################
    is_infinite  = Setting(0)
    oe_shape = Setting(0)
    dim_x_plus   = Setting(1.0)
    dim_x_minus  = Setting(1.0)
    dim_y_plus   = Setting(1.0)
    dim_y_minus  = Setting(1.0)

    input_data = None

    def createdFromNode(self, node):
        super(OWOpticalElementWithSurfaceShape, self).createdFromNode(node)
        self.__change_icon_from_surface_type()

    def widgetNodeAdded(self, node_item : SchemeNode):
        super(GenericElement, self).widgetNodeAdded(node_item)
        self.__change_icon_from_surface_type()

    def __change_icon_from_surface_type(self):
        try:
            node = self.getNode()
            node.description.icon = self.icons_for_shape[self.surface_shape_type]
            self.changeNodeIcon(icon_loader.from_description(node.description).get(node.description.icon))
            if node.title in self.oe_names: self.changeNodeTitle(self.title_for_shape[self.surface_shape_type])
        except:
            pass

    def get_oe_type(self): return "", ""

    @property
    def icons_for_shape(self):
        type, _ = self.get_oe_type()

        return {0 : "icons/plane_" + type + ".png",
                1 : "icons/spherical_" + type + ".png",
                2 : "icons/ellipsoid_" + type + ".png",
                3 : "icons/hyperboloid_" + type + ".png",
                4 : "icons/paraboloid_" + type + ".png",
                5 : "icons/toroidal_" + type + ".png",
                6 : "icons/conic_coefficients_" + type + ".png",}

    @property
    def oe_names(self):
        _, name = self.get_oe_type()
        return ["Generic " + name,
                "Plane " + name,
                "Spherical " + name,
                "Elliptical " + name,
                "Hyperbolical " + name,
                "Parabolical " + name,
                "Toroidal " + name,
                "Conic coefficients " + name]
    @property
    def title_for_shape(self):
        return {0 : self.oe_names[1],
                1 : self.oe_names[2],
                2 : self.oe_names[3],
                3 : self.oe_names[4],
                4 : self.oe_names[5],
                5 : self.oe_names[6],
                6 : self.oe_names[7]}

    def __init__(self):
        super().__init__()

        #
        # main buttons
        #
        self.runaction = widget.OWAction("Run Shadow4/Trace", self)
        self.runaction.triggered.connect(self.run_shadow4)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run shadow4/trace", callback=self.run_shadow4)
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

        #
        # tabs
        #
        self.tabs_control_area = oasysgui.tabWidget(self.controlArea)
        self.tabs_control_area.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_control_area.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_position         = oasysgui.createTabPage(self.tabs_control_area, "Position")           # to be populated
        tab_basic_settings   = oasysgui.createTabPage(self.tabs_control_area, "Basic Settings")
        tabs_basic_setting   = oasysgui.tabWidget(tab_basic_settings)
        subtab_surface_shape = oasysgui.createTabPage(tabs_basic_setting, "Surface Shape")  # to be populated
        specific_subtabs     = self.create_specific_subtabs(tabs_basic_setting)
        subtab_dimensions    = oasysgui.createTabPage(tabs_basic_setting, "Dimensions")        # to be populated
        
        tab_advanced_settings = oasysgui.createTabPage(self.tabs_control_area, "Advanced Settings")
        tabs_advanced_settings = oasysgui.tabWidget(tab_advanced_settings)
        subtab_modified_surface = oasysgui.createTabPage(tabs_advanced_settings, "Modified Surface") # to be populated
        subtab_oe_movement= oasysgui.createTabPage(tabs_advanced_settings, "O.E. Movement")          # to be populated        
        # subtab_output_files = oasysgui.createTabPage(tabs_advanced_settings, "Output Files")

        #
        # populate tabs with widgets
        #

        #########################################################
        # Position
        #########################################################
        self.populate_tab_position(tab_position)

        #########################################################
        # Basic Settings / Surface Shape
        #########################################################
        self.populate_tab_surface_shape(subtab_surface_shape)

        #########################################################
        # Specific SubTabs
        #########################################################
        self.populate_specific_subtabs(specific_subtabs)

        #########################################################
        # Basic Settings / Dimensions
        #########################################################
        self.populate_tab_dimensions(subtab_dimensions)
    
        #########################################################
        # Advanced Settings / Modified Surface
        #########################################################
        self.populate_tab_modified_surface(subtab_modified_surface)
    
        #########################################################
        # Advanced Settings / Modified Surface
        #########################################################
        self.populate_tab_oe_movement(subtab_oe_movement)

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def create_specific_subtabs(self, tabs_basic_setting): pass
    def populate_specific_subtabs(self, specific_subtabs): pass
    
    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="image_plane_distance")

        gui.comboBox(self.orientation_box, self, "angles_respect_to", label="Angles in [deg] with respect to the",
                     labelWidth=250, items=["Normal", "Surface"], callback=self.set_angles_respect_to,
                     sendSelectedValue=False, orientation="horizontal", tooltip="angles_respect_to")

        self.incidence_angle_deg_le = oasysgui.lineEdit(self.orientation_box, self, "incidence_angle_deg",
                                                        "Incident Angle\nwith respect to the Normal [deg]",
                                                        labelWidth=220, callback=self.calculate_incidence_angle_mrad,
                                                        valueType=float, orientation="horizontal", tooltip="incidence_angle_deg")
        self.incidence_angle_rad_le = oasysgui.lineEdit(self.orientation_box, self, "incidence_angle_mrad",
                                                        "Incident Angle\nwith respect to the surface [mrad]",
                                                        labelWidth=220, callback=self.calculate_incidence_angle_deg,
                                                        valueType=float, orientation="horizontal", tooltip="incidence_angle_mrad")
        self.reflection_angle_deg_le = oasysgui.lineEdit(self.orientation_box, self, "reflection_angle_deg",
                                                         "Reflection Angle\nwith respect to the Normal [deg]",
                                                         labelWidth=220, callback=self.calculate_reflection_angle_mrad,
                                                         valueType=float, orientation="horizontal", tooltip="reflection_angle_deg")
        self.reflection_angle_rad_le = oasysgui.lineEdit(self.orientation_box, self, "reflection_angle_mrad",
                                                         "Reflection Angle\nwith respect to the surface [mrad]",
                                                         labelWidth=220, callback=self.calculate_reflection_angle_deg,
                                                         valueType=float, orientation="horizontal", tooltip="reflection_angle_mrad")

        self.set_angles_respect_to()

        self.calculate_incidence_angle_mrad()
        self.calculate_reflection_angle_mrad()

        if True: # self.graphical_options.is_mirror:
            self.reflection_angle_deg_le.setEnabled(False)
            self.reflection_angle_rad_le.setEnabled(False)

        gui.comboBox(self.orientation_box, self, "oe_orientation_angle", label="O.E. Orientation Angle [deg]",
                     labelWidth=390,
                     items=[0, 90, 180, 270, "Other value..."],
                     valueType=float,
                     sendSelectedValue=False, orientation="horizontal", callback=self.oe_orientation_angle_user,
                     tooltip="oe_orientation_angle" )
        self.oe_orientation_angle_user_value_le = oasysgui.widgetBox(self.orientation_box, "", addSpace=False,
                                                                         orientation="vertical")
        oasysgui.lineEdit(self.oe_orientation_angle_user_value_le, self, "oe_orientation_angle_user_value",
                          "O.E. Orientation Angle [deg]",
                          labelWidth=220,
                          valueType=float, orientation="horizontal", tooltip="oe_orientation_angle_user_value")

        self.oe_orientation_angle_user()

    def populate_tab_surface_shape(self, subtab_surface_shape):

        box_1 = oasysgui.widgetBox(subtab_surface_shape, "Surface Shape", addSpace=True, orientation="vertical")

        gui.comboBox(box_1, self, "surface_shape_type", label="Figure",
                     labelWidth=390,
                     items=["Plane", "Sphere", "Ellipsoid", "Hyperboloid", "Paraboloid", "Toroid", "Conic coefficients"],
                     valueType=int,
                     sendSelectedValue=False, orientation="horizontal", callback=self.surface_shape_tab_visibility,
                     tooltip="surface_shape_type")

        #########
        ######### Focusing parameters
        #########
        box_1 = oasysgui.widgetBox(subtab_surface_shape, "Surface Shape Parameter", addSpace=True, orientation="vertical")

        self.focusing_box = oasysgui.widgetBox(box_1, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.focusing_box, self, "surface_shape_parameters", label="Type",
                     items=["internal/calculated", "external/user_defined"], labelWidth=240,
                     callback=self.surface_shape_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="surface_shape_parameters")

        #
        #internal focusing parameters
        #
        self.focusing_internal_box = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical", height=150)

        gui.comboBox(self.focusing_internal_box, self, "focii_and_continuation_plane", label="Focii and Continuation Plane",
                     labelWidth=280,
                     items=["Coincident", "Different"], callback=self.surface_shape_tab_visibility, sendSelectedValue=False,
                     orientation="horizontal", tooltip="focii_and_continuation_plane")


        self.object_side_focal_distance_box = oasysgui.widgetBox(self.focusing_internal_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.object_side_focal_distance_box, self,
                                                              "object_side_focal_distance",
                                                              "Object Side Focal Distance [m]", labelWidth=260,
                                                              valueType=float, orientation="horizontal", tooltip="object_side_focal_distance")

        self.image_side_focal_distance_box = oasysgui.widgetBox(self.focusing_internal_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.image_side_focal_distance_box, self, "image_side_focal_distance",
                                                             "Image Side Focal Distance [m]", labelWidth=260,
                                                             valueType=float, orientation="horizontal", tooltip="image_side_focal_distance")

        gui.comboBox(self.image_side_focal_distance_box, self, "incidence_angle_respect_to_normal_type", label="Incidence Angle",
                     labelWidth=260,
                     items=["Copied from position",
                            "User value"],
                     sendSelectedValue=False, orientation="horizontal", callback=self.surface_shape_tab_visibility,
                     tooltip="incidence_angle_respect_to_normal_type")


        self.incidence_angle_respect_to_normal_box = oasysgui.widgetBox(self.focusing_internal_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.incidence_angle_respect_to_normal_box, self,
                                                                     "incidence_angle_respect_to_normal",
                                                                     "Incidence Angle Respect to Normal [deg]",
                                                                     labelWidth=290, valueType=float,
                                                                     orientation="horizontal", tooltip="incidence_angle_respect_to_normal")

        self.focus_location_box = oasysgui.widgetBox(self.focusing_internal_box, "", addSpace=False, orientation="vertical")
        gui.comboBox(self.focus_location_box, self, "focus_location", label="Focus location", labelWidth=220,
                     items=["Image is at Infinity", "Source is at Infinity"], sendSelectedValue=False,
                     orientation="horizontal", tooltip="focus_location")

        #
        # external focusing parameters
        #

        # sphere
        self.focusing_external_sphere = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_spherical_radius = oasysgui.lineEdit(self.focusing_external_sphere, self, "spherical_radius",
                                                     "Spherical Radius [m]", labelWidth=260, valueType=float,
                                                     orientation="horizontal", tooltip="spherical_radius")
        # ellipsoid or hyperboloid
        self.focusing_external_ellipsoir_or_hyperboloid = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_ellipse_hyperbola_semi_major_axis = oasysgui.lineEdit(self.focusing_external_ellipsoir_or_hyperboloid, self,
                                                                      "ellipse_hyperbola_semi_major_axis",
                                                                      "Ellipse/Hyperbola semi-major Axis [m]",
                                                                      labelWidth=260, valueType=float,
                                                                      orientation="horizontal", tooltip="ellipse_hyperbola_semi_major_axis")
        self.le_ellipse_hyperbola_semi_minor_axis = oasysgui.lineEdit(self.focusing_external_ellipsoir_or_hyperboloid, self,
                                                                      "ellipse_hyperbola_semi_minor_axis",
                                                                      "Ellipse/Hyperbola semi-minor Axis [m]",
                                                                      labelWidth=260, valueType=float,
                                                                      orientation="horizontal", tooltip="ellipse_hyperbola_semi_minor_axis")
        oasysgui.lineEdit(self.focusing_external_ellipsoir_or_hyperboloid, self, "angle_of_majax_and_pole",
                          "Angle of MajAx and Pole [CCW, deg]", labelWidth=260, valueType=float,
                          orientation="horizontal", tooltip="angle_of_majax_and_pole")

        # paraboloid
        self.focusing_external_paraboloid = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_paraboloid_parameter = oasysgui.lineEdit(self.focusing_external_paraboloid, self, "paraboloid_parameter",
                                                         "Paraboloid parameter [m]", labelWidth=260, valueType=float,
                                                         orientation="horizontal", tooltip="float")

        # toroid
        self.focusing_external_toroid = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_torus_major_radius = oasysgui.lineEdit(self.focusing_external_toroid, self, "torus_major_radius",
                                                       "Torus Major Radius [m]", labelWidth=260, valueType=float,
                                                       orientation="horizontal", tooltip="torus_major_radius")
        self.le_torus_minor_radius = oasysgui.lineEdit(self.focusing_external_toroid, self, "torus_minor_radius",
                                                       "Torus Minor Radius [m]", labelWidth=260, valueType=float,
                                                       orientation="horizontal", tooltip="torus_minor_radius")


        gui.comboBox(self.focusing_external_toroid, self, "toroidal_mirror_pole_location", label="Torus pole location",
                     labelWidth=145,
                     items=["lower/outer (concave/concave)",
                            "lower/inner (concave/convex)",
                            "upper/inner (convex/concave)",
                            "upper/outer (convex/convex)"],
                     sendSelectedValue=False, orientation="horizontal", tooltip="toroidal_mirror_pole_location")

        # conic coefficients
        self.ccc_box = oasysgui.widgetBox(box_1, "", addSpace=False, orientation="vertical", height=250)

        oasysgui.lineEdit(self.ccc_box, self, "conic_coefficient_0", "c[0]=Cxx=", labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ccc_box, self, "conic_coefficient_1", "c[1]=Cyy=", labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ccc_box, self, "conic_coefficient_2", "c[2]=Czz=", labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ccc_box, self, "conic_coefficient_3", "c[3]=Cxy=", labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ccc_box, self, "conic_coefficient_4", "c[4]=Cyz=", labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ccc_box, self, "conic_coefficient_5", "c[5]=Cxz=", labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ccc_box, self, "conic_coefficient_6", "c[6]=Cx=",  labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ccc_box, self, "conic_coefficient_7", "c[7]=Cy=",  labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ccc_box, self, "conic_coefficient_8", "c[8]=Cz=",  labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ccc_box, self, "conic_coefficient_9", "c[9]=C0=",  labelWidth=60, valueType=float, orientation="horizontal")

        # flat or invert
        gui.comboBox(self.focusing_box, self, "surface_curvature", label="Surface Curvature",
                     items=["Concave", "Convex"], labelWidth=280, sendSelectedValue=False, orientation="horizontal",
                     tooltip="surface_curvature")

        #
        gui.comboBox(self.focusing_box, self, "is_cylinder", label="Cylindrical", items=["No", "Yes"], labelWidth=350,
                     callback=self.surface_shape_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="is_cylinder")

        self.cylinder_orientation_box = oasysgui.widgetBox(self.focusing_box, "", addSpace=False,
                                                           orientation="vertical")

        gui.comboBox(self.cylinder_orientation_box, self, "cylinder_orientation",
                     label="Cylinder Orientation (deg) [CCW from X axis]", labelWidth=350,
                     items=[0, 90],
                     valueType=float,
                     sendSelectedValue=False, orientation="horizontal", tooltip="cylinder_orientation")

        self.surface_shape_tab_visibility(is_init=True)

    def populate_tab_dimensions(self, subtab_dimensions):
        dimension_box = oasysgui.widgetBox(subtab_dimensions, "Dimensions", addSpace=True, orientation="vertical")

        gui.comboBox(dimension_box, self, "is_infinite", label="Limits Check",
                     items=["Infinite o.e. dimensions", "Finite o.e. dimensions"],
                     callback=self.dimensions_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="is_infinite")

        self.dimdet_box = oasysgui.widgetBox(dimension_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.dimdet_box, self, "oe_shape", label="Shape selected", labelWidth=260,
                     items=["Rectangular", "Elliptical"],
                     sendSelectedValue=False, orientation="horizontal", tooltip="oe_shape")

        self.le_dim_x_plus = oasysgui.lineEdit(self.dimdet_box, self, "dim_x_plus", "X(+) Half Width / Int Maj Ax [m]",
                                               labelWidth=260, valueType=float, orientation="horizontal", tooltip="dim_x_plus")
        self.le_dim_x_minus = oasysgui.lineEdit(self.dimdet_box, self, "dim_x_minus", "X(-) Half Width / Int Maj Ax [m]",
                                                labelWidth=260, valueType=float, orientation="horizontal", tooltip="dim_x_minus")
        self.le_dim_y_plus = oasysgui.lineEdit(self.dimdet_box, self, "dim_y_plus", "Y(+) Half Width / Int Min Ax [m]",
                                               labelWidth=260, valueType=float, orientation="horizontal", tooltip="dim_y_plus")
        self.le_dim_y_minus = oasysgui.lineEdit(self.dimdet_box, self, "dim_y_minus", "Y(-) Half Width / Int Min Ax [m]",
                                                labelWidth=260, valueType=float, orientation="horizontal", tooltip="dim_y_minus")

        self.dimensions_tab_visibility()

    def populate_tab_modified_surface(self, subtab_modified_surface):
        box = oasysgui.widgetBox(subtab_modified_surface, "Not yet implemented", addSpace=True, orientation="vertical")

    def populate_tab_oe_movement(self, subtab_oe_movement):
        box = oasysgui.widgetBox(subtab_oe_movement, "Not yet implemented", addSpace=True, orientation="vertical")

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

    def calculate_reflection_angle_mrad(self):
        digits = 7
        if self.angles_respect_to == 0: self.reflection_angle_mrad = round(numpy.radians(90 - self.reflection_angle_deg)*1000, digits)
        else:                           self.reflection_angle_mrad = round(numpy.radians(self.reflection_angle_deg)*1000, digits)

    def calculate_incidence_angle_deg(self):
        digits = 10
        if self.angles_respect_to == 0: self.incidence_angle_deg = round(numpy.degrees(0.5 * numpy.pi - (self.incidence_angle_mrad / 1000)), digits)
        else:                           self.incidence_angle_deg = round(numpy.degrees(self.incidence_angle_mrad / 1000), digits)

    def calculate_reflection_angle_deg(self):
        digits = 10

        if self.angles_respect_to == 0: self.reflection_angle_deg = round(numpy.degrees(0.5*numpy.pi-(self.reflection_angle_mrad/1000)), digits)
        else:                           self.reflection_angle_deg = round(numpy.degrees(self.reflection_angle_mrad/1000), digits)

    def oe_orientation_angle_user(self):
        if self.oe_orientation_angle < 4: self.oe_orientation_angle_user_value_le.setVisible(False)
        else:                             self.oe_orientation_angle_user_value_le.setVisible(True)

    def get_oe_orientation_angle(self):
        if self.oe_orientation_angle == 0:   return 0.0
        elif self.oe_orientation_angle == 1: return 90.0
        elif self.oe_orientation_angle == 2: return 180.0
        elif self.oe_orientation_angle == 3: return 270.0
        elif self.oe_orientation_angle == 4: return self.oe_orientation_angle_user_value

    #########################################################
    # Surface Shape Methods
    #########################################################
    def surface_shape_tab_visibility(self, is_init=False):
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

        self.ccc_box.setVisible(False)

        if self.surface_shape_type in (1,2,3,4,5): # not plane
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
        elif self.surface_shape_type == 6:
            self.ccc_box.setVisible(True)

        if not is_init: self.__change_icon_from_surface_type()

    #########################################################
    # Dimensions Methods
    #########################################################

    def dimensions_tab_visibility(self):

        if self.is_infinite: self.dimdet_box.setVisible(True)
        else:                self.dimdet_box.setVisible(False)

    #########################################################
    # S4 objects
    #########################################################

    def get_focusing_grazing_angle(self):
        if self.focii_and_continuation_plane == 0: return numpy.radians(90.0 - self.incidence_angle_deg)
        else:
            if self.incidence_angle_respect_to_normal_type == 0: return numpy.radians(90.0 - self.incidence_angle_deg)
            else:                                                return numpy.radians(self.incidence_angle_respect_to_normal)

    def get_focusing_p(self):
        if self.focii_and_continuation_plane == 0: return self.source_plane_distance
        else:                                      return self.object_side_focal_distance

    def get_focusing_q(self):
        if self.focii_and_continuation_plane == 0: return self.image_plane_distance
        else:                                      return self.image_side_focal_distance

    def get_boundary_shape(self):
        if self.is_infinite: return None
        else:
            if self.oe_shape == 0: # Rectangular
                return Rectangle(x_left=-self.dim_x_minus, x_right=self.dim_x_plus,
                                 y_bottom=-self.dim_y_minus, y_top=self.dim_y_plus)
            elif self.oe_shape == 1: # Ellispe
                return Ellipse(a_axis_min=-self.dim_x_minus, a_axis_max=self.dim_x_plus,
                               b_axis_min=-self.dim_y_minus, b_axis_max=self.dim_y_plus)

    def get_coordinates(self):
        print(">>>>>>inc ref m.o.a. in deg:",self.incidence_angle_deg,self.reflection_angle_deg, self.get_oe_orientation_angle())
        return ElementCoordinates(
                p=self.source_plane_distance,
                q=self.image_plane_distance,
                angle_radial=numpy.radians(self.incidence_angle_deg),
                angle_azimuthal=numpy.radians(self.get_oe_orientation_angle()),
                angle_radial_out=numpy.radians(self.reflection_angle_deg),
                )


    def set_shadow_data(self, input_data):
        self.not_interactive = self._check_not_interactive_conditions(input_data)
        self._on_receiving_input()

        if ShadowCongruence.check_empty_data(input_data):
            self.input_data = input_data.duplicate()
            if self.is_automatic_run: self.run_shadow4()

    def run_shadow4(self):
        self.shadow_output.setText("")

        sys.stdout = EmittingStream(textWritten=self._write_stdout)

        element = self.get_beamline_element_instance()
        element.set_optical_element(self.get_optical_element_instance())
        element.set_coordinates(self.get_coordinates())
        element.set_input_beam(self.input_data.beam)

        print(element.info())

        self.progressBarInit()

        output_beam, footprint = element.trace_beam()

        beamline = self.input_data.beamline.duplicate()
        beamline.append_beamline_element(element)

        self._set_plot_quality()

        self._plot_results(output_beam, footprint, progressBarValue=80)

        self.progressBarFinished()

        #
        # script
        #
        script = beamline.to_python_code()
        script += "\n\n\n# test plot"
        script += "\nif True:"
        script += "\n   from srxraylib.plot.gol import plot_scatter"
        script += "\n   rays = beam.get_rays()"
        script += "\n   plot_scatter(beam.get_photon_energy_eV(), beam.get_column(23), title='(Intensity,Photon Energy)')"
        script += "\n   plot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 2], title='(X,Z) in microns')"
        self.shadow4_script.set_code(script)

        #
        # send beam
        #
        self.send("Shadow Data", ShadowData(beam=output_beam, beamline=beamline)
)

    def receive_syned_data(self, data):
        raise Exception("Not yet implemented")

    def get_optical_element_instance(self): raise NotImplementedError()
    def get_beamline_element_instance(self): raise NotImplementedError()
