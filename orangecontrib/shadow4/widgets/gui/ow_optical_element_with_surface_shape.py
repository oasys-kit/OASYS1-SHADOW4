import numpy
import sys, os

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5 import QtWidgets

from orangewidget import widget
from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import EmittingStream, read_surface_file

from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.shape import Rectangle
from syned.beamline.shape import Ellipse

from orangecontrib.shadow4.widgets.gui.ow_optical_element import OWOpticalElement
from orangecontrib.shadow4.util.shadow_objects import ShadowData
from orangecontrib.shadow4.util.shadow_util import ShadowCongruence

from orangecanvas.resources import icon_loader
from orangecanvas.scheme.node import SchemeNode


class OWOpticalElementWithSurfaceShape(OWOpticalElement):

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

    def __init__(self):
        super().__init__()

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
        dimension_box = oasysgui.widgetBox(subtab_dimensions, "Dimensions", addSpace=True, orientation="vertical")

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

        gui.comboBox(box, self, "modified_surface", label="Modification Type", labelWidth=260,
                     items=["None", "Surface Error (numeric mesh)"],
                     callback=self.modified_surface_tab_visibility, sendSelectedValue=False, orientation="horizontal")

        gui.separator(box, height=10)


        self.mod_surf_err_box_1 = oasysgui.widgetBox(box, "", addSpace=False,
                                                     orientation="horizontal")

        self.le_ms_defect_file_name = oasysgui.lineEdit(self.mod_surf_err_box_1, self, "ms_defect_file_name",
                                                        "File name", labelWidth=80, valueType=str,
                                                        orientation="horizontal")

        gui.button(self.mod_surf_err_box_1, self, "...", callback=self.select_defect_file_name)
        # gui.button(self.mod_surf_err_box_1, self, "View", callback=self.viewDefectFileName)

        self.modified_surface_tab_visibility()


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

    def congruence_surface_data_file(self):

        # check congruence of limits and ask for corrections
        surface_data_file = self.ms_defect_file_name

        if not os.path.isfile(surface_data_file):
            raise Exception("File %s not found." % surface_data_file)

        ask_for_fix = False
        if self.is_infinite:
            ask_for_fix = True
        else:
            if self.oe_shape != 0:
                ask_for_fix = True

        if ask_for_fix:
            xx, yy, zz = read_surface_file(surface_data_file)

            print(">>>> File limits: ", xx.min(), xx.max(), yy.min(), yy.max())
            print(">>>> Current limits: ", self.dim_x_minus, self.dim_x_plus, self.dim_y_minus, self.dim_x_plus)

            if (xx.min() > -self.dim_x_minus) or \
                    (xx.max() > self.dim_x_plus) or \
                    (yy.min() > -self.dim_y_minus) or \
                    (y.max() > self.dim_y_plus):
                if QtWidgets.QMessageBox.information(self, "Confirm Modification",
                                                     "Dimensions of this O.E. must be changed in order to ensure congruence with the error profile surface, accept?",
                                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
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


    #########################################################
    # Dimensions Methods
    #########################################################

    def dimensions_tab_visibility(self):

        if self.is_infinite: self.dimdet_box.setVisible(False)
        else:                self.dimdet_box.setVisible(True)

    #########################################################
    # Modified surface
    #########################################################

    def modified_surface_tab_visibility(self):
        if self.modified_surface: self.mod_surf_err_box_1.setVisible(True)
        else:                     self.mod_surf_err_box_1.setVisible(False)


    def select_defect_file_name(self):
        self.le_ms_defect_file_name.setText(oasysgui.selectFileFromDialog(self, self.ms_defect_file_name, "Select Defect File Name", file_extension_filter="Data Files (*.h5 *.hdf5)"))


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

        # if self.angles_respect_to == 0: # respect to normal
        #     angle_radial = self.incidence_angle_mrad * 1e-3
        #     angle_radial_out = self.reflection_angle_mrad * 1e-3
        # else:
        angle_radial = numpy.pi / 2 - self.incidence_angle_mrad * 1e-3
        angle_radial_out = numpy.pi / 2 - self.reflection_angle_mrad * 1e-3

        print(">>>>>>normal inc ref [deg]:", numpy.degrees(angle_radial), numpy.degrees(angle_radial_out),
              self.get_oe_orientation_angle())
        print(">>>>>>grazing inc ref [mrad]:", 1e3 * angle_radial, 1e3 * angle_radial_out,
              self.get_oe_orientation_angle())
        print(">>>>>>m.o.a. [deg]:", self.get_oe_orientation_angle())

        return ElementCoordinates(
                p=self.source_plane_distance,
                q=self.image_plane_distance,
                angle_radial=angle_radial,
                angle_azimuthal=numpy.radians(self.get_oe_orientation_angle()),
                angle_radial_out=angle_radial_out,
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
        script += "\n   plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)', plot_histograms=0)"
        script += "\n   plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')"
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
