import numpy
import sys
import copy

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from shadow4.beamline.optical_elements.multilayers.s4_toroid_multilayer import S4ToroidMultilayer, S4ToroidMultilayerElement
from shadow4.beamline.optical_elements.multilayers.s4_conic_multilayer import S4ConicMultilayer, S4ConicMultilayerElement
from shadow4.beamline.optical_elements.multilayers.s4_plane_multilayer import S4PlaneMultilayer, S4PlaneMultilayerElement
from shadow4.beamline.optical_elements.multilayers.s4_ellipsoid_multilayer import S4EllipsoidMultilayer, S4EllipsoidMultilayerElement
from shadow4.beamline.optical_elements.multilayers.s4_hyperboloid_multilayer import S4HyperboloidMultilayer, S4HyperboloidMultilayerElement
from shadow4.beamline.optical_elements.multilayers.s4_paraboloid_multilayer import S4ParaboloidMultilayer, S4ParaboloidMultilayerElement
from shadow4.beamline.optical_elements.multilayers.s4_sphere_multilayer import S4SphereMultilayer, S4SphereMultilayerElement

from shadow4.beamline.optical_elements.multilayers.s4_numerical_mesh_multilayer import S4NumericalMeshMultilayer
from shadow4.beamline.optical_elements.multilayers.s4_additional_numerical_mesh_multilayer import S4AdditionalNumericalMeshMultilayer
from shadow4.beamline.optical_elements.multilayers.s4_additional_numerical_mesh_multilayer import S4AdditionalNumericalMeshMultilayerElement

from orangecontrib.shadow4.widgets.gui.ow_optical_element_with_surface_shape import OWOpticalElementWithSurfaceShape, SUBTAB_INNER_BOX_WIDTH
# from orangecontrib.shadow4.util.shadow4_objects import ShadowData, PreReflPreProcessorData, VlsPgmPreProcessorData
from orangecontrib.shadow4.util.shadow4_objects import MLayerPreProcessorData

