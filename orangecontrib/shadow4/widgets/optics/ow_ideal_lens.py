import numpy
from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui

from syned.beamline.element_coordinates import ElementCoordinates

from shadow4.beamline.optical_elements.ideal_elements.s4_ideal_lens import S4IdealLensElement, S4SuperIdealLensElement, S4IdealLens, S4SuperIdealLens

from orangecontrib.shadow4.widgets.gui.ow_optical_element import OWOpticalElement

class OWIdealLens(OWOpticalElement):
    name        = "Ideal Lens"
    description = "Shadow Ideal Lens"
    icon        = "icons/ideal_lens.png"

    priority = 3.2

    focal_x    = Setting(0.0)
    focal_z    = Setting(0.0)

    focal_p_x    = Setting(0.0)
    focal_p_z    = Setting(0.0)
    focal_q_x    = Setting(0.0)
    focal_q_z    = Setting(0.0)

    ideal_lens_type = Setting(0)

    def __init__(self):
        super().__init__(has_footprint=False)

    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="image_plane_distance")

    def create_basic_settings_subtabs(self, tabs_basic_settings):
        return oasysgui.createTabPage(tabs_basic_settings, "Ideal Lens Parameters")  # to be populated

    def populate_basic_setting_subtabs(self, basic_setting_subtabs):
        tab_ideal_lens = basic_setting_subtabs

        box_ideal_lens = oasysgui.widgetBox(tab_ideal_lens, "", addSpace=False, orientation="vertical", height=180)

        gui.comboBox(box_ideal_lens, self, "ideal_lens_type", label="Ideal Lens Type", labelWidth=350,
                     items=["Simple", "Super"],
                     callback=self.set_ideal_lens_type, sendSelectedValue=False, orientation="horizontal",
                     tooltip="ideal_lens_type")

        gui.separator(box_ideal_lens)

        self.box_focal_distances = oasysgui.widgetBox(box_ideal_lens, "Focal Distances", addSpace=False, orientation="vertical", height=140)
        self.box_p_q_distances   = oasysgui.widgetBox(box_ideal_lens, "p,q Distances",   addSpace=False, orientation="vertical", height=140)

        oasysgui.lineEdit(self.box_focal_distances, self, "focal_x", "focal distance X [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="focal_x")
        oasysgui.lineEdit(self.box_focal_distances, self, "focal_z", "focal distance Z [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="focal_z")

        oasysgui.lineEdit(self.box_p_q_distances, self, "focal_p_x", "p(X) [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="focal_p_x")
        oasysgui.lineEdit(self.box_p_q_distances, self, "focal_p_z", "p(Z) [m]",
                          labelWidth=260, valueType=float, orientation="horizontal", tooltip="focal_p_z")
        oasysgui.lineEdit(self.box_p_q_distances, self, "focal_q_x", "q(X) [m]",
                          labelWidth=260, valueType=float, orientation="horizontal", tooltip="focal_q_x")
        oasysgui.lineEdit(self.box_p_q_distances, self, "focal_q_z", "q(Z) [m]",
                          labelWidth=260, valueType=float, orientation="horizontal", tooltip="focal_q_z")

        self.set_ideal_lens_type()

    def get_element_instance(self):
        if self.ideal_lens_type == 0:
            optical_element = S4IdealLensElement()

        else:
            optical_element = S4SuperIdealLensElement()
        optical_element.set_optical_element(self.get_oe_instance())
        # optical_element.set_coordinates()
        optical_element.set_input_beam(self.input_data.beam)
        return optical_element

    def get_oe_instance(self):
        try:    name = self.getNode().title
        except: name = "Ideal Lens"

        if self.ideal_lens_type == 0:
            return S4IdealLens(
                name=name, focal_x=self.focal_x, focal_y=self.focal_z)
        else:
            return S4SuperIdealLens(
                name=name, focal_x=self.focal_x, focal_y=self.focal_z)

    def set_ideal_lens_type(self):
        self.box_focal_distances.setVisible(self.ideal_lens_type == 0)
        self.box_p_q_distances.setVisible(self.ideal_lens_type == 1)

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
        try:    name = self.getNode().title
        except: name = "Ideal Lens"

        if self.ideal_lens_type == 0:   return S4IdealLens(name=name,
                                                           focal_x=self.focal_x,
                                                           focal_y=self.focal_z)
        elif self.ideal_lens_type == 1: return S4SuperIdealLens(name=name,
                                                                focal_p_x=self.focal_p_x,
                                                                focal_p_y=self.focal_p_z,
                                                                focal_q_x=self.focal_q_x,
                                                                focal_q_y=self.focal_q_z)

    def get_beamline_element_instance(self):
        if self.ideal_lens_type == 0:   return S4IdealLensElement()
        elif self.ideal_lens_type == 1: return S4SuperIdealLensElement()


if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline
    from orangecontrib.shadow4.util.shadow4_objects import ShadowData
    import sys
    def get_test_beam():
        from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
        light_source = SourceGeometrical(name='SourceGeometrical', nrays=5000, seed=5676561)
        light_source.set_spatial_type_rectangle(width=0.001000, height=0.001000)
        light_source.set_angular_distribution_flat(hdiv1=0.000000, hdiv2=0.000000, vdiv1=0.000000, vdiv2=0.000000)
        light_source.set_energy_distribution_singleline(5000.000000, unit='A')
        light_source.set_polarization(polarization_degree=1.000000, phase_diff=0.000000, coherent_beam=0)
        beam = light_source.get_beam()

        return ShadowData(beam=beam, beamline=S4Beamline(light_source=light_source))

    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWIdealLens()
    ow.set_shadow_data(get_test_beam())

    ow.source_plane_distance = 0
    ow.image_plane_distance = 5000.0
    ow.focal_x = 5000.0
    ow.focal_z = 5000.0
    ow.run_shadow4()

    ow.show()
    a.exec_()
    ow.saveSettings()
