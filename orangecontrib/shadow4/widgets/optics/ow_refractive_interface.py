from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui

from shadow4.beamline.optical_elements.refractors.s4_conic_interface import S4ConicInterface, S4ConicInterfaceElement

from orangecontrib.shadow4.widgets.gui.ow_optical_element_with_surface_shape import OWOpticalElementWithSurfaceShape

class OWRefractiveInterface(OWOpticalElementWithSurfaceShape):
    name        = "Refractive Interface"
    description = "Shadow Refractive Interface"
    icon        = "icons/interface.png"

    optical_constants_refraction_index = Setting(0)
    refraction_index_in_object_medium  = Setting(0.0)
    attenuation_in_object_medium       = Setting(0.0)
    file_prerefl_for_object_medium     = Setting("<none>")
    refractive_index_in_image_medium   = Setting(0.0)
    attenuation_in_image_medium        = Setting(0.0)
    file_prerefl_for_image_medium      = Setting("<none>")

    priority = 3.1

    def __init__(self):
        super().__init__(has_footprint=False, switch_icons=False)

    def create_basic_settings_specific_subtabs(self, tabs_basic_settings):
        return oasysgui.createTabPage(tabs_basic_settings, "Refractor")

    def populate_basic_settings_specific_subtabs(self, specific_basic_settings_subtabs):
        tab_bas_refractor = specific_basic_settings_subtabs

        refractor_box = oasysgui.widgetBox(tab_bas_refractor, "Optical Constants - Refractive Index", addSpace=False, orientation="vertical", height=320)

        gui.comboBox(refractor_box, self, "optical_constants_refraction_index", label="optical constants\n/refraction index", labelWidth=120,
                     items=["from constants in both media",
                            "from prerefl in OBJECT media",
                            "from prerefl in IMAGE media",
                            "from prerefl in both media"],
                     callback=self.set_refractor_optical_constants, sendSelectedValue=False, orientation="horizontal")

        gui.separator(refractor_box, height=10)
        self.refractor_object_box_1 = oasysgui.widgetBox(refractor_box, "OBJECT side", addSpace=False, orientation="vertical", height=100)
        oasysgui.lineEdit(self.refractor_object_box_1, self, "refraction_index_in_object_medium", "refraction index in object medium", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_attenuation_in_object_medium = oasysgui.lineEdit(self.refractor_object_box_1, self, "attenuation_in_object_medium", "attenuation in object medium", labelWidth=260, valueType=float, orientation="horizontal")

        self.refractor_object_box_2 = oasysgui.widgetBox(refractor_box, "OBJECT side", addSpace=False, orientation="horizontal", height=100)
        self.le_file_prerefl_for_object_medium = oasysgui.lineEdit(self.refractor_object_box_2, self, "file_prerefl_for_object_medium",
                                                                   "file prerefl for\nobject medium", labelWidth=120, valueType=str, orientation="horizontal")

        gui.button(self.refractor_object_box_2, self, "...", callback=self.select_prerefl_object_file_name)

        self.refractor_image_box_1 = oasysgui.widgetBox(refractor_box, "IMAGE side", addSpace=False, orientation="vertical", height=100)
        oasysgui.lineEdit(self.refractor_image_box_1, self, "refractive_index_in_image_medium", "refraction index in image medium", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_attenuation_in_image_medium = oasysgui.lineEdit(self.refractor_image_box_1, self, "attenuation_in_image_medium", "attenuation in image medium", labelWidth=260, valueType=float, orientation="horizontal")

        self.refractor_image_box_2 = oasysgui.widgetBox(refractor_box, "IMAGE side", addSpace=False, orientation="horizontal", height=100)
        self.le_file_prerefl_for_image_medium = oasysgui.lineEdit(self.refractor_image_box_2, self, "file_prerefl_for_image_medium",
                                                                  "file prerefl for\nimage medium", labelWidth=120, valueType=str, orientation="horizontal")

        gui.button(self.refractor_image_box_2, self, "...", callback=self.select_prerefl_image_file_name)

        self.set_refractor_optical_constants()

    def set_refractor_optical_constants(self):
        self.refractor_object_box_1.setVisible(self.optical_constants_refraction_index == 0 or self.optical_constants_refraction_index == 2)
        self.refractor_object_box_2.setVisible(self.optical_constants_refraction_index == 1 or self.optical_constants_refraction_index == 3)
        self.refractor_image_box_1.setVisible(self.optical_constants_refraction_index == 0 or self.optical_constants_refraction_index == 1)
        self.refractor_image_box_2.setVisible(self.optical_constants_refraction_index == 2 or self.optical_constants_refraction_index == 3)

    def select_prerefl_object_file_name(self):
        self.le_file_prerefl_for_object_medium.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl_for_object_medium, "Select File Prerefl for Object Medium"))

    def select_prerefl_image_file_name(self):
        self.le_file_prerefl_for_image_medium.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl_for_image_medium, "Select File Prerefl for Image Medium"))

    def populate_tab_surface_shape(self, subtab_surface_shape):
        box_interface = oasysgui.widgetBox(subtab_surface_shape, "Surface Shape Parameters", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(box_interface, self, "conic_coefficient_0", "c[1]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_interface, self, "conic_coefficient_1", "c[2]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_interface, self, "conic_coefficient_2", "c[3]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_interface, self, "conic_coefficient_3", "c[4]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_interface, self, "conic_coefficient_4", "c[5]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_interface, self, "conic_coefficient_5", "c[6]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_interface, self, "conic_coefficient_6", "c[7]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_interface, self, "conic_coefficient_7", "c[8]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_interface, self, "conic_coefficient_8", "c[9]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_interface, self, "conic_coefficient_9", "c[10]", labelWidth=260, valueType=float, orientation="horizontal")

        view_shape_box = oasysgui.widgetBox(subtab_surface_shape, "Calculated Surface Shape", addSpace=False, orientation="vertical")

        gui.button(view_shape_box, self, "Render Surface Shape", callback=self.view_surface_shape_data)

    def get_optical_element_instance(self):
        try:     name = self.getNode().title
        except:  name = "Refractive Interface"

        return S4ConicInterface(name=name,
                                boundary_shape=self.get_boundary_shape(),
                                material_object="",  # TODO: discuss with Manolo
                                material_image="", # TODO: discuss with Manolo
                                f_r_ind=self.optical_constants_refraction_index,
                                r_ind_obj=self.refraction_index_in_object_medium,
                                r_attenuation_obj=self.attenuation_in_object_medium,
                                file_r_ind_obj=self.file_prerefl_for_object_medium,
                                r_ind_ima=self.refractive_index_in_image_medium,
                                r_attenuation_ima=self.attenuation_in_image_medium,
                                file_r_ind_ima=self.file_prerefl_for_image_medium,
                                conic_coefficients=[self.conic_coefficient_0,
                                                    self.conic_coefficient_1,
                                                    self.conic_coefficient_2,
                                                    self.conic_coefficient_3,
                                                    self.conic_coefficient_4,
                                                    self.conic_coefficient_5,
                                                    self.conic_coefficient_6,
                                                    self.conic_coefficient_7,
                                                    self.conic_coefficient_8,
                                                    self.conic_coefficient_9])

    def get_beamline_element_instance(self): return S4ConicInterfaceElement()
