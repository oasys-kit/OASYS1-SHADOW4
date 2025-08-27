

from shadow4.beamline.optical_elements.gratings.s4_plane_grating import S4PlaneGrating, S4PlaneGratingElement
from shadow4.beamline.optical_elements.gratings.s4_sphere_grating import S4SphereGrating, S4SphereGratingElement
from shadow4.beamline.s4_optical_element_decorators import SurfaceCalculation, S4SphereOpticalElementDecorator


import numpy
import sys
import xraylib

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from shadow4.beamline.optical_elements.gratings.s4_plane_grating import S4PlaneGrating, S4PlaneGratingElement
from shadow4.beamline.optical_elements.gratings.s4_sphere_grating import S4SphereGrating, S4SphereGratingElement
from shadow4.beamline.optical_elements.gratings.s4_conic_grating import S4ConicGrating, S4ConicGratingElement
from shadow4.beamline.optical_elements.gratings.s4_toroid_grating import S4ToroidGrating, S4ToroidGratingElement
from shadow4.beamline.optical_elements.gratings.s4_ellipsoid_grating import S4EllipsoidGrating, S4EllipsoidGratingElement
from shadow4.beamline.optical_elements.gratings.s4_hyperboloid_grating import S4HyperboloidGrating, S4HyperboloidGratingElement
from shadow4.beamline.optical_elements.gratings.s4_paraboloid_grating import S4ParaboloidGrating, S4ParaboloidGratingElement
from shadow4.beamline.optical_elements.gratings.s4_numerical_mesh_grating import S4NumericalMeshGrating, S4NumericalMeshGratingElement
from shadow4.beamline.optical_elements.gratings.s4_additional_numerical_mesh_grating import S4AdditionalNumericalMeshGrating, S4AdditionalNumericalMeshGratingElement


from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.widgets.gui.ow_optical_element_with_surface_shape import OWOpticalElementWithSurfaceShape

from orangecontrib.shadow4.util.shadow4_objects import VlsPgmPreProcessorData
import copy


