from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from syned.beamline.shape import Circle
from shadow4.beamline.optical_elements.refractors.s4_crl import S4CRL, S4CRLElement
from orangecontrib.shadow4.widgets.gui.ow_abstract_lens import OWAbstractLens

class OWCRL(OWAbstractLens):
    name = "Compound Refractive Lens"
    description = "Shadow Compound Refractive Lens"
    icon = "icons/crl.png"
    priority = 2.2

    n_lens                  = Setting(10)
    piling_thickness        = Setting(2.5)

    def __init__(self):
        super().__init__()

    def create_basic_settings_subtabs(self, tabs_basic_settings):
        return oasysgui.createTabPage(tabs_basic_settings, "CRL") # to be populated

    def populate_basic_setting_subtabs(self, basic_setting_subtabs):
        crl_box = oasysgui.widgetBox(basic_setting_subtabs, "CRL Parameters", addSpace=False, orientation="vertical", height=90)

        oasysgui.lineEdit(crl_box, self, "n_lens", "Number of lenses", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(crl_box, self, "piling_thickness", "Piling thickness [mm]", labelWidth=260, valueType=float, orientation="horizontal")

        super(OWCRL, self).populate_basic_setting_subtabs(basic_setting_subtabs)

    def get_optical_element_instance(self):
        try:    name = self.getNode().title
        except: name = "Compound Refractive Lens"

        um_to_si = 1e-6
        mm_to_si = 1e-3

        if self.has_finite_diameter == 0: boundary_shape = Circle(radius=um_to_si * self.diameter * 0.5)
        else:                             boundary_shape = None
        if self.is_cylinder == 1: cylinder_angle = self.cylinder_angle + 1
        else:                     cylinder_angle = 0

        return S4CRL(name=name,
                     n_lens=self.n_lens,
                     piling_thickness=self.piling_thickness*mm_to_si,
                     boundary_shape=boundary_shape,
                     material="", # not used
                     thickness=self.interthickness * um_to_si,
                     surface_shape=self.surface_shape,
                     convex_to_the_beam=self.convex_to_the_beam,
                     cylinder_angle=cylinder_angle,
                     ri_calculation_mode=self.ri_calculation_mode,
                     prerefl_file=self.prerefl_file,
                     refraction_index=self.refraction_index,
                     attenuation_coefficient=self.attenuation_coefficient,
                     radius=self.radius * um_to_si,
                     conic_coefficients=None)  # TODO: add conic coefficient shape to the GUI

    def get_beamline_element_instance(self):
        return S4CRLElement()
