import numpy, copy

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from syned.beamline.element_coordinates import ElementCoordinates

from orangecontrib.shadow4.widgets.gui.ow_optical_element import OWOpticalElement
from orangecontrib.shadow4.util.shadow4_objects import PreReflPreProcessorData


class OWAbstractLens(OWOpticalElement):
    surface_shape           = Setting(2)
    convex_to_the_beam      = Setting(0)
    has_finite_diameter     = Setting(0)
    diameter                = Setting(632.0)
    is_cylinder             = Setting(0)
    cylinder_angle          = Setting(0.0)
    ri_calculation_mode     = Setting(0)
    prerefl_file            = Setting("<none>")
    refraction_index        = Setting(1.0)
    attenuation_coefficient = Setting(0.0)
    radius                  = Setting(100.0)
    interthickness          = Setting(30.0)

    inputs = copy.deepcopy(OWOpticalElement.inputs)
    inputs.append(("PreRefl PreProcessor Data", PreReflPreProcessorData, "set_PreReflPreProcessorData"))


    def __init__(self):
        super().__init__(has_footprint=False)

    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance to First Interface (P)", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Last Interface Distance to Image plane (Q)", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="image_plane_distance")

    def create_basic_settings_subtabs(self, tabs_basic_settings):
        return oasysgui.createTabPage(tabs_basic_settings, "Lens")  # to be populated

    def populate_basic_setting_subtabs(self, basic_setting_subtabs):
        lens_box = oasysgui.widgetBox(basic_setting_subtabs, "Lens Parameters", addSpace=False, orientation="vertical", height=370)

        gui.comboBox(lens_box, self, "has_finite_diameter", label="Lens Diameter", labelWidth=260,
                     items=["Finite", "Infinite"], callback=self.set_diameter, sendSelectedValue=False, orientation="horizontal")

        self.diameter_box = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")
        self.diameter_box_empty = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=24)

        oasysgui.lineEdit(self.diameter_box, self, "diameter", "Lens Diameter Value [\u03bcm]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_diameter()

        gui.comboBox(lens_box, self, "surface_shape", label="Surface Shape", labelWidth=260,
                     items=["Plane", "Sphere", "Paraboloid"], callback=self.set_surface_shape, sendSelectedValue=False, orientation="horizontal")

        self.surface_shape_box = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")
        self.surface_shape_box_empty = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=24)

        oasysgui.lineEdit(self.surface_shape_box, self, "radius", "Curvature Radius [\u03bcm]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_surface_shape()

        oasysgui.lineEdit(lens_box, self, "interthickness", "Lens Thickness [\u03bcm]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(lens_box, self, "convex_to_the_beam", label="1st interface exposed to the beam", labelWidth=310,
                     items=["Convex", "Concave"], sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(lens_box, self, "is_cylinder", label="Cylindrical", labelWidth=310,
                     items=["No", "Yes"], callback=self.set_cylindrical, sendSelectedValue=False, orientation="horizontal")

        self.box_cyl = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")
        self.box_cyl_empty = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=24)

        gui.comboBox(self.box_cyl, self, "cylinder_angle", label="Cylinder Angle (deg)", labelWidth=260,
                     items=["0 (Meridional)", "90 (Sagittal)"], sendSelectedValue=False, orientation="horizontal")

        self.set_cylindrical()

        gui.comboBox(lens_box, self, "ri_calculation_mode", label="Refraction Index calculation mode", labelWidth=260,
                     items=["User Parameters", "Prerefl File"], callback=self.set_ri_calculation_mode,
                     sendSelectedValue=False, orientation="horizontal")

        self.calculation_mode_1 = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.calculation_mode_1, self, "refraction_index", "Refraction index", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.calculation_mode_1, self, "attenuation_coefficient", "Attenuation coefficient [cm-1]", labelWidth=260, valueType=float, orientation="horizontal")

        self.calculation_mode_2 = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.calculation_mode_2, "", addSpace=True, orientation="horizontal")

        self.le_file_prerefl = oasysgui.lineEdit(file_box, self, "prerefl_file", "File Prerefl", labelWidth=100, valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.select_file_prerefl)

        self.set_ri_calculation_mode()

    def set_surface_shape(self):
        self.surface_shape_box.setVisible(self.surface_shape > 0)
        self.surface_shape_box_empty.setVisible(self.surface_shape == 0)

    def set_diameter(self):
        self.diameter_box.setVisible(self.has_finite_diameter == 0)
        self.diameter_box_empty.setVisible(self.has_finite_diameter == 1)

    def set_cylindrical(self):
        self.box_cyl.setVisible(self.is_cylinder == 1)
        self.box_cyl_empty.setVisible(self.is_cylinder == 0)

    def set_ri_calculation_mode(self):
        self.calculation_mode_1.setVisible(self.ri_calculation_mode == 0)
        self.calculation_mode_2.setVisible(self.ri_calculation_mode == 1)

    def select_file_prerefl(self):
        self.le_file_prerefl.setText(oasysgui.selectFileFromDialog(self, self.prerefl_file, "Select File Prerefl", file_extension_filter="Data Files (*.dat)"))

    def set_PreReflPreProcessorData(self, data):
        if data is not None:
            if data.prerefl_data_file != PreReflPreProcessorData.NONE:
                self.prerefl_file = data.prerefl_data_file
                self.le_file_prerefl.setText(self.prerefl_file)
                self.ri_calculation_mode = 1
                self.set_ri_calculation_mode()
            else:
                QMessageBox.warning(self, "Warning", "Incompatible Preprocessor Data", QMessageBox.Ok)

    # ----------------------------------------------------
    # from OpticalElement

    def get_coordinates_instance(self):
        return ElementCoordinates(
                p=self.source_plane_distance,
                q=self.image_plane_distance,
                angle_radial=0.0,
                angle_azimuthal=0.0,
                angle_radial_out=numpy.pi,
                )
