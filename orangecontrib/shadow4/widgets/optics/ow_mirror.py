import numpy
import sys

from PyQt5.QtGui import QPalette, QColor, QFont


from orangewidget import widget
from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
from orangecontrib.shadow4.util.shadow_objects import ShadowBeam

from syned.beamline.beamline import Beamline
from shadow4.beamline.s4_beamline import S4Beamline

from syned.widget.widget_decorator import WidgetDecorator

from shadow4.syned.element_coordinates import ElementCoordinates

from shadow4.syned.shape import Rectangle  # TODO from syned.beamline.shape
from shadow4.syned.shape import Convexity  #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
from shadow4.syned.shape import Direction  #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
from shadow4.syned.shape import Side       #  Side:  SOURCE = 0  IMAGE = 1

from shadow4.beamline.s4_optical_element import SurfaceCalculation # INTERNAL = 0  EXTERNAL = 1

from shadow4.beamline.optical_elements.mirrors.s4_conic_mirror import S4ConicMirror, S4ConicMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_toroidal_mirror import S4ToroidalMirror, S4ToroidalMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_surface_data_mirror import S4SurfaceDataMirror, S4SurfaceDataMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror, S4PlaneMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_ellipsoid_mirror import S4EllipsoidMirror, S4EllipsoidMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_hyperboloid_mirror import S4HyperboloidMirror, S4HyperboloidMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_paraboloid_mirror import S4ParaboloidMirror, S4ParaboloidMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_sphere_mirror import S4SphereMirror, S4SphereMirrorElement


from shadow4.tools.graphics import plotxy

from orangecontrib.shadow4.util.shadow_objects import ShadowBeam
from orangecontrib.shadow4.util.shadow_util import ShadowCongruence


