import os

from orangecontrib.shadow4.widgets.gui.ow_abstract_lens import OWAbstractLens
import orangecanvas.resources as resources

from syned.beamline.shape import Circle, Rectangle
from shadow4.beamline.optical_elements.refractors.s4_lens import S4Lens, S4LensElement


class OWLens(OWAbstractLens):
    name = "Refractive Lens"
    description = "Shadow Refractive Lens"
    icon = "icons/lens.png"
    priority = 2.1

    help_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui"), "misc", "lens_help.png")

    def __init__(self):
        super().__init__()

    # ----------------------------------------------------
    # from OpticalElement

    def get_optical_element_instance(self):
        try:    name = self.getNode().title
        except: name = "Refractive Lens"

        um_to_si = 1e-6

        if self.has_finite_diameter == 0:
            boundary_shape = None
        elif self.has_finite_diameter == 1:
            boundary_shape = Circle(radius=um_to_si * self.diameter * 0.5)
        else:
            half_aperture = um_to_si * self.diameter * 0.5
            boundary_shape = Rectangle(x_left = -half_aperture, x_right = half_aperture,
                                       y_bottom = -half_aperture, y_top = half_aperture)

        if self.is_cylinder == 1:
            cylinder_angle = self.cylinder_angle + 1
        else:
            cylinder_angle = 0

        return S4Lens(name=name,
                      boundary_shape=boundary_shape,
                      material=self.material,
                      density=self.density,
                      thickness=self.interthickness*um_to_si,
                      surface_shape=self.surface_shape,
                      convex_to_the_beam=self.convex_to_the_beam,
                      cylinder_angle=cylinder_angle,
                      ri_calculation_mode=self.ri_calculation_mode,
                      prerefl_file=self.prerefl_file,
                      refraction_index=self.refraction_index,
                      attenuation_coefficient=self.attenuation_coefficient,
                      radius=self.radius*um_to_si,
                      conic_coefficients1=None, # TODO: add conic coefficient shape to the GUI
                      conic_coefficients2=None,  # TODO: add conic coefficient shape to the GUI
                      )

    def get_beamline_element_instance(self):
        return S4LensElement()

if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline
    import sys
    from orangecontrib.shadow4.util.shadow4_objects import ShadowData, PreReflPreProcessorData, VlsPgmPreProcessorData

    def get_test_beam():
        # electron beam
        from syned.storage_ring.light_source import ElectronBeam
        electron_beam = ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
        electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=3.63641e-06, sigma_xp=4.36821e-06,
                                     sigma_yp=1.37498e-06)

        # Gaussian undulator
        from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian
        sourceundulator = S4UndulatorGaussian(
            period_length=0.0159999,
            number_of_periods=100,
            photon_energy=2700.136,
            delta_e=0.0,
            flag_emittance=1,  # Use emittance (0=No, 1=Yes)
        )
        sourceundulator.set_energy_monochromatic(2700.14)

        from shadow4.sources.undulator.s4_undulator_gaussian_light_source import S4UndulatorGaussianLightSource
        light_source = S4UndulatorGaussianLightSource(name='GaussianUndulator', electron_beam=electron_beam,
                                              magnetic_structure=sourceundulator, nrays=5000, seed=5676561)

        beam = light_source.get_beam()

        return ShadowData(beam=beam, beamline=S4Beamline(light_source=light_source))

    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWLens()
    ow.set_shadow_data(get_test_beam())

    ow.show()
    a.exec_()
    ow.saveSettings()