class _OWMultilayer(OWOpticalElementWithSurfaceShape):

    reflectivity_source           = Setting(4) # f_refl
    file_refl                     = Setting("<none>")

    structure = Setting('[C,Pt]x30+Si')
    period = Setting(50.0)
    Gamma = Setting(0.4)

    def __init__(self, switch_icons=True):
        super(_OWMultilayer, self).__init__(switch_icons=switch_icons)

        self.reflection_angle_deg_le.setEnabled(False)
        self.reflection_angle_rad_le.setEnabled(False)


    def create_basic_settings_specific_subtabs(self, tabs_basic_setting): return oasysgui.createTabPage(tabs_basic_setting, "Reflectivity")

    def populate_basic_settings_specific_subtabs(self, specific_subtabs):
        subtab_reflectivity = specific_subtabs
        self.populate_tab_reflectivity(subtab_reflectivity)

    def populate_tab_reflectivity(self, subtab_reflectivity):
        box_1 = oasysgui.widgetBox(subtab_reflectivity, "Multilayer Reflectivity", addSpace=True, orientation="vertical", width=SUBTAB_INNER_BOX_WIDTH)

        reflectivity_flag_box = oasysgui.widgetBox(box_1, "", addSpace=False, orientation="vertical")
        gui.comboBox(reflectivity_flag_box, self, "reflectivity_source", label="Reflectivity source", labelWidth=150,
                     items=["pre_mlayer File",
                            "file 1D: (reflectivity vs angle)",
                            "file 1D: (reflectivity vs energy)",
                            "file 2D: (reflectivity vs energy and angle)",
                            "Internal (using xraylib)",
                            "Internal (using Dabax)",
                            ],
                     sendSelectedValue=False, orientation="horizontal",
                     tooltip="reflectivity_source", callback=self.reflectivity_tab_visibility)

        self.file_refl_box = oasysgui.widgetBox(reflectivity_flag_box, "", addSpace=False, orientation="horizontal", height=25)
        self.le_file_refl = oasysgui.lineEdit(self.file_refl_box, self, "file_refl", "File Name", labelWidth=100,
                                              valueType=str, orientation="horizontal", tooltip="file_refl")
        gui.button(self.file_refl_box, self, "...", callback=self.select_file_refl)

        self.box_xraylib_dabax = oasysgui.widgetBox(reflectivity_flag_box, "", addSpace=False, orientation="vertical") #, height=25)

        oasysgui.lineEdit(self.box_xraylib_dabax, self, "structure",
                          "ML structure [odd,even]xN+Sub: ", labelWidth=220, valueType=str,
                          orientation="horizontal", tooltip="structure")
        oasysgui.lineEdit(self.box_xraylib_dabax, self, "period",
                          "Bilayer thick [A]: ", labelWidth=180, valueType=float,
                          orientation="horizontal", tooltip="period")
        oasysgui.lineEdit(self.box_xraylib_dabax, self, "Gamma",
                          "Gamma [even/total]: ", labelWidth=180, valueType=float,
                          orientation="horizontal", tooltip="Gamma")

        oasysgui.widgetLabel(self.box_xraylib_dabax, "(Use preprocessor for graded ML & more options)")

        self.reflectivity_tab_visibility()

    #########################################################
    # Reflectvity Methods
    #########################################################
    def reflectivity_tab_visibility(self):
        self.file_refl_box.setVisible(False)

        if self.reflectivity_source < 4:
            self.file_refl_box.setVisible(True)
        else:
            self.file_refl_box.setVisible(False)

        if self.reflectivity_source >= 4:
            self.box_xraylib_dabax.setVisible(True)
        else:
            self.box_xraylib_dabax.setVisible(False)

    def select_file_refl(self):
        self.le_file_refl.setText(oasysgui.selectFileFromDialog(self, self.file_refl, "Select File with Reflectivity")) #, file_extension_filter="Data Files (*.dat)"))

    #########################################################
    # preprocessor
    #########################################################
    def set_MLayerPreProcessorData(self, data):
        if data is not None:
            if data.mlayer_data_file != MLayerPreProcessorData.NONE:
                self.file_refl = data.mlayer_data_file
                self.reflectivity_source = 0
                self.reflectivity_tab_visibility()
            else:
                QMessageBox.warning(self, "Warning", "Incompatible Preprocessor Data", QMessageBox.Ok)

    #########################################################
    # S4 objects
    #########################################################

    def get_optical_element_instance(self):

        # possible change of limits to match with the surface data file (must be done before creating multilayer)
        if self.modified_surface: self.congruence_surface_data_file()

        #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
        #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
        #  Side:  SOURCE = 0  IMAGE = 1

        try:    name = self.getNode().title
        except: name = "Multilayer"

        if self.surface_shape_type == 0:
            multilayer = S4PlaneMultilayer(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                f_refl=self.reflectivity_source,
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                structure=self.structure,
                period=self.period,
                Gamma=self.Gamma,
            )
        elif self.surface_shape_type == 1:
            print("FOCUSING DISTANCES: convexity:  ", numpy.logical_not(self.surface_curvature).astype(int))
            print("FOCUSING DISTANCES: internal/external:  ", self.surface_shape_parameters)
            print("FOCUSING DISTANCES: radius:  ", self.spherical_radius)
            print("FOCUSING DISTANCES: p:  ", self.get_focusing_p())
            print("FOCUSING DISTANCES: q:  ", self.get_focusing_q())
            print("FOCUSING DISTANCES: grazing angle:  ", self.get_focusing_grazing_angle())

            multilayer = S4SphereMultilayer(
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
                # inputs related to multilayer reflectivity
                f_refl=self.reflectivity_source,
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                structure=self.structure,
                period=self.period,
                Gamma=self.Gamma,
            )
        elif self.surface_shape_type == 2:
            multilayer = S4EllipsoidMultilayer(
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
                # inputs related to multilayer reflectivity
                f_refl=self.reflectivity_source,
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                structure=self.structure,
                period=self.period,
                Gamma=self.Gamma,
            )
        elif self.surface_shape_type == 3:
            multilayer = S4HyperboloidMultilayer(
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
                # inputs related to multilayer reflectivity
                f_refl=self.reflectivity_source,
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                structure=self.structure,
                period=self.period,
                Gamma=self.Gamma,
            )
        elif self.surface_shape_type == 4:
            multilayer = S4ParaboloidMultilayer(
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
                # inputs related to multilayer reflectivity
                f_refl=self.reflectivity_source,
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                structure=self.structure,
                period=self.period,
                Gamma=self.Gamma,
            )
        elif self.surface_shape_type == 5:
            multilayer = S4ToroidMultilayer(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                min_radius=self.torus_minor_radius,
                maj_radius=self.torus_major_radius, # tangential radius
                f_torus=self.toroidal_multilayer_pole_location,
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to multilayer reflectivity
                f_refl=self.reflectivity_source,
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                structure=self.structure,
                period=self.period,
                Gamma=self.Gamma,
            )
        elif self.surface_shape_type == 6:
            multilayer = S4ConicMultilayer(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                conic_coefficients=[
                     self.conic_coefficient_0,self.conic_coefficient_1,self.conic_coefficient_2,
                     self.conic_coefficient_3,self.conic_coefficient_4,self.conic_coefficient_5,
                     self.conic_coefficient_6,self.conic_coefficient_7,self.conic_coefficient_8,
                     self.conic_coefficient_9],
                # inputs related to multilayer reflectivity
                f_refl=self.reflectivity_source,
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                structure=self.structure,
                period=self.period,
                Gamma=self.Gamma,
            )

        # if error is selected...

        if self.modified_surface:
            return S4AdditionalNumericalMeshMultilayer(name=name,
                                                   ideal_multilayer=multilayer,
                                                   numerical_mesh_multilayer=S4NumericalMeshMultilayer(
                                                       surface_data_file=self.ms_defect_file_name,
                                                       boundary_shape=None),
                                                   )
        else:
            return multilayer

    def get_beamline_element_instance(self):
        if self.modified_surface:
            return S4AdditionalNumericalMeshMultilayerElement()
        else:
            if self.surface_shape_type == 0:   return S4PlaneMultilayerElement()
            elif self.surface_shape_type == 1: return S4SphereMultilayerElement()
            elif self.surface_shape_type == 2: return S4EllipsoidMultilayerElement()
            elif self.surface_shape_type == 3: return S4HyperboloidMultilayerElement()
            elif self.surface_shape_type == 4: return S4ParaboloidMultilayerElement()
            elif self.surface_shape_type == 5: return S4ToroidMultilayerElement()
            elif self.surface_shape_type == 6: return S4ConicMultilayerElement()


    def calculate_incidence_angle_mrad(self):
        super().calculate_incidence_angle_mrad()

        self.reflection_angle_deg = self.incidence_angle_deg
        self.reflection_angle_mrad = self.incidence_angle_mrad

    def calculate_incidence_angle_deg(self):
        super().calculate_incidence_angle_deg()

        self.reflection_angle_deg = self.incidence_angle_deg
        self.reflection_angle_mrad = self.incidence_angle_mrad

