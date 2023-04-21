from syned.beamline.shape import Circle
from shadow4.beamline.optical_elements.refractors.s4_lens import S4Lens, S4LensElement
from orangecontrib.shadow4.widgets.gui.ow_abstract_lens import OWAbstractLens

class OWLens(OWAbstractLens):
    name = "Refractive Lens"
    description = "Shadow Refractive Lens"
    icon = "icons/lens.png"
    priority = 2.1

    def __init__(self):
        super().__init__()

    # ----------------------------------------------------
    # from OpticalElement

    def get_optical_element_instance(self):
        try:    name = self.getNode().title
        except: name = "Refractive Lens"

        um_to_si = 1e-6

        if self.has_finite_diameter == 0: boundary_shape = Circle(radius=um_to_si*self.diameter*0.5)
        else:                             boundary_shape = None
        if self.is_cylinder == 1: cylinder_angle = self.cylinder_angle + 1
        else:                     cylinder_angle = 0

        return S4Lens(name=name,
                      boundary_shape=boundary_shape,
                      material="", # not used
                      thickness=self.interthickness*um_to_si,
                      surface_shape=self.surface_shape,
                      convex_to_the_beam=self.convex_to_the_beam,
                      cylinder_angle=cylinder_angle,
                      ri_calculation_mode=self.ri_calculation_mode,
                      prerefl_file=self.prerefl_file,
                      refraction_index=self.refraction_index,
                      attenuation_coefficient=self.attenuation_coefficient,
                      radius=self.radius*um_to_si,
                      conic_coefficients=None) # TODO: add conic coefficient shape to the GUI

    def get_beamline_element_instance(self):
        return S4LensElement()
