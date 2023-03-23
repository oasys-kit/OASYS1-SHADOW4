import numpy
import sys

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.shape import Side       #  Side:  SOURCE = 0  IMAGE = 1

from shadow4.beamline.optical_elements.mirrors.s4_toroidal_mirror import S4ToroidalMirror, S4ToroidalMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_conic_mirror import S4ConicMirror, S4ConicMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror, S4PlaneMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_ellipsoid_mirror import S4EllipsoidMirror, S4EllipsoidMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_hyperboloid_mirror import S4HyperboloidMirror, S4HyperboloidMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_paraboloid_mirror import S4ParaboloidMirror, S4ParaboloidMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_sphere_mirror import S4SphereMirror, S4SphereMirrorElement

from shadow4.beamline.optical_elements.mirrors.s4_numerical_mesh_mirror import S4NumericalMeshMirror
from shadow4.beamline.optical_elements.mirrors.s4_additional_numerical_mesh_mirror import S4AdditionalNumericalMeshMirror
from shadow4.beamline.optical_elements.mirrors.s4_additional_numerical_mesh_mirror import S4AdditionalNumericalMeshMirrorElement


from orangecontrib.shadow4.widgets.gui.ow_optical_element_with_surface_shape import OWOpticalElementWithSurfaceShape
from orangecontrib.shadow4.util.shadow_objects import ShadowData