class OWMultilayer(_OWMultilayer):
    name        = "Generic Multilayer"
    description = "Shadow Multilayer"
    icon        = "icons/plane_multilayer.png"

    inputs = copy.deepcopy(_OWMultilayer.inputs)
    inputs.append(("MLayer PreProcessor Data", MLayerPreProcessorData, "set_MLayerPreProcessorData"))

    priority = 1.391

    def get_oe_type(self):
        return "multilayer", "Multilayer"

if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline
    from orangecontrib.shadow4.util.shadow4_objects import ShadowData
    def get_test_beam():
        from shadow4.beamline.s4_beamline import S4Beamline

        beamline = S4Beamline()

        #
        #
        #
        from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
        light_source = SourceGeometrical(name='SourceGeometrical', nrays=5000, seed=5676561)
        light_source.set_spatial_type_point()
        light_source.set_depth_distribution_off()
        light_source.set_angular_distribution_uniform(hdiv1=-0.000000, hdiv2=0.000000, vdiv1=-0.000000, vdiv2=0.000000)
        light_source.set_energy_distribution_uniform(value_min=12000.000000, value_max=13000.000000, unit='eV')
        light_source.set_polarization(polarization_degree=1.000000, phase_diff=0.000000, coherent_beam=0)
        beam = light_source.get_beam()

        beamline.set_light_source(light_source)

        return ShadowData(beam=beam, beamline=S4Beamline(light_source=light_source))

    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWMultilayer()
    ow.file_refl = '/home/srio/Oasys/mlayer.dat'
    ow.set_shadow_data(get_test_beam())
    # ow.modified_surface = 1
    # ow.ms_defect_file_name = "/users/srio/Oasys/lens_profile_2D.h5"
    # ow.modified_surface_tab_visibility()
    ow.show()
    a.exec_()
    ow.saveSettings()
