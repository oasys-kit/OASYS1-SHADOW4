import numpy
from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui

from syned.beamline.element_coordinates import ElementCoordinates

from shadow4.beamline.optical_elements.ideal_elements.s4_ideal_fzp import S4IdealFZPElement, S4IdealFZP

from orangecontrib.shadow4.widgets.gui.ow_optical_element import OWOpticalElement

class OWIdealFZP(OWOpticalElement):
    name        = "Ideal FZP"
    description = "Shadow Ideal FZP"
    icon        = "icons/ideal_fzp.png"

    priority = 3.3

    focusing_direction = Setting(3)
    focal = Setting(1.0)
    nominal_wavelength_A = Setting(1.54)  # nominal wavelength in m
    diameter_microns = Setting(500.0)  # FZP diameter

    def __init__(self):
        super().__init__(has_footprint=True)

    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="image_plane_distance")

    def create_basic_settings_subtabs(self, tabs_basic_settings):
        return oasysgui.createTabPage(tabs_basic_settings, "Ideal FZP Parameters")  # to be populated

    def populate_basic_setting_subtabs(self, basic_setting_subtabs):
        tab_ideal_fzp = basic_setting_subtabs

        box_ideal_fzp = oasysgui.widgetBox(tab_ideal_fzp, "", addSpace=False, orientation="vertical", height=180)

        gui.comboBox(box_ideal_fzp, self, "focusing_direction", label="Focusing direction", labelWidth=350,
                     items=["None", "1D: x (sagittal)", "1D: z (meridional)", "2D (radial)"],
                     sendSelectedValue=False,
                     orientation="horizontal",
                     tooltip="focusing_direction")

        gui.separator(box_ideal_fzp)

        oasysgui.lineEdit(box_ideal_fzp, self, "focal", "Design focal distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="focal")

        oasysgui.lineEdit(box_ideal_fzp, self, "nominal_wavelength_A", "Design nominal wavelengt [A]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="nominal_wavelength_A")

        oasysgui.lineEdit(box_ideal_fzp, self, "diameter_microns", "FZP diameter [microns]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="diameter_microns")

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
        except: name = "Ideal FZP"

        return S4IdealFZP(name=name,
                focusing_direction=self.focusing_direction,
                nominal_wavelength=self.nominal_wavelength_A * 1e-10,
                focal=self.focal,
                diameter=self.diameter_microns * 1e-6,
                )

    def get_beamline_element_instance(self):
        return S4IdealFZPElement()

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
    ow = OWIdealFZP()
    ow.set_shadow_data(get_test_beam())
    # ow.run_shadow4()

    ow.show()
    a.exec_()
    ow.saveSettings()
