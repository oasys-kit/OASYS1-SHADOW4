import numpy
import sys
import copy

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from shadow4.beamline.optical_elements.mirrors.s4_toroid_mirror import S4ToroidMirror, S4ToroidMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_conic_mirror import S4ConicMirror, S4ConicMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror, S4PlaneMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_ellipsoid_mirror import S4EllipsoidMirror, S4EllipsoidMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_hyperboloid_mirror import S4HyperboloidMirror, S4HyperboloidMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_paraboloid_mirror import S4ParaboloidMirror, S4ParaboloidMirrorElement
from shadow4.beamline.optical_elements.mirrors.s4_sphere_mirror import S4SphereMirror, S4SphereMirrorElement

from shadow4.beamline.optical_elements.mirrors.s4_numerical_mesh_mirror import S4NumericalMeshMirror
from shadow4.beamline.optical_elements.mirrors.s4_additional_numerical_mesh_mirror import S4AdditionalNumericalMeshMirror
from shadow4.beamline.optical_elements.mirrors.s4_additional_numerical_mesh_mirror import S4AdditionalNumericalMeshMirrorElement

from orangecontrib.shadow4.widgets.gui.ow_optical_element_with_surface_shape import OWOpticalElementWithSurfaceShape, SUBTAB_INNER_BOX_WIDTH
from orangecontrib.shadow4.util.shadow4_objects import ShadowData, PreReflPreProcessorData, VlsPgmPreProcessorData