class OWMirror(OWOpticalElementWithSurfaceShape, WidgetDecorator):
    name        = "Generic Mirror"
    description = "Shadow Mirror"
    icon        = "icons/plane_mirror.png"

    priority = 1.0

    def get_oe_type(self):
        return "mirror", "Mirror"

    #########################################################
    # reflectivity
    #########################################################

    reflectivity_flag             = Setting(0)  # f_reflec
    reflectivity_source           = Setting(0) # f_refl
    file_refl                     = Setting("<none>")

    refraction_index_delta        = Setting(1e-5)
    refraction_index_beta         = Setting(1e-3)

    def __init__(self):
        super(OWMirror, self).__init__()


    def create_specific_subtabs(self, tabs_basic_setting): return oasysgui.createTabPage(tabs_basic_setting, "Reflectivity")

    def populate_specific_subtabs(self, specific_subtabs):
        subtab_reflectivity = specific_subtabs

        #########################################################
        # Basic Settings / Reflectivity
        #########################################################
        self.populate_tab_reflectivity(subtab_reflectivity)

    def populate_tab_reflectivity(self, subtab_reflectivity):
        # # f_reflec = 0    # reflectivity of surface: 0=no reflectivity, 1=full polarization
        # # f_refl   = 0    # 0=prerefl file
        # #                 # 1=electric susceptibility
        # #                 # 2=user defined file (1D reflectivity vs angle)
        # #                 # 3=user defined file (1D reflectivity vs energy)
        # #                 # 4=user defined file (2D reflectivity vs energy and angle)
        # # file_refl = "",  # preprocessor file fir f_refl=0,2,3,4
        # # refraction_index = 1.0,  # refraction index (complex) for f_refl=1

        box_1 = oasysgui.widgetBox(subtab_reflectivity, "Reflectivity Parameter", addSpace=True, orientation="vertical")

        gui.comboBox(box_1, self, "reflectivity_flag", label="Reflectivity", labelWidth=150,
                     items=["Not considered", "Full polarization"],
                     callback=self.reflectivity_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="reflectivity_flag")

        self.reflectivity_flag_box = oasysgui.widgetBox(box_1, "", addSpace=False, orientation="vertical")
        gui.comboBox(self.reflectivity_flag_box, self, "reflectivity_source", label="Reflectivity source", labelWidth=150,
                     items=["PreRefl File",
                            "Refraction index",
                            "file 1D: (reflectivity vs angle)",
                            "file 1D: (reflectivity vs energy)",
                            "file 2D: (reflectivity vs energy and angle)",
                            ],
                     callback=self.reflectivity_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="reflectivity_source")


        self.file_refl_box = oasysgui.widgetBox(self.reflectivity_flag_box, "", addSpace=False, orientation="horizontal", height=25)
        self.le_file_refl = oasysgui.lineEdit(self.file_refl_box, self, "file_refl", "File Name", labelWidth=100,
                                              valueType=str, orientation="horizontal", tooltip="file_refl")
        gui.button(self.file_refl_box, self, "...", callback=self.select_file_refl)


        self.refraction_index_box = oasysgui.widgetBox(self.reflectivity_flag_box, "", addSpace=False, orientation="horizontal", height=25)
        oasysgui.lineEdit(self.refraction_index_box, self, "refraction_index_delta",
                          "n=1-delta+i beta; delta: ", labelWidth=110, valueType=float,
                          orientation="horizontal", tooltip="refraction_index_delta")

        oasysgui.lineEdit(self.refraction_index_box, self, "refraction_index_beta",
                          "beta: ", labelWidth=30, valueType=float,
                          orientation="horizontal", tooltip="refraction_index_beta")

        self.reflectivity_tab_visibility()

    #########################################################
    # Reflectvity Methods
    #########################################################
    def reflectivity_tab_visibility(self):
        self.reflectivity_flag_box.setVisible(False)
        self.file_refl_box.setVisible(False)
        self.refraction_index_box.setVisible(False)

        if self.reflectivity_flag == 1:
            self.reflectivity_flag_box.setVisible(True)

        if self.reflectivity_source in [0, 2, 3, 4]:
            self.file_refl_box.setVisible(True)
        else:
            self.refraction_index_box.setVisible(True)

    def select_file_refl(self):
        self.le_file_refl.setText(oasysgui.selectFileFromDialog(self, self.file_refl, "Select File with Reflectivity")) #, file_extension_filter="Data Files (*.dat)"))

    #########################################################
    # S4 objects
    #########################################################

    def get_optical_element_instance(self):
        #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
        #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
        #  Side:  SOURCE = 0  IMAGE = 1
        if self.surface_shape_type == 0:
            mirror = S4PlaneMirror(
                name="Plane Mirror",
                boundary_shape=self.get_boundary_shape(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )
        elif self.surface_shape_type == 1:
            print("FOCUSING DISTANCES: convexity:  ", numpy.logical_not(self.surface_curvature).astype(int))
            print("FOCUSING DISTANCES: internal/external:  ", self.surface_shape_parameters)
            print("FOCUSING DISTANCES: radius:  ", self.spherical_radius)
            print("FOCUSING DISTANCES: p:  ", self.get_focusing_p())
            print("FOCUSING DISTANCES: q:  ", self.get_focusing_q())
            print("FOCUSING DISTANCES: grazing angle:  ", self.get_focusing_grazing_angle())

            mirror = S4SphereMirror(
                name="Sphere Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                radius=self.spherical_radius,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )
        elif self.surface_shape_type == 2:
            mirror = S4EllipsoidMirror(
                name="Ellipsoid Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                min_axis=0.0,
                maj_axis=0.0,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )
        elif self.surface_shape_type == 3:
            mirror = S4HyperboloidMirror(
                name="Hyperboloid Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                min_axis=0.0,
                maj_axis=0.0,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )
        elif self.surface_shape_type == 4:
            mirror = S4ParaboloidMirror(
                name="Paraboloid Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                parabola_parameter=0.0,
                at_infinity=Side.SOURCE, #  Side:  SOURCE = 0  IMAGE = 1
                pole_to_focus=None,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )
        elif self.surface_shape_type == 5:
            mirror = S4ToroidalMirror(
                name="Toroidal Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                min_radius=0.1,
                maj_radius=1.0,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )
        elif self.surface_shape_type == 6:
            mirror = S4ConicMirror(
                name="Conic coefficients Mirror",
                boundary_shape=self.get_boundary_shape(),
                conic_coefficients=[
                     self.conic_coefficient_0,self.conic_coefficient_1,self.conic_coefficient_2,
                     self.conic_coefficient_3,self.conic_coefficient_4,self.conic_coefficient_5,
                     self.conic_coefficient_6,self.conic_coefficient_7,self.conic_coefficient_8,
                     self.conic_coefficient_9],
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                # 1=electric susceptibility
                # 2=user defined file (1D reflectivity vs angle)
                # 3=user defined file (1D reflectivity vs energy)
                # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta  # refraction index (complex) for f_refl=1
            )

        # if error is selected...

        if self.modified_surface:
            # todo: check congruence of limits
            return S4AdditionalNumericalMeshMirror(name="ideal + error Mirror",
                                                   ideal_mirror=mirror,
                                                   numerical_mesh_mirror=S4NumericalMeshMirror(
                                                       surface_data_file=self.ms_defect_file_name,
                                                       boundary_shape=None),
                                                   )
        else:
            return mirror

    def get_beamline_element_instance(self):
        if self.modified_surface:
            return S4AdditionalNumericalMeshMirrorElement()
        else:
            if self.surface_shape_type == 0:   return S4PlaneMirrorElement()
            elif self.surface_shape_type == 1: return S4SphereMirrorElement()
            elif self.surface_shape_type == 2: return S4EllipsoidMirrorElement()
            elif self.surface_shape_type == 3: return S4HyperboloidMirrorElement()
            elif self.surface_shape_type == 4: return S4ParaboloidMirrorElement()
            elif self.surface_shape_type == 5: return S4ToroidalMirrorElement()
            elif self.surface_shape_type == 6: return S4ConicMirrorElement()


    def calculate_incidence_angle_mrad(self):
        super().calculate_incidence_angle_mrad()

        self.reflection_angle_deg = self.incidence_angle_deg
        self.reflection_angle_mrad = self.incidence_angle_mrad

    def calculate_incidence_angle_deg(self):
        super().calculate_incidence_angle_deg()

        self.reflection_angle_deg = self.incidence_angle_deg
        self.reflection_angle_mrad = self.incidence_angle_mrad


if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline
    def get_test_beam():
        # electron beam
        from syned.storage_ring.light_source import ElectronBeam
        electron_beam = ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
        electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=3.63641e-06, sigma_xp=4.36821e-06,
                                     sigma_yp=1.37498e-06)

        # Gaussian undulator
        from shadow4.sources.undulator.s4_undulator import S4Undulator
        sourceundulator = S4Undulator(
            period_length=0.0159999,
            number_of_periods=100,
            emin=2700.136,
            emax=2700.136,
            flag_emittance=1,  # Use emittance (0=No, 1=Yes)
        )
        sourceundulator.set_energy_monochromatic(2700.14)

        from shadow4.sources.undulator.s4_undulator_light_source import S4UndulatorLightSource
        light_source = S4UndulatorLightSource(name='GaussianUndulator', electron_beam=electron_beam,
                                             magnetic_structure=sourceundulator, nrays=5000, seed=5676561)

        beam = light_source.get_beam_in_gaussian_approximation()

        return ShadowData(beam=beam, beamline=S4Beamline(light_source=light_source))

    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWMirror()
    ow.set_shadow_data(get_test_beam())
    ow.show()
    a.exec_()
    ow.saveSettings()
