import sys
import copy

from orangewidget.settings import Setting
from oasys.widgets.gui import MessageDialog

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence

from orangecontrib.shadow4.widgets.tools.ow_plot_xy import _PlotXY

class PlotXYFootprint(_PlotXY):

    name = "Plot XY Footprint"
    description = "Display Data Tools: Plot XY Footprint"
    icon = "icons/footprint.png"
    priority = 1.2
    inputs = copy.deepcopy(_PlotXY.inputs)

    x_column_index = Setting(1)
    y_column_index = Setting(0)
    conversion_active = Setting(0)
    image_plane              = Setting(0)
    image_plane_new_position = Setting(0.0)

    def __init__(self):
        super().__init__(allow_retrace=False)

    def set_shadow_data(self, shadow_data : ShadowData):
        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_empty_beam(shadow_data.footprint):
                self.input_data = shadow_data
                if self.is_automatic_run: self.plot_results()
            else:
                MessageDialog.message(self, "Data not displayable: bad content", "Error", "critical")

    def get_beam_to_plot(self, return_str=False):
        if return_str:
            return "footprint"
        else:
            return self.input_data.footprint

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMessageBox


    def get_beamline():
        from shadow4.beamline.s4_beamline import S4Beamline

        beamline = S4Beamline()

        # electron beam
        from shadow4.sources.s4_electron_beam import S4ElectronBeam
        electron_beam = S4ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
        electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=4.36821e-06, sigma_xp=3.63641e-06,
                                     sigma_yp=1.37498e-06)

        # magnetic structure
        from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian
        source = S4UndulatorGaussian(
            period_length=0.042,  # syned Undulator parameter (length in m)
            number_of_periods=38.571,  # syned Undulator parameter
            photon_energy=5000.0,  # Photon energy (in eV)
            delta_e=4.0,  # Photon energy width (in eV)
            ng_e=100,  # Photon energy scan number of points
            flag_emittance=1,  # when sampling rays: Use emittance (0=No, 1=Yes)
            flag_energy_spread=0,  # when sampling rays: Use e- energy spread (0=No, 1=Yes)
            harmonic_number=1,  # harmonic number
            flag_autoset_flux_central_cone=1,  # value to set the flux peak
            flux_central_cone=681709040139326.4,  # value to set the flux peak
        )

        # light source
        from shadow4.sources.undulator.s4_undulator_gaussian_light_source import S4UndulatorGaussianLightSource
        light_source = S4UndulatorGaussianLightSource(name='GaussianUndulator', electron_beam=electron_beam,
                                                      magnetic_structure=source, nrays=15000, seed=5676561)
        beam = light_source.get_beam()

        beamline.set_light_source(light_source)

        # optical element number XX
        from syned.beamline.shape import Rectangle
        boundary_shape = Rectangle(x_left=-0.001, x_right=0.001, y_bottom=-0.001, y_top=0.001)

        from shadow4.beamline.optical_elements.absorbers.s4_screen import S4Screen
        optical_element = S4Screen(name='Generic Beam Screen/Slit/Stopper/Attenuator', boundary_shape=boundary_shape,
                                   i_abs=0,  # 0=No, 1=prerefl file_abs, 2=xraylib, 3=dabax
                                   i_stop=0, thick=0, file_abs='<specify file name>', material='Au', density=19.3)

        from syned.beamline.element_coordinates import ElementCoordinates
        coordinates = ElementCoordinates(p=27.2, q=0, angle_radial=0, angle_azimuthal=0, angle_radial_out=3.141592654)
        from shadow4.beamline.optical_elements.absorbers.s4_screen import S4ScreenElement
        beamline_element = S4ScreenElement(optical_element=optical_element, coordinates=coordinates, input_beam=beam)

        beam, footprint = beamline_element.trace_beam()

        beamline.append_beamline_element(beamline_element)

        # optical element number XX
        boundary_shape = None

        from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror
        optical_element = S4PlaneMirror(name='Plane Mirror', boundary_shape=boundary_shape,
                                        f_reflec=1, f_refl=5, file_refl='<none>', refraction_index=0.99999 + 0.001j,
                                        coating_material='Ni', coating_density=8.902, coating_roughness=0)

        from syned.beamline.element_coordinates import ElementCoordinates
        coordinates = ElementCoordinates(p=2.7, q=0, angle_radial=1.563796327, angle_azimuthal=1.570796327,
                                         angle_radial_out=1.563796327)
        movements = None
        from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirrorElement
        beamline_element = S4PlaneMirrorElement(optical_element=optical_element, coordinates=coordinates,
                                                movements=movements, input_beam=beam)

        beam, mirr = beamline_element.trace_beam()

        beamline.append_beamline_element(beamline_element)

        # test plot
        if 0:
            from srxraylib.plot.gol import plot_scatter
            plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1),
                         title='(Intensity,Photon Energy)', plot_histograms=0)
            plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1),
                         title='(X,Z) in microns')
        return beam, footprint, beamline
        ###############################


    beam, footprint, beamline = get_beamline()

    app = QApplication(sys.argv)
    w = PlotXYFootprint()
    w.set_shadow_data(ShadowData(beam=beam, footprint=footprint, number_of_rays=0, beamline=beamline))
    w.show()
    app.exec()

