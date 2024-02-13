

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
from shadow4.beamline.optical_elements.gratings.s4_numerical_mesh_grating import S4NumericalMeshGrating, S4NumericalMeshGratingElement
from shadow4.beamline.optical_elements.gratings.s4_additional_numerical_mesh_grating import S4AdditionalNumericalMeshGrating, S4AdditionalNumericalMeshGratingElement


from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.widgets.gui.ow_optical_element_with_surface_shape import OWOpticalElementWithSurfaceShape

from orangecontrib.shadow4.util.shadow4_objects import VlsPgmPreProcessorData
import copy

class OWGrating(OWOpticalElementWithSurfaceShape):
    name = "Generic Grating"
    description = "Shadow Grating"
    icon = "icons/plane_grating.png"

    priority = 1.390

    inputs = copy.deepcopy(OWOpticalElementWithSurfaceShape.inputs)
    inputs.append(("VLS-PGM PreProcessor Data", VlsPgmPreProcessorData, "setVlsPgmPreProcessorData"))

    def get_oe_type(self):
        return "grating", "Grating"

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
    # file_refl = Setting("")

    def __init__(self):
        super(OWGrating, self).__init__()
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

        #
        #
        # ## preprocessor file
        # self.crystal_box_1 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical")
        #
        # file_box = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=False, orientation="horizontal", height=30)
        #
        # self.le_file_crystal_parameters = oasysgui.lineEdit(file_box, self, "file_crystal_parameters",
        #                                                     "File (preprocessor)", tooltip="file_crystal_parameters",
        #                                                     labelWidth=150, valueType=str, orientation="horizontal")
        #
        # gui.button(file_box, self, "...", callback=self.select_file_crystal_parameters)
        #
        # ## xoppy file
        # self.crystal_box_2 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical")
        #
        #
        # crystal_box_2_1 = oasysgui.widgetBox(self.crystal_box_2, "", addSpace=False, orientation="horizontal")
        #
        # self.le_file_diffraction_profile = oasysgui.lineEdit(crystal_box_2_1, self,
        #                                                      "file_diffraction_profile", "File (user Diff Profile)",
        #                                                      tooltip="file_diffraction_profile",
        #                                                      labelWidth=120, valueType=str, orientation="horizontal")
        # gui.button(crystal_box_2_1, self, "...", callback=self.select_file_diffraction_profile)
        #
        # oasysgui.lineEdit(self.crystal_box_2, self, "user_defined_bragg_angle",
        #                   "Bragg Angle respect to the surface [deg]", tooltip="user_defined_bragg_angle",
        #                   labelWidth=260, valueType=float,
        #                   orientation="horizontal", callback=self.crystal_diffraction_tab_visibility)
        # oasysgui.lineEdit(self.crystal_box_2, self, "user_defined_asymmetry_angle", "Asymmetry angle [deg]",
        #                   tooltip="user_defined_asymmetry_angle",
        #                   labelWidth=260, valueType=float, orientation="horizontal",
        #                   callback=self.crystal_diffraction_tab_visibility)
        #
        # ##  parameters for internal calculations / xoppy file
        # self.crystal_box_3 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical") #, height=340)
        #
        # gui.comboBox(self.crystal_box_3, self, "user_defined_crystal", tooltip="user_defined_crystal",
        #              label="Crystal", addSpace=True,
        #              items=self.CRYSTALS, sendSelectedValue=False, orientation="horizontal", labelWidth=260)
        #
        # box_miller = oasysgui.widgetBox(self.crystal_box_3, "", orientation="horizontal", width=350)
        # oasysgui.lineEdit(box_miller, self, "user_defined_h", tooltip="user_defined_h",
        #                   label="Miller Indices [h k l]", addSpace=True,
        #                   valueType=int, labelWidth=200, orientation="horizontal")
        # oasysgui.lineEdit(box_miller, self, "user_defined_k", tooltip="user_defined_k",
        #                   addSpace=True, valueType=int, orientation="horizontal")
        # oasysgui.lineEdit(box_miller, self, "user_defined_l", tooltip="user_defined_l",
        #                   addSpace=True, valueType=int, orientation="horizontal")
        #
        #
        # ## autosetting
        # self.crystal_box_4 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical") #, height=240)
        #
        # gui.comboBox(self.crystal_box_4, self, "crystal_auto_setting", tooltip="crystal_auto_setting",
        #              label="Auto setting", labelWidth=350, items=["No", "Yes"],
        #              callback=self.crystal_diffraction_tab_visibility, sendSelectedValue=False, orientation="horizontal")
        #
        # gui.separator(self.crystal_box_4, height=10)
        #
        # ##
        # self.autosetting_box = oasysgui.widgetBox(self.crystal_box_4, "", addSpace=False,
        #                                           orientation="vertical")
        # self.autosetting_box_empty = oasysgui.widgetBox(self.crystal_box_4, "", addSpace=False,
        #                                                 orientation="vertical")
        #
        # self.autosetting_box_units = oasysgui.widgetBox(self.autosetting_box, "", addSpace=False, orientation="vertical")
        #
        # gui.comboBox(self.autosetting_box_units, self, "units_in_use", tooltip="units_in_use", label="Units in use",
        #              labelWidth=260, items=["eV", "Angstroms"],
        #              callback=self.crystal_diffraction_tab_visibility, sendSelectedValue=False, orientation="horizontal")
        #
        # self.autosetting_box_units_1 = oasysgui.widgetBox(self.autosetting_box_units, "", addSpace=False,
        #                                                   orientation="vertical")
        #
        # oasysgui.lineEdit(self.autosetting_box_units_1, self, "photon_energy", "Set photon energy [eV]",
        #                   tooltip="photon_energy", labelWidth=260,
        #                   valueType=float, orientation="horizontal")
        #
        # self.autosetting_box_units_2 = oasysgui.widgetBox(self.autosetting_box_units, "", addSpace=False,
        #                                                   orientation="vertical")
        #
        # oasysgui.lineEdit(self.autosetting_box_units_2, self, "photon_wavelength", "Set wavelength [Å]",
        #                   tooltip="photon_wavelength", labelWidth=260,
        #                   valueType=float, orientation="horizontal")
        #
        #
        self.grating_diffraction_tab_visibility()

    def populate_tab_grating_efficiency(self, subtab_grating_efficiency):
        pass

        # self.asymmetric_cut_box = oasysgui.widgetBox(subtab_crystal_geometry, "", addSpace=False, orientation="vertical",
        #                                              height=110)
        #
        # self.asymmetric_cut_combo = gui.comboBox(self.asymmetric_cut_box, self, "asymmetric_cut",
        #                                          tooltip="asymmetric_cut", label="Asymmetric cut",
        #                                          labelWidth=355,
        #                                          items=["No", "Yes"],
        #                                          callback=self.crystal_geometry_tab_visibility, sendSelectedValue=False,
        #                                          orientation="horizontal")
        #
        # self.asymmetric_cut_box_1 = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False, orientation="vertical")
        # self.asymmetric_cut_box_1_empty = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False,
        #                                                      orientation="vertical")
        #
        # oasysgui.lineEdit(self.asymmetric_cut_box_1, self, "planes_angle", "Planes angle [deg]",
        #                   tooltip="planes_angle", labelWidth=260,
        #                   valueType=float, orientation="horizontal")
        #
        # self.asymmetric_cut_box_1_order = oasysgui.widgetBox(self.asymmetric_cut_box_1, "", addSpace=False,
        #                                                      orientation="vertical")
        #
        # # oasysgui.lineEdit(self.asymmetric_cut_box_1_order, self,
        # #                   "below_onto_bragg_planes", "Below[-1]/onto[1] bragg planes **deleted**",
        # #                   tooltip="below_onto_bragg_planes",
        # #                   labelWidth=260, valueType=float, orientation="horizontal")
        #
        # self.thickness_box = oasysgui.widgetBox(subtab_crystal_geometry, "", addSpace=False, orientation="vertical",
        #                                              height=110)
        #
        # self.thickness_combo = gui.comboBox(self.thickness_box, self, "is_thick",
        #                                          tooltip="is_thick", label="Thick crystal approx.",
        #                                          labelWidth=355,
        #                                          items=["No", "Yes"],
        #                                          callback=self.crystal_geometry_tab_visibility, sendSelectedValue=False,
        #                                          orientation="horizontal")
        #
        # self.thickness_box_1 = oasysgui.widgetBox(self.thickness_box, "", addSpace=False, orientation="vertical")
        # self.thickness_box_1_empty = oasysgui.widgetBox(self.thickness_box_1, "", addSpace=False,
        #                                                      orientation="vertical")
        #
        # self.le_thickness_1 = oasysgui.lineEdit(self.thickness_box_1, self,
        #                                         "thickness", "Crystal thickness [m]",tooltip="thickness",
        #                                         valueType=float, labelWidth=260, orientation="horizontal")
        #
        # # self.set_BraggLaue()
        #
        # # gui.separator(self.mosaic_box_1)
        #
        # # self.johansson_box = oasysgui.widgetBox(self.mosaic_box_1, "", addSpace=False, orientation="vertical", height=100)
        # #
        # # gui.comboBox(self.johansson_box, self, "johansson_geometry", tooltip="johansson_geometry",
        # #              label="Johansson Geometry **deleted**", labelWidth=355, items=["No", "Yes"],
        # #              callback=self.crystal_geometry_tab_visibility, sendSelectedValue=False, orientation="horizontal")
        # #
        # # self.johansson_box_1 = oasysgui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")
        # # self.johansson_box_1_empty = oasysgui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")
        # #
        # # self.le_johansson_radius = oasysgui.lineEdit(self.johansson_box_1, self, "johansson_radius", "Johansson radius",
        # #                                              tooltip="johansson_radius",
        # #                                              labelWidth=260, valueType=float, orientation="horizontal")
        # #
        # # self.mosaic_box_2 = oasysgui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")
        # #
        # # oasysgui.lineEdit(self.mosaic_box_2, self, "angle_spread_FWHM", "Angle spread FWHM [deg]",
        # #                   tooltip="angle_spread_FWHM", labelWidth=260,
        # #                   valueType=float, orientation="horizontal")
        # # self.le_thickness_2 = oasysgui.lineEdit(self.mosaic_box_2, self, "thickness", "Thickness",
        # #                                         tooltip="thickness", labelWidth=260,
        # #                                         valueType=float, orientation="horizontal")
        # # oasysgui.lineEdit(self.mosaic_box_2, self, "seed_for_mosaic", "Seed for mosaic [>10^5]",
        # #                   tooltip="seed_for_mosaic", labelWidth=260,
        # #                   valueType=float, orientation="horizontal")
        #
        # # self.set_Mosaic()
        #
        # self.crystal_geometry_tab_visibility()

    #########################################################
    # Grating Methods
    #########################################################

    def setVlsPgmPreProcessorData(self, data):
        if data is not None:
            self.surface_shape_type = 0
            self.surface_shape_tab_visibility()

            self.source_plane_distance = data.d_mirror_to_grating/2 * 1e-3
            self.image_plane_distance = data.d_grating_to_exit_slits * 1e-3

            self.angles_respect_to = 0
            self.incidence_angle_deg = data.alpha
            self.reflection_angle_deg =data.beta
            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

            self.oe_orientation_angle = 2
            self.order = -1

            self.f_ruling = 1
            self.ruling = data.shadow_coeff_0 * 1e3
            self.ruling_coeff_linear = data.shadow_coeff_1 * 1e6
            self.ruling_coeff_quadratic = data.shadow_coeff_2 * 1e9
            self.ruling_coeff_cubic = data.shadow_coeff_3 * 1e12
            self.ruling_coeff_quartic = 0.0
            self.grating_diffraction_tab_visibility()


    def grating_diffraction_tab_visibility(self):
        self.grating_box_vls.setVisible(self.f_ruling==1)

    #
    # def crystal_geometry_tab_visibility(self):
    #     # self.set_mosaic()
    #     self.set_asymmetric_cut()
    #     self.set_thickness()
    #     # self.set_johansson_geometry()
    #
    # def set_diffraction_calculation(self):
    #     self.crystal_box_1.setVisible(False)
    #     self.crystal_box_2.setVisible(False)
    #     self.crystal_box_3.setVisible(False)
    #
    #     if (self.diffraction_calculation == 0):   # internal xraylib
    #         self.crystal_box_3.setVisible(True)
    #     elif (self.diffraction_calculation == 1): # internal
    #         self.crystal_box_3.setVisible(True)
    #     elif (self.diffraction_calculation == 2): # preprocessor bragg v1
    #         self.crystal_box_1.setVisible(True)
    #     elif (self.diffraction_calculation == 3): # preprocessor bragg v2
    #         self.crystal_box_1.setVisible(True)
    #     elif (self.diffraction_calculation == 4): # user file, E-independent
    #         self.crystal_box_2.setVisible(True)
    #     elif (self.diffraction_calculation == 5): # user file, E-dependent
    #         self.crystal_box_2.setVisible(True)
    #
    #     if self.diffraction_calculation in (4,5):
    #         self.incidence_angle_deg_le.setEnabled(True)
    #         self.incidence_angle_rad_le.setEnabled(True)
    #         self.reflection_angle_deg_le.setEnabled(True)
    #         self.reflection_angle_rad_le.setEnabled(True)
    #
    # def select_file_crystal_parameters(self):
    #     self.le_file_crystal_parameters.setText(oasysgui.selectFileFromDialog(self, self.file_crystal_parameters, "Select File With Crystal Parameters"))
    #
    # def set_autosetting(self):
    #     self.autosetting_box_empty.setVisible(self.crystal_auto_setting == 0)
    #     self.autosetting_box.setVisible(self.crystal_auto_setting == 1)
    #
    #     if self.crystal_auto_setting == 0:
    #         self.incidence_angle_deg_le.setEnabled(True)
    #         self.incidence_angle_rad_le.setEnabled(True)
    #         self.reflection_angle_deg_le.setEnabled(True)
    #         self.reflection_angle_rad_le.setEnabled(True)
    #     else:
    #         self.incidence_angle_deg_le.setEnabled(False)
    #         self.incidence_angle_rad_le.setEnabled(False)
    #         self.reflection_angle_deg_le.setEnabled(False)
    #         self.reflection_angle_rad_le.setEnabled(False)
    #         self.set_units_in_use()
    #
    # def set_units_in_use(self):
    #     self.autosetting_box_units_1.setVisible(self.units_in_use == 0)
    #     self.autosetting_box_units_2.setVisible(self.units_in_use == 1)
    #
    # def select_file_diffraction_profile(self):
    #     self.le_file_diffraction_profile.setText(oasysgui.selectFileFromDialog(self, self.file_diffraction_profile, "Select File With User Defined Diffraction Profile"))
    #
    #
    # def set_asymmetric_cut(self):
    #     self.asymmetric_cut_box_1.setVisible(self.asymmetric_cut == 1)
    #     self.asymmetric_cut_box_1_empty.setVisible(self.asymmetric_cut == 0)
    #
    # def set_thickness(self):
    #     self.thickness_box_1.setVisible(self.is_thick == 0)
    #     self.thickness_box_1_empty.setVisible(self.is_thick == 1)
    #


    #########################################################
    # S4 objects
    #########################################################

    def get_optical_element_instance(self):

        if self.surface_shape_type > 0 and self.surface_shape_parameters == 0:
            raise ValueError("Curved grating with internal calculation not allowed.")


        if self.surface_shape_type == 0:
            grating = S4PlaneGrating(
                name="Plane Grating",
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=0 if (self.f_ruling==0) else 5,
            )

        elif self.surface_shape_type == 1:
            print("FOCUSING DISTANCES: convexity:  ", numpy.logical_not(self.surface_curvature).astype(int))
            print("FOCUSING DISTANCES: radius:  ", self.spherical_radius)

            grating = S4SphereGrating(
                name="Sphere Grating",
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=0 if (self.f_ruling == 0) else 5,
                #
                surface_calculation=SurfaceCalculation.EXTERNAL,
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                radius=self.spherical_radius,
                p_focus=0.0,
                q_focus=0.0,
                grazing_angle=0.0,
            )
        elif self.surface_shape_type == 5:
            grating = S4ToroidGrating(
                name="Toroid Grating",
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=0 if (self.f_ruling == 0) else 5,
                #
                min_radius=self.torus_minor_radius,
                maj_radius=self.torus_major_radius,
                f_torus=self.toroidal_mirror_pole_location,
            )
        elif self.surface_shape_type == 6:
            grating = S4ConicGrating(
                name="Conic Grating",
                boundary_shape=self.get_boundary_shape(),
                ruling=self.ruling,
                ruling_coeff_linear=self.ruling_coeff_linear,
                ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                ruling_coeff_cubic=self.ruling_coeff_cubic,
                ruling_coeff_quartic=self.ruling_coeff_quartic,
                coating=None,
                coating_thickness=None,
                order=self.order,
                f_ruling=0 if (self.f_ruling == 0) else 5,
                conic_coefficients=[
                    self.conic_coefficient_0, self.conic_coefficient_1, self.conic_coefficient_2,
                    self.conic_coefficient_3, self.conic_coefficient_4, self.conic_coefficient_5,
                    self.conic_coefficient_6, self.conic_coefficient_7, self.conic_coefficient_8,
                    self.conic_coefficient_9],
            )
        else:
            raise NotImplementedError("surface_shape_type=%d not implemented " % self.urface_shape_type)
        #     crystal = S4ConicCrystal(
        #         name="Conic Crystal",
        #         boundary_shape=self.get_boundary_shape(),
        #         material=self.CRYSTALS[self.user_defined_crystal],
        #         miller_index_h=self.user_defined_h,
        #         miller_index_k=self.user_defined_k,
        #         miller_index_l=self.user_defined_l,
        #         asymmetry_angle=0.0 if not self.asymmetric_cut else numpy.radians(self.planes_angle),
        #         is_thick=self.is_thick,
        #         thickness=self.thickness,
        #         f_central=self.crystal_auto_setting,
        #         f_phot_cent=self.units_in_use,
        #         phot_cent=(self.photon_energy if (self.units_in_use == 0) else self.photon_wavelength),
        #         file_refl=self.file_crystal_parameters,
        #         f_bragg_a=True if self.asymmetric_cut else False,
        #         f_ext=0,
        #         material_constants_library_flag=self.diffraction_calculation,
        #         conic_coefficients=[
        #              self.conic_coefficient_0,self.conic_coefficient_1,self.conic_coefficient_2,
        #              self.conic_coefficient_3,self.conic_coefficient_4,self.conic_coefficient_5,
        #              self.conic_coefficient_6,self.conic_coefficient_7,self.conic_coefficient_8,
        #              self.conic_coefficient_9],
        #     )
        #
        # # if error is selected...

        if self.modified_surface:
            return S4AdditionalNumericalMeshGrating(name="ideal + error Grating",
                        ideal_grating=grating,
                        numerical_mesh_grating=S4NumericalMeshGrating(
                            surface_data_file=self.ms_defect_file_name,
                            boundary_shape=None,
                            name="Sphere Grating",
                            # boundary_shape=self.get_boundary_shape(),
                            ruling=self.ruling,
                            ruling_coeff_linear=self.ruling_coeff_linear,
                            ruling_coeff_quadratic=self.ruling_coeff_quadratic,
                            ruling_coeff_cubic=self.ruling_coeff_cubic,
                            ruling_coeff_quartic=self.ruling_coeff_quartic,
                            coating=None,
                            coating_thickness=None,
                            order=self.order,
                            f_ruling=0 if (self.f_ruling == 0) else 5,
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
            # elif self.surface_shape_type == 2: return S4EllipsoidCrystalElement()
            # elif self.surface_shape_type == 3: return S4HyperboloidCrystalElement()
            # elif self.surface_shape_type == 4: return S4ParaboloidCrystalElement()
            elif self.surface_shape_type == 5: return S4ToroidGratingElement()
            elif self.surface_shape_type == 6: return S4ConicGratingElement()
            else: raise NotImplementedError("surface_shape_type not yet implemented!")


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