class OWMirror(GenericElement, WidgetDecorator):

    name = "Generic Mirror"
    description = "Shadow Mirror"
    icon = "icons/plane_mirror.png"
    priority = 5

    inputs = [("Input Beam", ShadowBeam, "setBeam")]
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Beam4",
                "type":ShadowBeam,
                "doc":"",}]



    #########################################################
    # Position
    #########################################################
    source_plane_distance               = Setting(1.0)
    image_plane_distance                = Setting(1.0)
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

    #########################################################
    # reflectivity
    #########################################################

    reflectivity_flag             = Setting(0)  # f_reflec
    reflectivity_source           = Setting(0) # f_refl
    file_refl                     = Setting("<none>")

    refraction_index_delta        = Setting(1e-5)
    refraction_index_beta         = Setting(1e-3)

    #########################################################
    # dimensions
    #########################################################
    is_infinite  = Setting(0)
    mirror_shape = Setting(0)
    dim_x_plus   = Setting(1.0)
    dim_x_minus  = Setting(1.0)
    dim_y_plus   = Setting(1.0)
    dim_y_minus  = Setting(1.0)


    input_beam = None
    beamline = None


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


        tab_position = oasysgui.createTabPage(self.tabs_control_area, "Position")           # to be populated

        tab_basic_settings = oasysgui.createTabPage(self.tabs_control_area, "Basic Settings")
        tabs_basic_setting = oasysgui.tabWidget(tab_basic_settings)
        subtab_surface_shape = oasysgui.createTabPage(tabs_basic_setting, "Surface Shape")  # to be populated
        subtab_reflectivity = oasysgui.createTabPage(tabs_basic_setting, "Reflectivity")    # to be populated
        subtab_dimensions = oasysgui.createTabPage(tabs_basic_setting, "Dimensions")        # to be populated

        tab_advanced_settings = oasysgui.createTabPage(self.tabs_control_area, "Advanced Settings")
        tabs_advanced_settings = oasysgui.tabWidget(tab_advanced_settings)
        subtab_modified_surface = oasysgui.createTabPage(tabs_advanced_settings, "Modified Surface") # to be populated
        subtab_oe_movement= oasysgui.createTabPage(tabs_advanced_settings, "O.E. Movement")          # to be populated
        # subtab_source_movement = oasysgui.createTabPage(tabs_advanced_settings, "Source Movement")
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
        # Basic Settings / Reflectivity
        #########################################################
        self.populate_tab_reflectivity(subtab_reflectivity)

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

        #
        #
        #

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)


    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance", labelWidth=260,
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

        gui.comboBox(self.orientation_box, self, "mirror_orientation_angle", label="O.E. Orientation Angle [deg]",
                     labelWidth=390,
                     items=[0, 90, 180, 270, "Other value..."],
                     valueType=float,
                     sendSelectedValue=False, orientation="horizontal", callback=self.mirror_orientation_angle_user,
                     tooltip="mirror_orientation_angle" )
        self.mirror_orientation_angle_user_value_le = oasysgui.widgetBox(self.orientation_box, "", addSpace=False,
                                                                         orientation="vertical")
        oasysgui.lineEdit(self.mirror_orientation_angle_user_value_le, self, "mirror_orientation_angle_user_value",
                          "O.E. Orientation Angle [deg]",
                          labelWidth=220,
                          valueType=float, orientation="horizontal", tooltip="mirror_orientation_angle_user_value")

        self.mirror_orientation_angle_user()

    def populate_tab_surface_shape(self, subtab_surface_shape):

        box_1 = oasysgui.widgetBox(subtab_surface_shape, "Surface Shape", addSpace=True, orientation="vertical")

        gui.comboBox(box_1, self, "surface_shape_type", label="Figure",
                     labelWidth=390,
                     items=["Plane", "Sphere", "Ellipsoid", "Hyperboloid", "Paraboloid", "Toroid"],
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
                                                              "Object Side Focal Distance", labelWidth=260,
                                                              valueType=float, orientation="horizontal", tooltip="object_side_focal_distance")

        self.image_side_focal_distance_box = oasysgui.widgetBox(self.focusing_internal_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.image_side_focal_distance_box, self, "image_side_focal_distance",
                                                             "Image Side Focal Distance", labelWidth=260,
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
                                                     "Spherical Radius", labelWidth=260, valueType=float,
                                                     orientation="horizontal", tooltip="spherical_radius")
        # ellipsoid or hyperboloid
        self.focusing_external_ellipsoir_or_hyperboloid = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_ellipse_hyperbola_semi_major_axis = oasysgui.lineEdit(self.focusing_external_ellipsoir_or_hyperboloid, self,
                                                                      "ellipse_hyperbola_semi_major_axis",
                                                                      "Ellipse/Hyperbola semi-major Axis",
                                                                      labelWidth=260, valueType=float,
                                                                      orientation="horizontal", tooltip="ellipse_hyperbola_semi_major_axis")
        self.le_ellipse_hyperbola_semi_minor_axis = oasysgui.lineEdit(self.focusing_external_ellipsoir_or_hyperboloid, self,
                                                                      "ellipse_hyperbola_semi_minor_axis",
                                                                      "Ellipse/Hyperbola semi-minor Axis",
                                                                      labelWidth=260, valueType=float,
                                                                      orientation="horizontal", tooltip="ellipse_hyperbola_semi_minor_axis")
        oasysgui.lineEdit(self.focusing_external_ellipsoir_or_hyperboloid, self, "angle_of_majax_and_pole",
                          "Angle of MajAx and Pole [CCW, deg]", labelWidth=260, valueType=float,
                          orientation="horizontal", tooltip="angle_of_majax_and_pole")

        # paraboloid
        self.focusing_external_paraboloid = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_paraboloid_parameter = oasysgui.lineEdit(self.focusing_external_paraboloid, self, "paraboloid_parameter",
                                                         "Paraboloid parameter", labelWidth=260, valueType=float,
                                                         orientation="horizontal", tooltip="float")

        # toroid
        self.focusing_external_toroid = oasysgui.widgetBox(self.focusing_box, "", addSpace=False, orientation="vertical",
                                                         height=150)
        self.le_torus_major_radius = oasysgui.lineEdit(self.focusing_external_toroid, self, "torus_major_radius",
                                                       "Torus Major Radius", labelWidth=260, valueType=float,
                                                       orientation="horizontal", tooltip="torus_major_radius")
        self.le_torus_minor_radius = oasysgui.lineEdit(self.focusing_external_toroid, self, "torus_minor_radius",
                                                       "Torus Minor Radius", labelWidth=260, valueType=float,
                                                       orientation="horizontal", tooltip="torus_minor_radius")


        gui.comboBox(self.focusing_external_toroid, self, "toroidal_mirror_pole_location", label="Torus pole location",
                     labelWidth=145,
                     items=["lower/outer (concave/concave)",
                            "lower/inner (concave/convex)",
                            "upper/inner (convex/concave)",
                            "upper/outer (convex/convex)"],
                     sendSelectedValue=False, orientation="horizontal", tooltip="toroidal_mirror_pole_location")

        #
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

        self.surface_shape_tab_visibility()

    def populate_tab_reflectivity(self, subtab_reflectivity):

        # # f_reflec = 0    # reflectivity of surface: 0=no reflectivity, 1=full polarization
        # # f_refl   = 0    # 0=prerefl file
        # #                 # 1=electric susceptibility
        # #                 # 2=user defined file (1D reflectivity vs angle)
        # #                 # 3=user defined file (1D reflectivity vs energy)
        # #                 # 4=user defined file (2D reflectivity vs energy and angle)
        # # file_refl = "",  # preprocessor file fir f_refl=0,2,3,4
        # # refraction_index = 1.0,  # refraction index (complex) for f_refl=1


        box_1 = oasysgui.widgetBox(subtab_reflectivity, "Reflectivity Parameter", addSpace=True, orientation="vertical")

        gui.comboBox(box_1, self, "reflectivity_flag", label="Reflectivity", labelWidth=150,
                     items=["Not considered", "Full polarization"],
                     callback=self.reflectivity_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="reflectivity_flag")

        self.reflectivity_flag_box = oasysgui.widgetBox(box_1, "", addSpace=False, orientation="vertical")
        gui.comboBox(self.reflectivity_flag_box, self, "reflectivity_source", label="Reflectivity source", labelWidth=150,
                     items=["PreRefl File",
                            "Refraction index",
                            "file 1D: (reflectivity vs angle)",
                            "file 1D: (reflectivity vs energy)",
                            "file 2D: (reflectivity vs energy and angle)",
                            ],
                     callback=self.reflectivity_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="reflectivity_source")


        self.file_refl_box = oasysgui.widgetBox(self.reflectivity_flag_box, "", addSpace=False, orientation="horizontal", height=25)
        self.le_file_refl = oasysgui.lineEdit(self.file_refl_box, self, "file_refl", "File Name", labelWidth=100,
                                              valueType=str, orientation="horizontal", tooltip="file_refl")
        gui.button(self.file_refl_box, self, "...", callback=self.select_file_refl)


        self.refraction_index_box = oasysgui.widgetBox(self.reflectivity_flag_box, "", addSpace=False, orientation="horizontal", height=25)
        oasysgui.lineEdit(self.refraction_index_box, self, "refraction_index_delta",
                          "n=1-delta+i beta; delta: ", labelWidth=110, valueType=float,
                          orientation="horizontal", tooltip="refraction_index_delta")

        oasysgui.lineEdit(self.refraction_index_box, self, "refraction_index_beta",
                          "beta: ", labelWidth=30, valueType=float,
                          orientation="horizontal", tooltip="refraction_index_beta")

        self.reflectivity_tab_visibility()

    def populate_tab_dimensions(self, subtab_dimensions):
        dimension_box = oasysgui.widgetBox(subtab_dimensions, "Dimensions", addSpace=True, orientation="vertical")

        gui.comboBox(dimension_box, self, "is_infinite", label="Limits Check",
                     items=["Infinite o.e. dimensions", "Finite o.e. dimensions"],
                     callback=self.dimensions_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="is_infinite")

        self.dimdet_box = oasysgui.widgetBox(dimension_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.dimdet_box, self, "mirror_shape", label="Shape selected", labelWidth=260,
                     items=["Rectangular", "Full ellipse", "Ellipse with hole"],
                     sendSelectedValue=False, orientation="horizontal", tooltip="mirror_shape")

        self.le_dim_x_plus = oasysgui.lineEdit(self.dimdet_box, self, "dim_x_plus", "X(+) Half Width / Int Maj Ax",
                                               labelWidth=260, valueType=float, orientation="horizontal", tooltip="dim_x_plus")
        self.le_dim_x_minus = oasysgui.lineEdit(self.dimdet_box, self, "dim_x_minus", "X(-) Half Width / Int Maj Ax",
                                                labelWidth=260, valueType=float, orientation="horizontal", tooltip="dim_x_minus")
        self.le_dim_y_plus = oasysgui.lineEdit(self.dimdet_box, self, "dim_y_plus", "Y(+) Half Width / Int Min Ax",
                                               labelWidth=260, valueType=float, orientation="horizontal", tooltip="dim_y_plus")
        self.le_dim_y_minus = oasysgui.lineEdit(self.dimdet_box, self, "dim_y_minus", "Y(-) Half Width / Int Min Ax",
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

    def get_mirror_orientation_angle(self):
        if self.mirror_orientation_angle == 0:
            return 0.0
        elif self.mirror_orientation_angle == 1:
            return 90.0
        elif self.mirror_orientation_angle == 2:
            return 180.0
        elif self.mirror_orientation_angle == 3:
            return 270.0
        elif self.mirror_orientation_angle == 4:
            return self.mirror_orientation_angle_user_value




    #########################################################
    # Surface Shape Methods
    #########################################################
    def surface_shape_tab_visibility(self):

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
    def reflectivity_tab_visibility(self):

        self.reflectivity_flag_box.setVisible(False)
        self.file_refl_box.setVisible(False)
        self.refraction_index_box.setVisible(False)

        if self.reflectivity_flag == 1:
            self.reflectivity_flag_box.setVisible(True)

        if self.reflectivity_source in [0, 2, 3, 4]:
            self.file_refl_box.setVisible(True)
        else:
            self.refraction_index_box.setVisible(True)

    def select_file_refl(self):
        self.le_file_refl.setText(oasysgui.selectFileFromDialog(self, self.file_refl, "Select File with Reflectivity")) #, file_extension_filter="Data Files (*.dat)"))

    #########################################################
    # Dimensions Methods
    #########################################################

    def dimensions_tab_visibility(self):

        if self.is_infinite:
            self.dimdet_box.setVisible(True)
        else:
            self.dimdet_box.setVisible(False)

    #########################################################
    # S4 objects
    #########################################################

    def get_focusing_grazing_angle(self):
        if self.focii_and_continuation_plane == 0:
            return numpy.radians(90.0 - self.incidence_angle_deg)
        else:
            if self.incidence_angle_respect_to_normal_type:
                return numpy.radians(90.0 - self.incidence_angle_deg)
            else:
                return numpy.radians(self.incidence_angle_respect_to_normal)

    def get_focusing_p(self):
        if self.focii_and_continuation_plane == 0:
            return self.source_plane_distance
        else:
            return self.object_side_focal_distance

    def get_focusing_q(self):
        if self.focii_and_continuation_plane == 0:
            return self.image_plane_distance
        else:
            return self.image_side_focal_distance

    def get_boundary_shape(self):
        return None

    def get_mirror_instance(self):
        #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
        #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
        #  Side:  SOURCE = 0  IMAGE = 1


        if self.surface_shape_type == 0:
            mirror = S4PlaneMirror(
                name="Plane Mirror",
                boundary_shape=self.get_boundary_shape(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )
        elif self.surface_shape_type == 1:
            print("FOCUSING DISTANCES: convexity:  ", numpy.logical_not(self.surface_curvature).astype(int))
            print("FOCUSING DISTANCES: internal/external:  ", self.surface_shape_parameters)
            print("FOCUSING DISTANCES: radius:  ", self.spherical_radius)
            print("FOCUSING DISTANCES: p:  ", self.get_focusing_p())
            print("FOCUSING DISTANCES: q:  ", self.get_focusing_q())
            print("FOCUSING DISTANCES: grazing angle:  ", self.get_focusing_grazing_angle())

            mirror = S4SphereMirror(
                name="Sphere Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                radius=self.spherical_radius,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )

        elif self.surface_shape_type == 2:
            mirror = S4EllipsoidMirror(
                name="Ellipsoid Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                min_axis=0.0,
                maj_axis=0.0,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )
        elif self.surface_shape_type == 3:
            mirror = S4HyperboloidMirror(
                name="Hyperboloid Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                min_axis=0.0,
                maj_axis=0.0,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )
        elif self.surface_shape_type == 4:
            mirror = S4ParaboloidMirror(
                name="Paraboloid Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                parabola_parameter=0.0,
                at_infinity=Side.SOURCE, #  Side:  SOURCE = 0  IMAGE = 1
                pole_to_focus=None,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )
        elif self.surface_shape_type == 5:
            mirror = S4ToroidalMirror(
                name="Toroidal Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                min_radius=0.1,
                maj_radius=1.0,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )

        return mirror


    def get_coordinates(self):
        print(">>>>>>inc ref m.o.a. in deg:",self.incidence_angle_deg,self.reflection_angle_deg,self.get_mirror_orientation_angle())
        return ElementCoordinates(
                p=self.source_plane_distance,
                q=self.image_plane_distance,
                angle_radial=numpy.radians(self.incidence_angle_deg),
                angle_azimuthal=numpy.radians(self.get_mirror_orientation_angle()),
                angle_radial_out=numpy.radians(self.reflection_angle_deg),
                )

    def get_element_instance(self):

        if self.surface_shape_type == 0:
            optical_element = S4PlaneMirrorElement()
        elif self.surface_shape_type == 1:
            optical_element = S4SphereMirrorElement()
        elif self.surface_shape_type == 2:
            optical_element = S4EllipsoidMirrorElement()
        elif self.surface_shape_type == 3:
            optical_element = S4HyperboloidMirrorElement()
        elif self.surface_shape_type == 4:
            optical_element = S4ParaboloidMirrorElement()
        elif self.surface_shape_type == 5:
            optical_element = S4ToroidalMirrorElement()

        optical_element.set_optical_element(self.get_mirror_instance())
        optical_element.set_coordinates(self.get_coordinates())

        return optical_element


    def setBeam(self, input_beam):
        self.not_interactive = self.check_not_interactive_conditions(input_beam)

        self.onReceivingInput()

        if ShadowCongruence.checkEmptyBeam(input_beam):
            self.input_beam = input_beam
            self.beamline = input_beam.get_beamline()

            if self.is_automatic_run:
                self.run_shadow4()


    def run_shadow4(self):

        self.shadow_output.setText("")

        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        element = self.get_element_instance()
        print(element.info())

        self.progressBarInit()

        beam1, mirr1 = element.trace_beam(beam_in=self.input_beam._beam)

        beamline = self.beamline.duplicate()
        beamline.append_beamline_element(element)

        output_beam = ShadowBeam(oe_number=0, beam=beam1, beamline=beamline)

        self.set_PlotQuality()

        self.plot_results(output_beam, progressBarValue=80)

        self.progressBarFinished()

        #
        # script
        #
        script = beamline.to_python_code()
        script += "\n\n\n# run shadow4"
        script += "\nbeamline.run_beamline()"
        self.shadow4_script.set_code(script)

        #
        # send beam
        #
        self.send("Beam4", output_beam)

    def receive_syned_data(self, data):
        raise Exception("Not yet implemented")



if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline
    def get_test_beam():
        # electron beam
        from syned.storage_ring.light_source import ElectronBeam
        electron_beam = ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
        electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=3.63641e-06, sigma_xp=4.36821e-06,
                                     sigma_yp=1.37498e-06)

        # Gaussian undulator
        from shadow4.sources.undulator.s4_undulator import S4Undulator
        sourceundulator = S4Undulator(
            period_length=0.0159999,
            number_of_periods=100,
            emin=2700.136,
            emax=2700.136,
            flag_emittance=1,  # Use emittance (0=No, 1=Yes)
        )
        sourceundulator.set_energy_monochromatic(2700.14)

        from shadow4.sources.undulator.s4_undulator_light_source import S4UndulatorLightSource
        light_source = S4UndulatorLightSource(name='GaussianUndulator', electron_beam=electron_beam,
                                             magnetic_structure=sourceundulator)

        beam = light_source.get_beam_in_gaussian_approximation(NRAYS=5000, SEED=5676561)

        return ShadowBeam(oe_number=0, beam=beam, beamline=S4Beamline(light_source=light_source))

    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWMirror()
    ow.setBeam(get_test_beam())
    ow.show()
    a.exec_()
    ow.saveSettings()