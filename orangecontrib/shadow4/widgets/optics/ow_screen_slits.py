import numpy

from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui

from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.shape import Rectangle
from syned.beamline.shape import Ellipse

from shadow4.beamline.optical_elements.absorbers.s4_screen import S4ScreenElement, S4Screen

from orangecontrib.shadow4.widgets.gui.ow_optical_element import OWOpticalElement, NO_FILE_SPECIFIED

from orangecanvas.resources import icon_loader
from orangecanvas.scheme.node import SchemeNode


class OWScreenSlits(OWOpticalElement):
    name        = "Generic Beam Screen/Slit/Stopper/Attenuator"
    description = "Shadow Screen/Slit/Stopper/Attenuator"
    icon        = "icons/generic_beam_stopper.png"

    priority = 1.1

    aperturing           = Setting(0)
    open_slit_solid_stop = Setting(0)
    aperture_shape       = Setting(0)
    absorption           = Setting(0)
    slit_width_xaxis     = Setting(0.0)
    slit_height_zaxis    = Setting(0.0)
    slit_center_xaxis    = Setting(0.0)
    slit_center_zaxis    = Setting(0.0)
    thickness            = Setting(0.0)
    opt_const_file_name  = Setting(NO_FILE_SPECIFIED)
    material             = Setting("Au")
    density              = Setting(19.3)

    def createdFromNode(self, node):
        super(OWScreenSlits, self).createdFromNode(node)
        self.__change_icon_from_oe_type()

    def widgetNodeAdded(self, node_item : SchemeNode):
        super(OWScreenSlits, self).widgetNodeAdded(node_item)
        self.__change_icon_from_oe_type()

    def __change_icon_from_oe_type(self):
        try:
            title, icon = self.title_and_icon_for_oe

            node = self.getNode()
            node.description.icon = icon
            self.changeNodeIcon(icon_loader.from_description(node.description).get(node.description.icon))
            if node.title in self.oe_names: self.changeNodeTitle(title)
        except:
            pass

    @property
    def oe_names(self):
        return ["Generic Beam Stopper", "Screen", "Aperture", "Obstruction", "Absorber", "Aperture/Absorber", "Obstruction/Absorber"]

    @property
    def title_and_icon_for_oe(self):
        if self.absorption == 0:
            if self.aperturing == 0: return self.oe_names[1], "icons/screen.png"
            elif self.aperturing == 1:
                if self.open_slit_solid_stop == 0: return self.oe_names[2], "icons/aperture_only.png"
                else:                              return self.oe_names[3], "icons/obstruction_only.png"
        else:
            if self.aperturing == 0: return self.oe_names[4], "icons/absorber.png"
            elif self.aperturing == 1:
                if self.open_slit_solid_stop == 0: return self.oe_names[5], "icons/aperture_absorber.png"
                else:                              return self.oe_names[6], "icons/obstruction_absorber.png"

    def __init__(self):
        super().__init__(has_footprint=False)

    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="image_plane_distance")

    def create_basic_settings_subtabs(self, tabs_basic_settings):
        return oasysgui.createTabPage(tabs_basic_settings, "Beam Stopper Type")  # to be populated

    def populate_basic_setting_subtabs(self, basic_setting_subtabs):
        tab_beam_stopper_type = basic_setting_subtabs

        box_aperturing = oasysgui.widgetBox(tab_beam_stopper_type, "Screen/Slit Shape", addSpace=False, orientation="vertical", height=240)

        gui.comboBox(box_aperturing, self, "aperturing", label="Aperturing", labelWidth=350,
                     items=["No", "Yes"], tooltip="aperturing",
                     callback=self.set_aperturing, sendSelectedValue=False, orientation="horizontal")

        gui.separator(box_aperturing)

        self.box_aperturing_shape = oasysgui.widgetBox(box_aperturing, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.box_aperturing_shape, self, "open_slit_solid_stop", label="Open slit/Solid stop", labelWidth=260,
                     items=["aperture/slit", "obstruction/stop"], tooltip="open_slit_solid_stop",
                     callback=self.set_open_slit_solid_stop, sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.box_aperturing_shape, self, "aperture_shape", label="Aperture shape", labelWidth=260,
                     items=["Rectangular", "Ellipse"], tooltip="aperture_shape",
                     sendSelectedValue=False, orientation="horizontal")

        box_aperturing_shape = oasysgui.widgetBox(self.box_aperturing_shape, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(box_aperturing_shape, self, "slit_width_xaxis", "Slit width/x-axis   [m]", tooltip="slit_width_xaxis",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_aperturing_shape, self, "slit_height_zaxis", "Slit height/z-axis [m]", tooltip="slit_height_zaxis", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_aperturing_shape, self, "slit_center_xaxis", "Slit center/x-axis [m]", tooltip="slit_center_xaxis", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_aperturing_shape, self, "slit_center_zaxis", "Slit center/z-axis [m]", tooltip="slit_center_zaxis", labelWidth=260, valueType=float, orientation="horizontal")

        box_absorption = oasysgui.widgetBox(tab_beam_stopper_type, "Absorption Parameters", addSpace=False, orientation="vertical", height=200)

        gui.comboBox(box_absorption, self, "absorption", label="Absorption", labelWidth=350,
                     items=["No", "Yes (using preprocessor file)", "Yes (using xraylib)", "Yes (using dabax)"],
                     tooltip="absorption",
                     callback=self.set_absorption, sendSelectedValue=False, orientation="horizontal")

        gui.separator(box_absorption)#, width=self.INNER_BOX_WIDTH_L0)
        self.box_thickness = oasysgui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.box_thickness, self, "thickness", "Thickness [m]", labelWidth=180, valueType=float,
                          tooltip="thickness", orientation="horizontal")

        self.box_absorption = oasysgui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.box_absorption, "", addSpace=False, orientation="horizontal", height=25)

        self.le_opt_const_file_name = oasysgui.lineEdit(file_box, self, "opt_const_file_name", "prerefl file",
                                                        tooltip="opt_const_file_name", labelWidth=130, valueType=str,
                                                        orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.select_opt_const_file_name)

        self.box_material = oasysgui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.box_material, self, "material",
                          "material (formula): ", labelWidth=180, valueType=str,
                          orientation="horizontal", tooltip="material")


        oasysgui.lineEdit(self.box_material, self, "density",
                          "density [g/cm^3]: ", labelWidth=180, valueType=float,
                          orientation="horizontal", tooltip="density")

        self.set_aperturing(is_init=True)
        self.set_absorption(is_init=True)

    def set_aperturing(self, is_init=False):
        self.box_aperturing_shape.setVisible(self.aperturing == 1)

        if not is_init: self.__change_icon_from_oe_type()

    def set_open_slit_solid_stop(self, is_init=False):
        if not is_init: self.__change_icon_from_oe_type()

    def set_absorption(self, is_init=False):
        #self.box_absorption_empty.setVisible(self.absorption == 0)
        self.box_thickness.setVisible(self.absorption >= 1)
        self.box_absorption.setVisible(self.absorption == 1)
        self.box_material.setVisible(self.absorption in (2,3))

        if not is_init: self.__change_icon_from_oe_type()

    def select_opt_const_file_name(self):
        self.le_opt_const_file_name.setText(oasysgui.selectFileFromDialog(self, self.opt_const_file_name, "Open Opt. Const. File"))

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

    def get_optical_element_instance(self):
        boundary_shape = None

        if self.aperturing == 1:
            if self.aperture_shape == 0:   boundary_shape = Rectangle(x_left=self.slit_center_xaxis - self.slit_width_xaxis*0.5,
                                                                      x_right=self.slit_center_xaxis + self.slit_width_xaxis*0.5,
                                                                      y_bottom=self.slit_center_zaxis - self.slit_height_zaxis*0.5,
                                                                      y_top=self.slit_center_zaxis + self.slit_height_zaxis*0.5)
            elif self.aperture_shape == 1: boundary_shape = Ellipse(a_axis_min=self.slit_center_xaxis - self.slit_width_xaxis*0.5,
                                                                    a_axis_max=self.slit_center_xaxis + self.slit_width_xaxis*0.5,
                                                                    b_axis_min=self.slit_center_zaxis - self.slit_height_zaxis*0.5,
                                                                    b_axis_max=self.slit_center_zaxis + self.slit_height_zaxis*0.5)

        return S4Screen(name=self.getNode().title,
                        boundary_shape=boundary_shape,
                        i_abs=self.absorption,
                        i_stop=self.open_slit_solid_stop==1,
                        thick=self.thickness,
                        file_abs=self.opt_const_file_name,
                        material=self.material,
                        density=self.density)

    def get_beamline_element_instance(self): return S4ScreenElement()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    a = QApplication(sys.argv)
    ow = OWScreenSlits()
    ow.show()
    a.exec_()
    ow.saveSettings()
