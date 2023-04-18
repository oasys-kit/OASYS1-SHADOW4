import numpy
import sys, os

from PyQt5.QtWidgets import QDialog, QGridLayout, QWidget

from matplotlib import cm
from oasys.widgets.gui import FigureCanvas3D
from matplotlib.figure import Figure
try:    from mpl_toolkits.mplot3d import Axes3D  # plot 3D
except: pass

from orangecanvas.resources import icon_loader
from orangecanvas.scheme.node import SchemeNode

from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets.gui import ConfirmDialog, MessageDialog
from oasys.util.oasys_util import read_surface_file
from oasys.util.oasys_objects import OasysPreProcessorData

from syned.beamline.shape import Rectangle
from syned.beamline.shape import Ellipse

from srxraylib.metrology import profiles_simulation

from orangecontrib.shadow4.widgets.gui.ow_optical_element import OWOpticalElement, optical_element_inputs, SUBTAB_INNER_BOX_WIDTH

from shadow4.beamline.s4_beamline_element_movements import S4BeamlineElementMovements

class OWOpticalElementWithSurfaceShape(OWOpticalElement):
    inputs = optical_element_inputs()
    inputs.append(("PreProcessor Data", OasysPreProcessorData, "set_surface_data"))

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
    is_infinite  = Setting(1)
    oe_shape = Setting(0)
    dim_x_plus   = Setting(1.0)
    dim_x_minus  = Setting(1.0)
    dim_y_plus   = Setting(1.0)
    dim_y_minus  = Setting(1.0)

    #########################################################
    # modified surface
    #########################################################

    modified_surface = Setting(0)
    ms_defect_file_name = Setting("<none>.hdf5")

    #########################################################
    # o.e. movement
    #########################################################

    oe_movement            = Setting(0)
    oe_movement_offset_x   = Setting(0.0)
    oe_movement_rotation_x = Setting(0.0)
    oe_movement_offset_y   = Setting(0.0)
    oe_movement_rotation_y = Setting(0.0)
    oe_movement_offset_z   = Setting(0.0)
    oe_movement_rotation_z = Setting(0.0)


    input_data = None

    def createdFromNode(self, node):
        super(OWOpticalElementWithSurfaceShape, self).createdFromNode(node)
        self.__change_icon_from_surface_type()

    def widgetNodeAdded(self, node_item : SchemeNode):
        super(OWOpticalElementWithSurfaceShape, self).widgetNodeAdded(node_item)
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

    def __init__(self, show_automatic_box=True, has_footprint=True):
        super().__init__(show_automatic_box=show_automatic_box, has_footprint=has_footprint)

    def create_basic_settings_subtabs(self, tabs_basic_settings):
        subtab_surface_shape            = oasysgui.createTabPage(tabs_basic_settings, "Surface Shape")  # to be populated
        specific_basic_settings_subtabs = self.create_basic_settings_specific_subtabs(tabs_basic_settings)
        subtab_dimensions               = oasysgui.createTabPage(tabs_basic_settings, "Dimensions")        # to be populated

        return subtab_surface_shape, specific_basic_settings_subtabs, subtab_dimensions

    def create_advanced_settings_subtabs(self, tabs_advanced_settings):
        subtab_modified_surface = oasysgui.createTabPage(tabs_advanced_settings, "Modified Surface")  # to be populated

        return subtab_modified_surface

    def populate_basic_setting_subtabs(self, basic_setting_subtabs):
        subtab_surface_shape, specific_basic_settings_subtabs, subtab_dimensions = basic_setting_subtabs

        #########################################################
        # Basic Settings / Surface Shape
        #########################################################
        self.populate_tab_surface_shape(subtab_surface_shape)

        #########################################################
        # Specific SubTabs
        #########################################################
        self.populate_basic_settings_specific_subtabs(specific_basic_settings_subtabs)

        #########################################################
        # Basic Settings / Dimensions
        #########################################################
        self.populate_tab_dimensions(subtab_dimensions)

    def populate_advanced_setting_subtabs(self, advanced_setting_subtabs):
        subtab_modified_surface = advanced_setting_subtabs

        #########################################################
        # Advanced Settings / Modified Surface
        #########################################################
        self.populate_tab_modified_surface(subtab_modified_surface)

        #########################################################
        # Advanced Settings / O.E. Movement
        #########################################################
        self.populate_tab_oe_movement(subtab_modified_surface)

    def create_basic_settings_specific_subtabs(self, tabs_basic_setting): return None
    def populate_basic_settings_specific_subtabs(self, specific_basic_settings_subtabs): pass

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
        dimension_box = oasysgui.widgetBox(subtab_dimensions, "Dimensions", addSpace=True, orientation="vertical", width=SUBTAB_INNER_BOX_WIDTH)

        gui.comboBox(dimension_box, self, "is_infinite", label="Limits Check",
                     items=["Finite o.e. dimensions", "Infinite o.e. dimensions"],
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
        box = oasysgui.widgetBox(subtab_modified_surface, "Modified Surface Parameters", addSpace=True, orientation="vertical")

        # mod_surf_box = oasysgui.widgetBox(tab_adv_mod_surf, "Modified Surface Parameters", addSpace=False,
        #                                   orientation="vertical", height=390)

        gui.comboBox(box, self, "modified_surface", label="Modification Type", labelWidth=130,
                     items=["None", "Surface Error (numeric mesh)"],
                     callback=self.modified_surface_tab_visibility, sendSelectedValue=False, orientation="horizontal")

        gui.separator(box, height=10)


        self.mod_surf_err_box_1 = oasysgui.widgetBox(box, "", addSpace=False, orientation="horizontal")

        self.le_ms_defect_file_name = oasysgui.lineEdit(self.mod_surf_err_box_1, self, "ms_defect_file_name",
                                                        "File name", labelWidth=60, valueType=str,
                                                        orientation="horizontal")

        gui.button(self.mod_surf_err_box_1, self, "...", callback=self.select_defect_file_name, width=30)
        gui.button(self.mod_surf_err_box_1, self, "View", callback=self.view_surface_data_file, width=40)

        self.modified_surface_tab_visibility()

    def populate_tab_oe_movement(self, subtab_oe_movement):
        mir_mov_box = oasysgui.widgetBox(subtab_oe_movement, "O.E. Movement Parameters", addSpace=True, orientation="vertical")

        # mir_mov_box = oasysgui.widgetBox(tab_adv_mir_mov, "O.E. Movement Parameters", addSpace=False,
        #                                  orientation="vertical", height=230)

        gui.comboBox(mir_mov_box, self, "oe_movement", label="O.E. Movement", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.oe_movement_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="oe_movement")

        gui.separator(mir_mov_box, height=10)

        self.mir_mov_box_1 = oasysgui.widgetBox(mir_mov_box, "", addSpace=False, orientation="vertical")

        self.le_mm_mirror_offset_x = oasysgui.lineEdit(self.mir_mov_box_1, self, "oe_movement_offset_x", "O.E. Offset X [m]",
                                                       labelWidth=260, valueType=float, orientation="horizontal",
                                                       tooltip="oe_movement_offset_x")
        oasysgui.lineEdit(self.mir_mov_box_1, self, "oe_movement_rotation_x", "O.E. Rotation X [CCW, deg]",
                          labelWidth=260, valueType=float, orientation="horizontal",
                          tooltip="oe_movement_rotation_x")
        self.le_mm_mirror_offset_y = oasysgui.lineEdit(self.mir_mov_box_1, self, "oe_movement_offset_y", "O.E. Offset Y [m]",
                                                       labelWidth=260, valueType=float, orientation="horizontal",
                                                       tooltip="oe_movement_offset_y")
        oasysgui.lineEdit(self.mir_mov_box_1, self, "oe_movement_rotation_y", "O.E. Rotation Y [CCW, deg]",
                          labelWidth=260, valueType=float, orientation="horizontal",
                          tooltip="oe_movement_rotation_y")
        self.le_mm_mirror_offset_z = oasysgui.lineEdit(self.mir_mov_box_1, self, "oe_movement_offset_z", "O.E. Offset Z [m]",
                                                       labelWidth=260, valueType=float, orientation="horizontal",
                                                       tooltip="oe_movement_offset_z")
        oasysgui.lineEdit(self.mir_mov_box_1, self, "oe_movement_rotation_z", "O.E. Rotation Z [CCW, deg]",
                          labelWidth=260, valueType=float, orientation="horizontal",
                          tooltip="oe_movement_rotation_z")

        self.oe_movement_tab_visibility()

    def oe_movement_tab_visibility(self):
        self.mir_mov_box_1.setVisible(self.oe_movement == 1)

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

            self.cylinder_orientation_box.setVisible(self.is_cylinder==1)
        elif self.surface_shape_type == 6:
            self.ccc_box.setVisible(True)

        if not is_init: self.__change_icon_from_surface_type()

    def set_surface_data(self, oasys_data : OasysPreProcessorData):
        if not oasys_data is None:
            if not oasys_data.error_profile_data is None:
                try:
                    surface_data = oasys_data.error_profile_data.surface_data

                    error_profile_x_dim = oasys_data.error_profile_data.error_profile_x_dim
                    error_profile_y_dim = oasys_data.error_profile_data.error_profile_y_dim

                    self.ms_defect_file_name = surface_data.surface_data_file
                    self.modified_surface = 1
                    self.modified_surface_tab_visibility()

                    self.congruence_surface_data_file(surface_data.xx, surface_data.yy, surface_data.zz)
                except Exception as exception:
                    self.prompt_exception(exception)

    def congruence_surface_data_file(self, xx=None, yy=None, zz=None):
        # check congruence of limits and ask for corrections
        surface_data_file = self.ms_defect_file_name

        if not os.path.isfile(surface_data_file): raise Exception("File %s not found." % surface_data_file)

        ask_for_fix = False
        if self.is_infinite == 1:
            ask_for_fix = True
        else:
            if self.oe_shape != 0:
                ask_for_fix = True

        if ask_for_fix:
            if xx is None or yy is None or zz is None: xx, yy, zz = read_surface_file(surface_data_file)

            print(">>>> File limits: ", xx.min(), xx.max(), yy.min(), yy.max())
            print(">>>> Current limits: ", self.dim_x_minus, self.dim_x_plus, self.dim_y_minus, self.dim_x_plus)

            if (xx.min() > -self.dim_x_minus) or \
                    (xx.max() > self.dim_x_plus) or \
                    (yy.min() > -self.dim_y_minus) or \
                    (yy.max() > self.dim_y_plus):
                if ConfirmDialog.confirmed(parent=self,
                                           message="Dimensions of this O.E. must be changed in order to ensure congruence with the error profile surface, accept?",
                                           title="Confirm Modification",
                                           width=600):
                    self.is_infinite = 0
                    self.oe_shape = 0
                    self.dim_x_minus = numpy.min((-xx.min(), self.dim_x_minus))
                    self.dim_x_plus = numpy.min((xx.max(), self.dim_x_plus))
                    self.dim_y_minus = numpy.min((-yy.min(), self.dim_y_minus))
                    self.dim_y_plus = numpy.min((yy.max(), self.dim_y_plus))

                    print(">>>> NEW limits: ", self.dim_x_minus, self.dim_x_plus, self.dim_y_minus, self.dim_x_plus)

                    self.dimensions_tab_visibility()
                else:
                    print(">>>> **NOT CHANGED** limits: ", self.dim_x_minus, self.dim_x_plus, self.dim_y_minus, self.dim_x_plus)

    def view_surface_data_file(self):
        try:
            dialog = self.ShowSurfaceDataFileDialog(parent=self, surface_data_file=self.ms_defect_file_name)
            dialog.show()
        except Exception as exception:
            self.prompt_exception(exception)

    #########################################################
    # Dimensions Methods
    #########################################################

    def dimensions_tab_visibility(self):
        self.dimdet_box.setVisible(self.is_infinite==0)

    #########################################################
    # Modified surface
    #########################################################

    def modified_surface_tab_visibility(self):
        self.mod_surf_err_box_1.setVisible(self.modified_surface == 1)

    def select_defect_file_name(self):
        self.le_ms_defect_file_name.setText(oasysgui.selectFileFromDialog(self, self.ms_defect_file_name, "Select Defect File Name", file_extension_filter="Data Files (*.h5 *.hdf5)"))

    #########################################################
    # Movements methods
    #########################################################
    def get_movements_instance(self):
        if self.oe_movement == 0:
            return None
        else:
            return S4BeamlineElementMovements(f_move=1,
                                              offset_x=self.oe_movement_offset_x,
                                              offset_y=self.oe_movement_offset_y,
                                              offset_z=self.oe_movement_offset_z,
                                              rotation_x=numpy.radians(self.oe_movement_rotation_x),
                                              rotation_y=numpy.radians(self.oe_movement_rotation_y),
                                              rotation_z=numpy.radians(self.oe_movement_rotation_z),
                                              )
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


    class ShowSurfaceDataFileDialog(QDialog):

        def __init__(self, parent=None, surface_data_file=""):
            QDialog.__init__(self, parent)
            self.setWindowTitle('Surface Error Profile')
            self.setFixedHeight(700)
            layout = QGridLayout(self)

            figure = Figure(figsize=(8, 7))
            figure.patch.set_facecolor('white')

            axis = figure.add_subplot(111, projection='3d')
            axis.set_xlabel("X [m]")
            axis.set_ylabel("Y [m]")
            axis.set_zlabel("Z [nm]")

            figure_canvas = FigureCanvas3D(ax=axis, fig=figure, show_legend=False, show_buttons=False)
            figure_canvas.setFixedWidth(500)
            figure_canvas.setFixedHeight(645)

            xx, yy, zz = read_surface_file(surface_data_file)

            x_to_plot, y_to_plot = numpy.meshgrid(xx, yy)
            zz_slopes = zz.T

            axis.plot_surface(x_to_plot, y_to_plot,  zz*1e9, rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            sloperms = profiles_simulation.slopes(zz_slopes, xx, yy, return_only_rms=1)

            title = ' Slope error rms in X direction: %f $\mu$rad' % (sloperms[0]*1e6) + '\n' + \
                    ' Slope error rms in Y direction: %f $\mu$rad' % (sloperms[1]*1e6) + '\n' + \
                    ' Figure error rms in X direction: %f nm' % (round(zz_slopes[:, 0].std()*1e9, 6)) + '\n' + \
                    ' Figure error rms in Y direction: %f nm' % (round(zz_slopes[0, :].std()*1e9, 6))

            axis.set_title(title)
            figure_canvas.draw()
            axis.mouse_init()

            widget = QWidget(parent=self)
            container = oasysgui.widgetBox(widget, "", addSpace=False, orientation="horizontal", width=500)
            #gui.button(container, self, "Export Surface (.dat)", callback=self.save_shadow_surface)
            #gui.button(container, self, "Export Surface (.hdf5)", callback=self.save_oasys_surface)
            gui.button(container, self, "Close", callback=self.accept)

            layout.addWidget(figure_canvas, 0, 0)
            layout.addWidget(widget, 1, 0)

            self.setLayout(layout)