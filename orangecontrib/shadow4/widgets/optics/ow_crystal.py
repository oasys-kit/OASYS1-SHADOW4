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

from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.shape import Rectangle
from syned.beamline.shape import Convexity  #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
from syned.beamline.shape import Direction  #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
from syned.beamline.shape import Side       #  Side:  SOURCE = 0  IMAGE = 1

from shadow4.beamline.s4_optical_element import SurfaceCalculation # INTERNAL = 0  EXTERNAL = 1

from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal, S4PlaneCrystalElement

from shadow4.tools.graphics import plotxy

from orangecontrib.shadow4.util.shadow_objects import ShadowBeam
from orangecontrib.shadow4.util.shadow_util import ShadowCongruence

from orangecanvas.resources import icon_loader
from orangecanvas.scheme.node import SchemeNode

import xraylib


class OWCrystal(GenericElement, WidgetDecorator):

    icons_for_type = {0 : "icons/plane_crystal.png",
                      1 : "icons/spherical_crystal.png",
                      2 : "icons/ellipsoid_crystal.png",
                      3 : "icons/hyperboloid_crystal.png",
                      4 : "icons/paraboloid_crystal.png",
                      5 : "icons/toroidal_crystal.png",}

    mirror_names = ["Generic Crystal",
                    "Plane Crystal",
                    "Spherical Crystal",
                    "Elliptical Crystal",
                    "Hyperbolical Crystal",
                    "Parabolical Crystal",
                    "Toroidal Crystal"]

    titles_for_type = {0 : mirror_names[1],
                       1 : mirror_names[2],
                       2 : mirror_names[3],
                       3 : mirror_names[4],
                       4 : mirror_names[5],
                       5 : mirror_names[6]}

    name = "Generic Crystal"
    description = "Shadow Crystal"
    icon = "icons/plane_crystal.png"

    priority = 15

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
    # crystal
    #########################################################

    # reflectivity_flag             = Setting(0)  # f_reflec
    # reflectivity_source           = Setting(0) # f_refl
    # file_refl                     = Setting("<none>")
    #
    # refraction_index_delta        = Setting(1e-5)
    # refraction_index_beta         = Setting(1e-3)

    diffraction_geometry = Setting(0)
    diffraction_calculation = Setting(0)
    file_diffraction_profile = Setting("diffraction_profile.dat")

    CRYSTALS = xraylib.Crystal_GetCrystalsList()

    user_defined_bragg_angle = Setting(14.223)
    user_defined_crystal = Setting(32)
    user_defined_h = Setting(1)
    user_defined_k = Setting(1)
    user_defined_l = Setting(1)
    user_defined_asymmetry_angle = Setting(0.0)
    file_crystal_parameters = Setting("bragg.dat")
    crystal_auto_setting = Setting(0)
    units_in_use = Setting(0)
    photon_energy = Setting(5.0)
    photon_wavelength = Setting(5000.0)

    mosaic_crystal = Setting(0)
    angle_spread_FWHM = Setting(0.0)
    thickness = Setting(0.0)
    seed_for_mosaic = Setting(1626261131)

    johansson_geometry = Setting(0)
    johansson_radius = Setting(0.0)

    asymmetric_cut = Setting(0)
    planes_angle = Setting(0.0)
    below_onto_bragg_planes = Setting(-1)

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
    beamline   = None

    def widgetNodeAdded(self, node_item : SchemeNode):
        super(GenericElement, self).widgetNodeAdded(node_item)

        self.__change_icon_from_surface_type(is_init=False)

    def __change_icon_from_surface_type(self, is_init):
        try:
            if not is_init:
                node = self.getNode()
                node.description.icon = self.icons_for_type[self.surface_shape_type]
                self.changeNodeIcon(icon_loader.from_description(node.description).get(node.description.icon))
                if node.title in self.mirror_names: self.changeNodeTitle(self.titles_for_type[self.surface_shape_type])
        except:
            pass

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
        # subtab_reflectivity = oasysgui.createTabPage(tabs_basic_setting, "Reflectivity")    # to be populated
        subtab_crystal_diffraction = oasysgui.createTabPage(tabs_basic_setting, "Xtal Diff")
        subtab_crystal_geometry = oasysgui.createTabPage(tabs_basic_setting, "Xtal Geom")
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
        # Basic Settings / Crystal Diffraction
        #########################################################
        self.populate_tab_crystal_diffraction(subtab_crystal_diffraction)

        #########################################################
        # Basic Settings / Crystal Geometry
        #########################################################
        self.populate_tab_crystal_geometry(subtab_crystal_geometry)

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

        self.__is_init = False

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

        self.surface_shape_tab_visibility(is_init=True)


        # box_1 = oasysgui.widgetBox(subtab_reflectivity, "Reflectivity Parameter", addSpace=True, orientation="vertical")
        #
        # gui.comboBox(box_1, self, "reflectivity_flag", label="Reflectivity", labelWidth=150,
        #              items=["Not considered", "Full polarization"],
        #              callback=self.reflectivity_tab_visibility, sendSelectedValue=False, orientation="horizontal",
        #              tooltip="reflectivity_flag")
        #
        # self.reflectivity_flag_box = oasysgui.widgetBox(box_1, "", addSpace=False, orientation="vertical")
        # gui.comboBox(self.reflectivity_flag_box, self, "reflectivity_source", label="Reflectivity source", labelWidth=150,
        #              items=["PreRefl File",
        #                     "Refraction index",
        #                     "file 1D: (reflectivity vs angle)",
        #                     "file 1D: (reflectivity vs energy)",
        #                     "file 2D: (reflectivity vs energy and angle)",
        #                     ],
        #              callback=self.reflectivity_tab_visibility, sendSelectedValue=False, orientation="horizontal",
        #              tooltip="reflectivity_source")
        #
        #
        # self.file_refl_box = oasysgui.widgetBox(self.reflectivity_flag_box, "", addSpace=False, orientation="horizontal", height=25)
        # self.le_file_refl = oasysgui.lineEdit(self.file_refl_box, self, "file_refl", "File Name", labelWidth=100,
        #                                       valueType=str, orientation="horizontal", tooltip="file_refl")
        # gui.button(self.file_refl_box, self, "...", callback=self.select_file_refl)
        #
        #
        # self.refraction_index_box = oasysgui.widgetBox(self.reflectivity_flag_box, "", addSpace=False, orientation="horizontal", height=25)
        # oasysgui.lineEdit(self.refraction_index_box, self, "refraction_index_delta",
        #                   "n=1-delta+i beta; delta: ", labelWidth=110, valueType=float,
        #                   orientation="horizontal", tooltip="refraction_index_delta")
        #
        # oasysgui.lineEdit(self.refraction_index_box, self, "refraction_index_beta",
        #                   "beta: ", labelWidth=30, valueType=float,
        #                   orientation="horizontal", tooltip="refraction_index_beta")
        #
        # self.reflectivity_tab_visibility()

    def populate_tab_crystal_diffraction(self, subtab_crystal_diffraction):
        crystal_box = oasysgui.widgetBox(subtab_crystal_diffraction, "Diffraction Settings", addSpace=True, orientation="vertical")

        # crystal_box = oasysgui.widgetBox(self.tab_cryst_1, "Diffraction Parameters", addSpace=True,
        #                                  orientation="vertical", height=435)

        gui.comboBox(crystal_box, self, "diffraction_geometry", label="Diffraction Geometry", labelWidth=250,
                     items=["Bragg", "Laue"],
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_BraggLaue)

        gui.comboBox(crystal_box, self, "diffraction_calculation", label="Diffraction Profile", labelWidth=250,
                     items=["Calculated internally", "Preprocessor file", "User File (energy-independent)", "User File (energy-dependent)"],
                     sendSelectedValue=False, orientation="horizontal",
                     callback=self.set_DiffractionCalculation)

        gui.separator(crystal_box)

        self.crystal_box_1 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical", height=340)

        file_box = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=False, orientation="horizontal", height=30)

        self.le_file_crystal_parameters = oasysgui.lineEdit(file_box, self, "file_crystal_parameters",
                                                            "File with crystal\nparameters",
                                                            labelWidth=150, valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.selectFileCrystalParameters)

        gui.comboBox(self.crystal_box_1, self, "crystal_auto_setting", label="Auto setting", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_Autosetting, sendSelectedValue=False, orientation="horizontal")

        gui.separator(self.crystal_box_1, height=10)

        self.autosetting_box = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=False,
                                                  orientation="vertical")
        self.autosetting_box_empty = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=False,
                                                        orientation="vertical")

        self.autosetting_box_units = oasysgui.widgetBox(self.autosetting_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.autosetting_box_units, self, "units_in_use", label="Units in use", labelWidth=260,
                     items=["eV", "Angstroms"],
                     callback=self.set_UnitsInUse, sendSelectedValue=False, orientation="horizontal")

        self.autosetting_box_units_1 = oasysgui.widgetBox(self.autosetting_box_units, "", addSpace=False,
                                                          orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_1, self, "photon_energy", "Set photon energy [eV]", labelWidth=260,
                          valueType=float, orientation="horizontal")

        self.autosetting_box_units_2 = oasysgui.widgetBox(self.autosetting_box_units, "", addSpace=False,
                                                          orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_2, self, "photon_wavelength", "Set wavelength [Å]", labelWidth=260,
                          valueType=float, orientation="horizontal")

        self.crystal_box_2 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical", height=340)

        crystal_box_2_1 = oasysgui.widgetBox(self.crystal_box_2, "", addSpace=False, orientation="horizontal")

        self.le_file_diffraction_profile = oasysgui.lineEdit(crystal_box_2_1, self, "file_diffraction_profile",
                                                             "File with Diffraction\nProfile (XOP format)", labelWidth=120,
                                                             valueType=str,
                                                             orientation="horizontal")

        gui.button(crystal_box_2_1, self, "...", callback=self.selectFileDiffractionProfile)

    def populate_tab_crystal_geometry(self, subtab_crystal_geometry):
        mosaic_box = oasysgui.widgetBox(subtab_crystal_geometry, "Geometric Parameters", addSpace=True, orientation="vertical")

        gui.comboBox(mosaic_box, self, "mosaic_crystal", label="Mosaic Crystal", labelWidth=355,
                     items=["No", "Yes"],
                     callback=self.set_Mosaic, sendSelectedValue=False, orientation="horizontal")

        gui.separator(mosaic_box, height=10)

        self.mosaic_box_1 = oasysgui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")

        self.asymmetric_cut_box = oasysgui.widgetBox(self.mosaic_box_1, "", addSpace=False, orientation="vertical",
                                                     height=110)

        self.asymmetric_cut_combo = gui.comboBox(self.asymmetric_cut_box, self, "asymmetric_cut", label="Asymmetric cut",
                                                 labelWidth=355,
                                                 items=["No", "Yes"],
                                                 callback=self.set_AsymmetricCut, sendSelectedValue=False,
                                                 orientation="horizontal")

        self.asymmetric_cut_box_1 = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False, orientation="vertical")
        self.asymmetric_cut_box_1_empty = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False,
                                                             orientation="vertical")

        oasysgui.lineEdit(self.asymmetric_cut_box_1, self, "planes_angle", "Planes angle [deg]", labelWidth=260,
                          valueType=float, orientation="horizontal")

        self.asymmetric_cut_box_1_order = oasysgui.widgetBox(self.asymmetric_cut_box_1, "", addSpace=False,
                                                             orientation="vertical")

        oasysgui.lineEdit(self.asymmetric_cut_box_1_order, self, "below_onto_bragg_planes",
                          "Below[-1]/onto[1] bragg planes", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_thickness_1 = oasysgui.lineEdit(self.asymmetric_cut_box_1_order, self, "thickness", "Thickness",
                                                valueType=float, labelWidth=260, orientation="horizontal")

        self.set_BraggLaue()

        gui.separator(self.mosaic_box_1)

        self.johansson_box = oasysgui.widgetBox(self.mosaic_box_1, "", addSpace=False, orientation="vertical", height=100)

        gui.comboBox(self.johansson_box, self, "johansson_geometry", label="Johansson Geometry", labelWidth=355,
                     items=["No", "Yes"],
                     callback=self.set_JohanssonGeometry, sendSelectedValue=False, orientation="horizontal")

        self.johansson_box_1 = oasysgui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")
        self.johansson_box_1_empty = oasysgui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")

        self.le_johansson_radius = oasysgui.lineEdit(self.johansson_box_1, self, "johansson_radius", "Johansson radius",
                                                     labelWidth=260, valueType=float, orientation="horizontal")

        self.mosaic_box_2 = oasysgui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.mosaic_box_2, self, "angle_spread_FWHM", "Angle spread FWHM [deg]", labelWidth=260,
                          valueType=float, orientation="horizontal")
        self.le_thickness_2 = oasysgui.lineEdit(self.mosaic_box_2, self, "thickness", "Thickness", labelWidth=260,
                                                valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mosaic_box_2, self, "seed_for_mosaic", "Seed for mosaic [>10^5]", labelWidth=260,
                          valueType=float, orientation="horizontal")

        self.set_Mosaic()


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

        self.__change_icon_from_surface_type(is_init)

    #########################################################
    # Crystal Methods
    #########################################################
    # def reflectivity_tab_visibility(self):
    #
    #     self.reflectivity_flag_box.setVisible(False)
    #     self.file_refl_box.setVisible(False)
    #     self.refraction_index_box.setVisible(False)
    #
    #     if self.reflectivity_flag == 1:
    #         self.reflectivity_flag_box.setVisible(True)
    #
    #     if self.reflectivity_source in [0, 2, 3, 4]:
    #         self.file_refl_box.setVisible(True)
    #     else:
    #         self.refraction_index_box.setVisible(True)
    #
    # def select_file_refl(self):
    #     self.le_file_refl.setText(oasysgui.selectFileFromDialog(self, self.file_refl, "Select File with Reflectivity")) #, file_extension_filter="Data Files (*.dat)"))

    def set_BraggLaue(self):
        self.asymmetric_cut_box_1_order.setVisible(self.diffraction_geometry==1) #LAUE
        if self.diffraction_geometry==1:
            self.asymmetric_cut = 1
            self.set_AsymmetricCut()
            self.asymmetric_cut_combo.setEnabled(False)
        else:
            self.asymmetric_cut_combo.setEnabled(True)

    def set_DiffractionCalculation(self):
        # todo: reimplement this
        # self.tab_cryst_2.setEnabled(self.diffraction_calculation == 0)

        self.crystal_box_1.setVisible(self.diffraction_calculation == 1)

        self.crystal_box_2.setVisible(self.diffraction_calculation in (0,2))

        if (self.diffraction_calculation == 2):
            self.incidence_angle_deg_le.setEnabled(True)
            self.incidence_angle_rad_le.setEnabled(True)
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)
        else:
            self.set_Autosetting()

    def selectFileCrystalParameters(self):
        self.le_file_crystal_parameters.setText(oasysgui.selectFileFromDialog(self, self.file_crystal_parameters, "Select File With Crystal Parameters"))

    def set_Autosetting(self):
        self.autosetting_box_empty.setVisible(self.crystal_auto_setting == 0)
        self.autosetting_box.setVisible(self.crystal_auto_setting == 1)

        if self.crystal_auto_setting == 0:
            self.incidence_angle_deg_le.setEnabled(True)
            self.incidence_angle_rad_le.setEnabled(True)
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)
        else:
            self.incidence_angle_deg_le.setEnabled(False)
            self.incidence_angle_rad_le.setEnabled(False)
            self.reflection_angle_deg_le.setEnabled(False)
            self.reflection_angle_rad_le.setEnabled(False)
            self.set_UnitsInUse()

    def set_UnitsInUse(self):
        self.autosetting_box_units_1.setVisible(self.units_in_use == 0)
        self.autosetting_box_units_2.setVisible(self.units_in_use == 1)

    def selectFileDiffractionProfile(self):
        self.le_file_diffraction_profile.setText(oasysgui.selectFileFromDialog(self, self.file_diffraction_profile, "Select File With User Defined Diffraction Profile"))


    def set_Mosaic(self):
        self.mosaic_box_1.setVisible(self.mosaic_crystal == 0)
        self.mosaic_box_2.setVisible(self.mosaic_crystal == 1)

        if self.mosaic_crystal == 0:
            self.set_AsymmetricCut()
            self.set_JohanssonGeometry()

    def set_AsymmetricCut(self):
        self.asymmetric_cut_box_1.setVisible(self.asymmetric_cut == 1)
        self.asymmetric_cut_box_1_empty.setVisible(self.asymmetric_cut == 0)

    def set_JohanssonGeometry(self):
        self.johansson_box_1.setVisible(self.johansson_geometry == 1)
        self.johansson_box_1_empty.setVisible(self.johansson_geometry == 0)

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
            mirror = S4PlaneCrystal(
                name="Plane Mirror",
                boundary_shape=self.get_boundary_shape(), # todo: add kws...
            )
        elif self.surface_shape_type == 1:
            print("FOCUSING DISTANCES: convexity:  ", numpy.logical_not(self.surface_curvature).astype(int))
            print("FOCUSING DISTANCES: internal/external:  ", self.surface_shape_parameters)
            print("FOCUSING DISTANCES: radius:  ", self.spherical_radius)
            print("FOCUSING DISTANCES: p:  ", self.get_focusing_p())
            print("FOCUSING DISTANCES: q:  ", self.get_focusing_q())
            print("FOCUSING DISTANCES: grazing angle:  ", self.get_focusing_grazing_angle())

            raise NotImplementedError

        else:
            raise NotImplementedError

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
            optical_element = S4PlaneCrystalElement()
        else:
            raise NotImplementedError
        # elif self.surface_shape_type == 1:
        #     optical_element = S4SphereMirrorElement()
        # elif self.surface_shape_type == 2:
        #     optical_element = S4EllipsoidMirrorElement()
        # elif self.surface_shape_type == 3:
        #     optical_element = S4HyperboloidMirrorElement()
        # elif self.surface_shape_type == 4:
        #     optical_element = S4ParaboloidMirrorElement()
        # elif self.surface_shape_type == 5:
        #     optical_element = S4ToroidalMirrorElement()

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
        pass

        self.shadow_output.setText("")

        # sys.stdout = EmittingStream(textWritten=self.writeStdOut)
        #
        # element = self.get_element_instance()
        # print(element.info())
        #
        # self.progressBarInit()
        #
        # beam1, mirr1 = element.trace_beam(beam_in=self.input_beam._beam)
        #
        # beamline = self.beamline.duplicate()
        # beamline.append_beamline_element(element)
        #
        # output_beam = ShadowBeam(oe_number=0, beam=beam1, beamline=beamline)
        #
        # self.set_PlotQuality()
        #
        # self.plot_results(output_beam, progressBarValue=80)
        #
        # self.progressBarFinished()
        #
        # #
        # # script
        # #
        # script = beamline.to_python_code()
        # script += "\n\n\n# test plot"
        # script += "\nif True:"
        # script += "\n   from srxraylib.plot.gol import plot_scatter"
        # script += "\n   rays = beam.get_rays()"
        # script += "\n   plot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 2], title='(X,Z) in microns')"
        # self.shadow4_script.set_code(script)
        #
        # #
        # # send beam
        # #
        # self.send("Beam4", output_beam)

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
                                             magnetic_structure=sourceundulator, nrays=5000, seed=5676561)

        beam = light_source.get_beam_in_gaussian_approximation()

        return ShadowBeam(oe_number=0, beam=beam, beamline=S4Beamline(light_source=light_source))

    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWCrystal()
    ow.setBeam(get_test_beam())
    ow.show()
    a.exec_()
    ow.saveSettings()