class _OWMirror(OWOpticalElementWithSurfaceShape):
    #########################################################
    # reflectivity
    #########################################################

    reflectivity_flag             = Setting(0)  # f_reflec
    reflectivity_source           = Setting(0) # f_refl
    file_refl                     = Setting("<none>")

    refraction_index_delta        = Setting(1e-5)
    refraction_index_beta         = Setting(1e-3)

    coating_material = Setting("Si")
    coating_density = Setting(2.33)
    coating_roughness = Setting(0.0)

    def __init__(self, switch_icons=True):
        super(_OWMirror, self).__init__(switch_icons=switch_icons)

        self.reflection_angle_deg_le.setEnabled(False)
        self.reflection_angle_rad_le.setEnabled(False)


    def create_basic_settings_specific_subtabs(self, tabs_basic_setting): return oasysgui.createTabPage(tabs_basic_setting, "Reflectivity")

    def populate_basic_settings_specific_subtabs(self, specific_subtabs):
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

        box_1 = oasysgui.widgetBox(subtab_reflectivity, "Mirror Reflectivity", addSpace=True, orientation="vertical", width=SUBTAB_INNER_BOX_WIDTH)

        gui.comboBox(box_1, self, "reflectivity_flag", label="Reflectivity", labelWidth=150,
                     items=["Not considered", "Yes"],
                     callback=self.reflectivity_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="reflectivity_flag")

        self.reflectivity_flag_box = oasysgui.widgetBox(box_1, "", addSpace=False, orientation="vertical")
        gui.comboBox(self.reflectivity_flag_box, self, "reflectivity_source", label="Reflectivity source", labelWidth=150,
                     items=["PreRefl File",
                            "Refraction index",
                            "file 1D: (reflectivity vs angle)",
                            "file 1D: (reflectivity vs energy)",
                            "file 2D: (reflectivity vs energy and angle)",
                            "Internal (using xraylib)",
                            "Internal (using Dabax)",
                            ],
                     callback=self.reflectivity_tab_visibility, sendSelectedValue=False, orientation="horizontal",
                     tooltip="reflectivity_source")


        self.file_refl_box = oasysgui.widgetBox(self.reflectivity_flag_box, "", addSpace=False, orientation="horizontal", height=25)
        self.le_file_refl = oasysgui.lineEdit(self.file_refl_box, self, "file_refl", "File Name", labelWidth=100,
                                              valueType=str, orientation="horizontal", tooltip="file_refl")
        gui.button(self.file_refl_box, self, "...", callback=self.select_file_refl)


        self.refraction_index_box = oasysgui.widgetBox(self.reflectivity_flag_box, "", addSpace=False, orientation="vertical", height=50)
        oasysgui.lineEdit(self.refraction_index_box, self, "refraction_index_delta",
                          "n=1-delta+i beta; delta: ", labelWidth=180, valueType=float,
                          orientation="horizontal", tooltip="refraction_index_delta")

        oasysgui.lineEdit(self.refraction_index_box, self, "refraction_index_beta",
                          "                  beta: ", labelWidth=180, valueType=float,
                          orientation="horizontal", tooltip="refraction_index_beta")

        self.material_refl_box = oasysgui.widgetBox(self.reflectivity_flag_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.material_refl_box, self, "coating_material",
                          "Coating material (formula): ", labelWidth=180, valueType=str,
                          orientation="horizontal", tooltip="coating_material")

        oasysgui.lineEdit(self.material_refl_box, self, "coating_density",
                          "Coating density [g/cm^3]: ", labelWidth=180, valueType=float,
                          orientation="horizontal", tooltip="coating_density")

        self.roughness_refl_box = oasysgui.widgetBox(self.reflectivity_flag_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.roughness_refl_box, self, "coating_roughness",
                          "Coating roughness rms [A]: ", labelWidth=180, valueType=float,
                          orientation="horizontal", tooltip="coating_roughness")

        self.reflectivity_tab_visibility()

    #########################################################
    # Reflectvity Methods
    #########################################################
    def reflectivity_tab_visibility(self):
        self.reflectivity_flag_box.setVisible(False)
        self.file_refl_box.setVisible(False)
        self.refraction_index_box.setVisible(False)
        self.material_refl_box.setVisible(False)
        self.roughness_refl_box.setVisible(False)

        if self.reflectivity_flag == 1:
            self.reflectivity_flag_box.setVisible(True)

        if self.reflectivity_source == 1:
            self.refraction_index_box.setVisible(True)

        if self.reflectivity_source in [0, 2, 3, 4]:
            self.file_refl_box.setVisible(True)

        if self.reflectivity_source in [5, 6]:
            self.material_refl_box.setVisible(True)

        if self.reflectivity_source in [0, 1, 5, 6]:
            self.roughness_refl_box.setVisible(True)

    def select_file_refl(self):
        self.le_file_refl.setText(oasysgui.selectFileFromDialog(self, self.file_refl, "Select File with Reflectivity")) #, file_extension_filter="Data Files (*.dat)"))

    #########################################################
    # preprocessor
    #########################################################

    def set_PreReflPreProcessorData(self, data):
        if data is not None:
            if data.prerefl_data_file != PreReflPreProcessorData.NONE:
                self.file_refl = data.prerefl_data_file
                self.reflectivity_flag = 1
                self.reflectivity_source = 0
                self.reflectivity_tab_visibility()
            else:
                QMessageBox.warning(self, "Warning", "Incompatible Preprocessor Data", QMessageBox.Ok)

    def set_VlsPgmPreProcessorData(self, data):
        if data is not None:
            self.surface_shape_type = 0
            self.surface_shape_tab_visibility()

            self.source_plane_distance = data.d_source_plane_to_mirror
            self.image_plane_distance =  data.d_mirror_to_grating/2
            self.angles_respect_to = 0
            self.incidence_angle_deg  = (data.alpha + data.beta)/2
            self.reflection_angle_deg = (data.alpha + data.beta)/2

            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

    #########################################################
    # S4 objects
    #########################################################

    def get_optical_element_instance(self):

        # possible change of limits to match with the surface data file (must be done before creating mirror)
        if self.modified_surface: self.congruence_surface_data_file()

        #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
        #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
        #  Side:  SOURCE = 0  IMAGE = 1

        try:    name = self.getNode().title
        except: name = "Mirror"

        if self.surface_shape_type == 0:
            mirror = S4PlaneMirror(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=self.reflectivity_source,  # 0=prerefl file
                                                # 1=electric susceptibility
                                                # 2=user defined file (1D reflectivity vs angle)
                                                # 3=user defined file (1D reflectivity vs energy)
                                                # 4=user defined file (2D reflectivity vs energy and angle)
                                                # 5=direct calculation using xraylib
                                                # 6=direct calculation using dabax
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1-self.refraction_index_delta+1j*self.refraction_index_beta,  # refraction index (complex) for f_refl=1
                coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
                coating_density=self.coating_density,      # coating material density for f_refl=5,6
                coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            )
        elif self.surface_shape_type == 1:
            print("FOCUSING DISTANCES: convexity:  ", numpy.logical_not(self.surface_curvature).astype(int))
            print("FOCUSING DISTANCES: internal/external:  ", self.surface_shape_parameters)
            print("FOCUSING DISTANCES: radius:  ", self.spherical_radius)
            print("FOCUSING DISTANCES: p:  ", self.get_focusing_p())
            print("FOCUSING DISTANCES: q:  ", self.get_focusing_q())
            print("FOCUSING DISTANCES: grazing angle:  ", self.get_focusing_grazing_angle())

            mirror = S4SphereMirror(
                name=name,
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
                                                # 5=direct calculation using xraylib
                                                # 6=direct calculation using dabax
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
                # refraction index (complex) for f_refl=1
                coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
                coating_density=self.coating_density,      # coating material density for f_refl=5,6
                coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            )
        elif self.surface_shape_type == 2:
            mirror = S4EllipsoidMirror(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                min_axis=self.ellipse_hyperbola_semi_minor_axis * 2, # todo: check factor 2
                maj_axis=self.ellipse_hyperbola_semi_major_axis * 2, # todo: check factor 2
                pole_to_focus=self.angle_of_majax_and_pole, # todo: change variable name
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
                                                # 5=direct calculation using xraylib
                                                # 6=direct calculation using dabax
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
                # refraction index (complex) for f_refl=1
                coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
                coating_density=self.coating_density,      # coating material density for f_refl=5,6
                coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            )
        elif self.surface_shape_type == 3:
            mirror = S4HyperboloidMirror(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                min_axis=0.0,
                maj_axis=0.0,
                pole_to_focus=self.angle_of_majax_and_pole, # todo: change variable name
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
                                                # 5=direct calculation using xraylib
                                                # 6=direct calculation using dabax
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
                # refraction index (complex) for f_refl=1
                coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
                coating_density=self.coating_density,      # coating material density for f_refl=5,6
                coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            )
        elif self.surface_shape_type == 4:
            mirror = S4ParaboloidMirror(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                parabola_parameter=self.paraboloid_parameter,
                at_infinity=self.focus_location, #  Side:  Side.SOURCE: SOURCE = 0  IMAGE = 1
                pole_to_focus=self.angle_of_majax_and_pole, # todo: rename this input
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
                                                # 5=direct calculation using xraylib
                                                # 6=direct calculation using dabax
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
                # refraction index (complex) for f_refl=1
                coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
                coating_density=self.coating_density,      # coating material density for f_refl=5,6
                coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            )
        elif self.surface_shape_type == 5:
            mirror = S4ToroidMirror(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                min_radius=self.torus_minor_radius,
                maj_radius=self.torus_major_radius, # tangential radius
                f_torus=self.toroidal_mirror_pole_location,
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
                                                # 5=direct calculation using xraylib
                                                # 6=direct calculation using dabax
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
                # refraction index (complex) for f_refl=1
                coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
                coating_density=self.coating_density,      # coating material density for f_refl=5,6
                coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            )
        elif self.surface_shape_type == 6:
            mirror = S4ConicMirror(
                name=name,
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
                                                # 5=direct calculation using xraylib
                                                # 6=direct calculation using dabax
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
                # refraction index (complex) for f_refl=1
                coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
                coating_density=self.coating_density,      # coating material density for f_refl=5,6
                coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            )

        # if error is selected...

        if self.modified_surface:
            return S4AdditionalNumericalMeshMirror(name=name,
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
            elif self.surface_shape_type == 5: return S4ToroidMirrorElement()
            elif self.surface_shape_type == 6: return S4ConicMirrorElement()


    def calculate_incidence_angle_mrad(self):
        super().calculate_incidence_angle_mrad()

        self.reflection_angle_deg = self.incidence_angle_deg
        self.reflection_angle_mrad = self.incidence_angle_mrad

    def calculate_incidence_angle_deg(self):
        super().calculate_incidence_angle_deg()

        self.reflection_angle_deg = self.incidence_angle_deg
        self.reflection_angle_mrad = self.incidence_angle_mrad

class OWMirror(_OWMirror):
    name        = "Generic Mirror"
    description = "Shadow Mirror"
    icon        = "icons/plane_mirror.png"

    inputs = copy.deepcopy(_OWMirror.inputs)
    inputs.append(("PreRefl PreProcessor Data", PreReflPreProcessorData, "set_PreReflPreProcessorData"))
    inputs.append(("VLS-PGM PreProcessor Data", VlsPgmPreProcessorData, "set_VlsPgmPreProcessorData"))

    priority = 1.2

    def get_oe_type(self):
        return "mirror", "Mirror"

if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline
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
    ow = OWMirror()
    ow.set_shadow_data(get_test_beam())
    ow.modified_surface = 1
    ow.ms_defect_file_name = "/users/srio/Oasys/lens_profile_2D.h5"
    ow.modified_surface_tab_visibility()

    ow.show()
    a.exec_()
    ow.saveSettings()