class _OWGrating(OWOpticalElementWithSurfaceShape):

    #########################################################
    # grating
    #########################################################

    ruling                 = Setting(800e3)
    ruling_coeff_linear    = Setting(0.0)
    ruling_coeff_quadratic = Setting(0.0)
    ruling_coeff_cubic     = Setting(0.0)
    ruling_coeff_quartic   = Setting(0.0)
    order = Setting(-1)
    f_ruling = Setting(1)

    def __init__(self):
        super(_OWGrating, self).__init__()
        # with gratings no "internal surface parameters" allowed. Fix value and hide selecting combo:
        self.surface_shape_parameters = 1
        self.surface_shape_internal_external_box.setVisible(False)

    def create_basic_settings_specific_subtabs(self, tabs_basic_setting):
        subtab_grating_diffraction = oasysgui.createTabPage(tabs_basic_setting, "Grating")    # to be populated
        subtab_grating_efficiency = oasysgui.createTabPage(tabs_basic_setting, "G. Efficiency")    # to be populated

        return subtab_grating_diffraction, subtab_grating_efficiency

    def populate_basic_settings_specific_subtabs(self, specific_subtabs):
        subtab_grating_diffraction, subtab_grating_efficiency = specific_subtabs

        #########################################################
        # Basic Settings / Grating Diffraction
        #########################################################
        self.populate_tab_grating_diffraction(subtab_grating_diffraction)

        #########################################################
        # Basic Settings / Grating Efficiency
        #########################################################
        self.populate_tab_grating_efficiency(subtab_grating_efficiency)

    def populate_tab_grating_diffraction(self, subtab_grating_diffraction):

        grating_box = oasysgui.widgetBox(subtab_grating_diffraction, "Grating Diffraction", addSpace=True, orientation="vertical")


        gui.comboBox(grating_box, self, "f_ruling", tooltip="f_ruling",
                     label="Ruling type", labelWidth=120,
                     items=["Constant on X-Y plane",
                            "VLS Variable (Polynomial) Line Density"],
                     sendSelectedValue=False, orientation="horizontal",
                     callback=self.grating_diffraction_tab_visibility)

        gui.separator(grating_box)

        oasysgui.lineEdit(grating_box, self, "ruling", tooltip="ruling",
                          label="ruling (coeff 0; lines/m)", addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")

        self.grating_box_vls = oasysgui.widgetBox(grating_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.grating_box_vls, self, "ruling_coeff_linear", tooltip="ruling_coeff_linear",
                          label="ruling (coeff 1; Lines/m\u00b2])", addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")

        oasysgui.lineEdit(self.grating_box_vls, self, "ruling_coeff_quadratic", tooltip="ruling_coeff_quadratic",
                          label="ruling (coeff 2; Lines/m\u00b3])", addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")

        oasysgui.lineEdit(self.grating_box_vls, self, "ruling_coeff_cubic", tooltip="ruling_coeff_cubic",
                          label="ruling (coeff 3; Lines/m\u2074])", addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")

        oasysgui.lineEdit(self.grating_box_vls, self, "ruling_coeff_quartic", tooltip="ruling_coeff_quartic",
                          label="ruling (coeff 4; Lines/m\u2075])", addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")

        oasysgui.lineEdit(grating_box, self, "order", tooltip="order",
                          label="Diffraction order (- for inside orders)", addSpace=True,
                          valueType=int, labelWidth=200, orientation="horizontal")

        self.grating_diffraction_tab_visibility()

    def populate_tab_grating_efficiency(self, subtab_grating_efficiency):
        pass

    #########################################################
    # Grating Methods
    #########################################################

    def setVlsPgmPreProcessorData(self, data):
        if data is not None:
            self.surface_shape_type = 0
            self.surface_shape_tab_visibility()

            self.source_plane_distance = data.d_mirror_to_grating/2
            self.image_plane_distance = data.d_grating_to_exit_slits

            self.angles_respect_to = 0
            self.incidence_angle_deg = data.alpha
            self.reflection_angle_deg =data.beta
            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

            self.oe_orientation_angle = 2
            self.order = -1

            self.f_ruling = 1
            self.ruling = data.shadow_coeff_0
            self.ruling_coeff_linear = data.shadow_coeff_1
            self.ruling_coeff_quadratic = data.shadow_coeff_2
            self.ruling_coeff_cubic = data.shadow_coeff_3
            self.ruling_coeff_quartic = 0.0
            self.grating_diffraction_tab_visibility()


    def grating_diffraction_tab_visibility(self):
        self.grating_box_vls.setVisible(self.f_ruling==1)

    #########################################################
    # S4 objects
    #########################################################

    def get_optical_element_instance(self):
        if self.surface_shape_type > 0 and self.surface_shape_parameters == 0:
            raise ValueError("Curved grating with internal calculation not allowed.")

        try:    name = self.getNode().title
        except: name = "Grating"

        if self.surface_shape_type == 0:
            grating = S4PlaneGrating(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=self.f_ruling,
            )

        elif self.surface_shape_type == 1:
            print("FOCUSING DISTANCES: convexity:  ", numpy.logical_not(self.surface_curvature).astype(int))
            print("FOCUSING DISTANCES: radius:  ", self.spherical_radius)

            grating = S4SphereGrating(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=self.f_ruling,
                #
                # surface_calculation=SurfaceCalculation.EXTERNAL,
                radius=self.spherical_radius,
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
            )
        elif self.surface_shape_type == 2:
            grating = S4EllipsoidGrating(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=self.f_ruling,
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                min_axis=self.ellipse_hyperbola_semi_minor_axis * 2, # todo: check factor 2
                maj_axis=self.ellipse_hyperbola_semi_major_axis * 2, # todo: check factor 2
                pole_to_focus=self.angle_of_majax_and_pole, # todo: change variable name
            )
        elif self.surface_shape_type == 3:
            grating = S4HyperboloidGrating(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=self.f_ruling,
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                min_axis=0.0,
                maj_axis=0.0,
                pole_to_focus=self.angle_of_majax_and_pole, # todo: change variable name
            )
        elif self.surface_shape_type == 4:
            grating = S4ParaboloidGrating(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=self.f_ruling,
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                parabola_parameter=self.paraboloid_parameter,
                at_infinity=self.focus_location, #  Side:  Side.SOURCE: SOURCE = 0  IMAGE = 1
                pole_to_focus=self.angle_of_majax_and_pole, # todo: rename this input
            )
        elif self.surface_shape_type == 5:
            grating = S4ToroidGrating(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=self.f_ruling,
                #
                min_radius=self.torus_minor_radius,
                maj_radius=self.torus_major_radius,
                f_torus=self.toroidal_mirror_pole_location,
            )
        elif self.surface_shape_type == 6:
            grating = S4ConicGrating(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=self.f_ruling,
                conic_coefficients=[
                    self.conic_coefficient_0, self.conic_coefficient_1, self.conic_coefficient_2,
                    self.conic_coefficient_3, self.conic_coefficient_4, self.conic_coefficient_5,
                    self.conic_coefficient_6, self.conic_coefficient_7, self.conic_coefficient_8,
                    self.conic_coefficient_9],
            )
        else:
            raise NotImplementedError("surface_shape_type=%d not implemented " % self.surface_shape_type)

        if self.modified_surface:
            return S4AdditionalNumericalMeshGrating(name=name,
                        ideal_grating=grating,
                        numerical_mesh_grating=S4NumericalMeshGrating(
                            surface_data_file=self.ms_defect_file_name,
                            boundary_shape=None,
                            ruling=self.ruling,
                            ruling_coeff_linear=self.ruling_coeff_linear,
                            ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                            ruling_coeff_cubic=self.ruling_coeff_cubic,
                            ruling_coeff_quartic=self.ruling_coeff_quartic,
                            coating=None,
                            coating_thickness=None,
                            order=self.order,
                            f_ruling=self.f_ruling,
                            )
                        )
        else:
            return grating

    def get_beamline_element_instance(self):
        if self.modified_surface:
            return S4AdditionalNumericalMeshGratingElement()
        else:
            if self.surface_shape_type == 0:   return  S4PlaneGratingElement()
            elif self.surface_shape_type == 1: return S4SphereGratingElement()
            elif self.surface_shape_type == 2: return S4EllipsoidGratingElement()
            elif self.surface_shape_type == 3: return S4HyperboloidGratingElement()
            elif self.surface_shape_type == 4: return S4ParaboloidGratingElement()
            elif self.surface_shape_type == 5: return S4ToroidGratingElement()
            elif self.surface_shape_type == 6: return S4ConicGratingElement()
            else: raise NotImplementedError("surface_shape_type not yet implemented!")

class OWGrating(_OWGrating):
    name = "Generic Grating"
    description = "Shadow Grating"
    icon = "icons/plane_grating.png"

    priority = 1.390

    inputs = copy.deepcopy(OWOpticalElementWithSurfaceShape.inputs)
    inputs.append(("VLS-PGM PreProcessor Data", VlsPgmPreProcessorData, "setVlsPgmPreProcessorData"))

    def get_oe_type(self):
        return "grating", "Grating"

if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline
    from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
    def get_test_beam():
        from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
        light_source = SourceGeometrical(name='SourceGeometrical', nrays=5000, seed=5676561)
        light_source.set_spatial_type_point()
        light_source.set_angular_distribution_flat(hdiv1=-0.000000, hdiv2=0.000000, vdiv1=-0.000000, vdiv2=0.000000)
        light_source.set_energy_distribution_uniform(value_min=7990.000000, value_max=8010.000000, unit='eV')
        light_source.set_polarization(polarization_degree=1.000000, phase_diff=0.000000, coherent_beam=0)
        beam = light_source.get_beam()
        return ShadowData(beam=beam, beamline=S4Beamline(light_source=light_source))

    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWGrating()
    ow.set_shadow_data(get_test_beam())
    ow.show()
    a.exec_()
    ow.saveSettings()