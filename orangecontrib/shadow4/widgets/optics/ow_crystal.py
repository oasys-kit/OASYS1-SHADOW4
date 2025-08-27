import numpy
import sys
import xraylib

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from syned.beamline.optical_elements.crystals.crystal import DiffractionGeometry

from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal, S4PlaneCrystalElement
from shadow4.beamline.optical_elements.crystals.s4_sphere_crystal import S4SphereCrystal, S4SphereCrystalElement
from shadow4.beamline.optical_elements.crystals.s4_paraboloid_crystal import S4ParaboloidCrystal, S4ParaboloidCrystalElement
from shadow4.beamline.optical_elements.crystals.s4_ellipsoid_crystal import S4EllipsoidCrystal, S4EllipsoidCrystalElement
from shadow4.beamline.optical_elements.crystals.s4_hyperboloid_crystal import S4HyperboloidCrystal, S4HyperboloidCrystalElement
from shadow4.beamline.optical_elements.crystals.s4_conic_crystal import S4ConicCrystal, S4ConicCrystalElement
from shadow4.beamline.optical_elements.crystals.s4_toroid_crystal import S4ToroidCrystal, S4ToroidCrystalElement
from shadow4.beamline.optical_elements.crystals.s4_numerical_mesh_crystal import S4NumericalMeshCrystal, S4NumericalMeshCrystalElement
from shadow4.beamline.optical_elements.crystals.s4_additional_numerical_mesh_crystal import S4AdditionalNumericalMeshCrystal, S4AdditionalNumericalMeshCrystalElement


from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.widgets.gui.ow_optical_element_with_surface_shape import OWOpticalElementWithSurfaceShape

from orangecontrib.shadow4.util.shadow4_objects import BraggPreProcessorData
import copy

class _OWCrystal(OWOpticalElementWithSurfaceShape):
    # name = "Generic Crystal"
    # description = "Shadow Crystal"
    # icon = "icons/plane_crystal.png"
    #
    # priority = 1.3
    #
    # def get_oe_type(self):
    #     return "crystal", "Crystal"
    #
    # inputs = copy.deepcopy(OWOpticalElementWithSurfaceShape.inputs)
    # inputs.append(("Bragg PreProcessor Data", BraggPreProcessorData, "setBraggProcessorData"))

    #########################################################
    # crystal
    #########################################################

    # diffraction_geometry = Setting(0)
    diffraction_calculation = Setting(0)

    file_diffraction_profile = Setting("diffraction_profile.dat")
    user_defined_bragg_angle = Setting(14.223)
    user_defined_asymmetry_angle = Setting(0.0)

    CRYSTALS = xraylib.Crystal_GetCrystalsList()
    user_defined_crystal = Setting(32)

    user_defined_h = Setting(1)
    user_defined_k = Setting(1)
    user_defined_l = Setting(1)

    file_crystal_parameters = Setting("bragg.dat")
    crystal_auto_setting = Setting(1)
    units_in_use = Setting(0)
    photon_energy = Setting(8000.0)
    photon_wavelength = Setting(1.0)

    # mosaic_crystal = Setting(0)
    # angle_spread_FWHM = Setting(0.0)
    # seed_for_mosaic = Setting(1626261131)

    is_thick = Setting(1)
    thickness = Setting(1e-3)

    # johansson_geometry = Setting(0)
    # johansson_radius = Setting(0.0)

    asymmetric_cut = Setting(0)
    planes_angle = Setting(0.0)
    below_onto_bragg_planes = Setting(-1)
    method_efields_management = Setting(0)

    def __init__(self):
        super(_OWCrystal, self).__init__()
        # with crystals no "internal surface parameters" allowed. Fix value and hide selecting combo:
        self.surface_shape_parameters = 1
        self.surface_shape_internal_external_box.setVisible(False)

    def create_basic_settings_specific_subtabs(self, tabs_basic_setting):
        subtab_crystal_diffraction = oasysgui.createTabPage(tabs_basic_setting, "Diffraction")    # to be populated
        subtab_crystal_geometry = oasysgui.createTabPage(tabs_basic_setting, "Geometry")    # to be populated

        return subtab_crystal_diffraction, subtab_crystal_geometry

    def populate_basic_settings_specific_subtabs(self, specific_subtabs):
        subtab_crystal_diffraction, subtab_crystal_geometry = specific_subtabs

        #########################################################
        # Basic Settings / Crystal Diffraction
        #########################################################
        self.populate_tab_crystal_diffraction(subtab_crystal_diffraction)

        #########################################################
        # Basic Settings / Crystal Geometry
        #########################################################
        self.populate_tab_crystal_geometry(subtab_crystal_geometry)

    def populate_tab_crystal_diffraction(self, subtab_crystal_diffraction):
        crystal_box = oasysgui.widgetBox(subtab_crystal_diffraction, "Diffraction Settings", addSpace=True, orientation="vertical")

        # gui.comboBox(crystal_box, self, "diffraction_geometry", tooltip="diffraction_geometry",
        #              label="Diffraction Geometry", labelWidth=250,
        #              items=["Bragg", "Laue *NYI*"],
        #              sendSelectedValue=False, orientation="horizontal", callback=self.crystal_diffraction_tab_visibility)


        gui.comboBox(crystal_box, self, "diffraction_calculation", tooltip="diffraction_calculation",
                     label="Diffraction Profile", labelWidth=120,
                     items=["Calculated internally with xraylib",
                            "Calculated internally with dabax *NYI*",
                            "bragg preprocessor file v1",
                            "bragg preprocessor file v2",
                            "User File (energy-independent) *NYI*",
                            "User File (energy-dependent) *NYI*"],
                     sendSelectedValue=False, orientation="horizontal",
                     callback=self.crystal_diffraction_tab_visibility)

        gui.separator(crystal_box)


        ## preprocessor file
        self.crystal_box_1 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=False, orientation="horizontal", height=30)

        self.le_file_crystal_parameters = oasysgui.lineEdit(file_box, self, "file_crystal_parameters",
                                                            "File (preprocessor)", tooltip="file_crystal_parameters",
                                                            labelWidth=150, valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.select_file_crystal_parameters)

        ## xoppy file
        self.crystal_box_2 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical")


        crystal_box_2_1 = oasysgui.widgetBox(self.crystal_box_2, "", addSpace=False, orientation="horizontal")

        self.le_file_diffraction_profile = oasysgui.lineEdit(crystal_box_2_1, self,
                                                             "file_diffraction_profile", "File (user Diff Profile)",
                                                             tooltip="file_diffraction_profile",
                                                             labelWidth=120, valueType=str, orientation="horizontal")
        gui.button(crystal_box_2_1, self, "...", callback=self.select_file_diffraction_profile)

        oasysgui.lineEdit(self.crystal_box_2, self, "user_defined_bragg_angle",
                          "Bragg Angle respect to the surface [deg]", tooltip="user_defined_bragg_angle",
                          labelWidth=260, valueType=float,
                          orientation="horizontal", callback=self.crystal_diffraction_tab_visibility)
        oasysgui.lineEdit(self.crystal_box_2, self, "user_defined_asymmetry_angle", "Asymmetry angle [deg]",
                          tooltip="user_defined_asymmetry_angle",
                          labelWidth=260, valueType=float, orientation="horizontal",
                          callback=self.crystal_diffraction_tab_visibility)

        ##  parameters for internal calculations / xoppy file
        self.crystal_box_3 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical") #, height=340)

        gui.comboBox(self.crystal_box_3, self, "user_defined_crystal", tooltip="user_defined_crystal",
                     label="Crystal", addSpace=True,
                     items=self.CRYSTALS, sendSelectedValue=False, orientation="horizontal", labelWidth=260)

        box_miller = oasysgui.widgetBox(self.crystal_box_3, "", orientation="horizontal", width=350)
        oasysgui.lineEdit(box_miller, self, "user_defined_h", tooltip="user_defined_h",
                          label="Miller Indices [h k l]", addSpace=True,
                          valueType=int, labelWidth=200, orientation="horizontal")
        oasysgui.lineEdit(box_miller, self, "user_defined_k", tooltip="user_defined_k",
                          addSpace=True, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box_miller, self, "user_defined_l", tooltip="user_defined_l",
                          addSpace=True, valueType=int, orientation="horizontal")


        ## autosetting
        self.crystal_box_4 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical") #, height=240)

        gui.comboBox(self.crystal_box_4, self, "crystal_auto_setting", tooltip="crystal_auto_setting",
                     label="Auto setting", labelWidth=350, items=["No", "Yes"],
                     callback=self.crystal_diffraction_tab_visibility, sendSelectedValue=False, orientation="horizontal")

        gui.separator(self.crystal_box_4, height=10)

        ##
        self.autosetting_box = oasysgui.widgetBox(self.crystal_box_4, "", addSpace=False,
                                                  orientation="vertical")
        self.autosetting_box_empty = oasysgui.widgetBox(self.crystal_box_4, "", addSpace=False,
                                                        orientation="vertical")

        self.autosetting_box_units = oasysgui.widgetBox(self.autosetting_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.autosetting_box_units, self, "units_in_use", tooltip="units_in_use", label="Units in use",
                     labelWidth=260, items=["eV", "Angstroms"],
                     callback=self.crystal_diffraction_tab_visibility, sendSelectedValue=False, orientation="horizontal")

        self.autosetting_box_units_1 = oasysgui.widgetBox(self.autosetting_box_units, "", addSpace=False,
                                                          orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_1, self, "photon_energy", "Set photon energy [eV]",
                          tooltip="photon_energy", labelWidth=260,
                          valueType=float, orientation="horizontal")

        self.autosetting_box_units_2 = oasysgui.widgetBox(self.autosetting_box_units, "", addSpace=False,
                                                          orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_2, self, "photon_wavelength", "Set wavelength [Å]",
                          tooltip="photon_wavelength", labelWidth=260,
                          valueType=float, orientation="horizontal")


        #
        advanced_box = oasysgui.widgetBox(subtab_crystal_diffraction, "Advanced Settings", addSpace=True, orientation="vertical")

        gui.comboBox(advanced_box, self, "method_efields_management", tooltip="method_efields_management",
                     label="manage electric fields", labelWidth=160,
                     items=["via Jones calculus (S4)",
                            "via rotations (S3)"],
                     sendSelectedValue=False, orientation="horizontal",
                     callback=self.crystal_diffraction_tab_visibility)


        self.crystal_diffraction_tab_visibility()

    def populate_tab_crystal_geometry(self, subtab_crystal_geometry):
        # mosaic_box = oasysgui.widgetBox(subtab_crystal_geometry, "Geometric Parameters", addSpace=True, orientation="vertical")
        #
        # gui.comboBox(mosaic_box, self, "mosaic_crystal", tooltip="mosaic_crystal", label="Mosaic Crystal **deleted**", labelWidth=355,
        #              items=["No", "Yes"],
        #              callback=self.crystal_geometry_tab_visibility, sendSelectedValue=False, orientation="horizontal")
        #
        # gui.separator(mosaic_box, height=10)

        # self.mosaic_box_1 = oasysgui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")
        #
        self.asymmetric_cut_box = oasysgui.widgetBox(subtab_crystal_geometry, "", addSpace=False, orientation="vertical",
                                                     height=110)

        self.asymmetric_cut_combo = gui.comboBox(self.asymmetric_cut_box, self, "asymmetric_cut",
                                                 tooltip="asymmetric_cut", label="Asymmetric cut",
                                                 labelWidth=355,
                                                 items=["No", "Yes"],
                                                 callback=self.crystal_geometry_tab_visibility, sendSelectedValue=False,
                                                 orientation="horizontal")

        self.asymmetric_cut_box_1 = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False, orientation="vertical")
        self.asymmetric_cut_box_1_empty = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False,
                                                             orientation="vertical")

        oasysgui.lineEdit(self.asymmetric_cut_box_1, self, "planes_angle", "Planes angle [deg]",
                          tooltip="planes_angle", labelWidth=260,
                          valueType=float, orientation="horizontal")

        self.asymmetric_cut_box_1_order = oasysgui.widgetBox(self.asymmetric_cut_box_1, "", addSpace=False,
                                                             orientation="vertical")

        # oasysgui.lineEdit(self.asymmetric_cut_box_1_order, self,
        #                   "below_onto_bragg_planes", "Below[-1]/onto[1] bragg planes **deleted**",
        #                   tooltip="below_onto_bragg_planes",
        #                   labelWidth=260, valueType=float, orientation="horizontal")

        self.thickness_box = oasysgui.widgetBox(subtab_crystal_geometry, "", addSpace=False, orientation="vertical",
                                                     height=110)

        self.thickness_combo = gui.comboBox(self.thickness_box, self, "is_thick",
                                                 tooltip="is_thick", label="Thick crystal approx.",
                                                 labelWidth=355,
                                                 items=["No", "Yes"],
                                                 callback=self.crystal_geometry_tab_visibility, sendSelectedValue=False,
                                                 orientation="horizontal")

        self.thickness_box_1 = oasysgui.widgetBox(self.thickness_box, "", addSpace=False, orientation="vertical")
        self.thickness_box_1_empty = oasysgui.widgetBox(self.thickness_box_1, "", addSpace=False,
                                                             orientation="vertical")

        self.le_thickness_1 = oasysgui.lineEdit(self.thickness_box_1, self,
                                                "thickness", "Crystal thickness [m]", tooltip="thickness",
                                                valueType=float, labelWidth=260, orientation="horizontal")

        # self.set_BraggLaue()

        # gui.separator(self.mosaic_box_1)

        # self.johansson_box = oasysgui.widgetBox(self.mosaic_box_1, "", addSpace=False, orientation="vertical", height=100)
        #
        # gui.comboBox(self.johansson_box, self, "johansson_geometry", tooltip="johansson_geometry",
        #              label="Johansson Geometry **deleted**", labelWidth=355, items=["No", "Yes"],
        #              callback=self.crystal_geometry_tab_visibility, sendSelectedValue=False, orientation="horizontal")
        #
        # self.johansson_box_1 = oasysgui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")
        # self.johansson_box_1_empty = oasysgui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")
        #
        # self.le_johansson_radius = oasysgui.lineEdit(self.johansson_box_1, self, "johansson_radius", "Johansson radius",
        #                                              tooltip="johansson_radius",
        #                                              labelWidth=260, valueType=float, orientation="horizontal")
        #
        # self.mosaic_box_2 = oasysgui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")
        #
        # oasysgui.lineEdit(self.mosaic_box_2, self, "angle_spread_FWHM", "Angle spread FWHM [deg]",
        #                   tooltip="angle_spread_FWHM", labelWidth=260,
        #                   valueType=float, orientation="horizontal")
        # self.le_thickness_2 = oasysgui.lineEdit(self.mosaic_box_2, self, "thickness", "Thickness",
        #                                         tooltip="thickness", labelWidth=260,
        #                                         valueType=float, orientation="horizontal")
        # oasysgui.lineEdit(self.mosaic_box_2, self, "seed_for_mosaic", "Seed for mosaic [>10^5]",
        #                   tooltip="seed_for_mosaic", labelWidth=260,
        #                   valueType=float, orientation="horizontal")

        # self.set_Mosaic()

        self.crystal_geometry_tab_visibility()

    #########################################################
    # Crystal Methods
    #########################################################

    def crystal_diffraction_tab_visibility(self):
        # self.set_BraggLaue()  #todo: to be deleted
        self.set_diffraction_calculation()
        self.set_autosetting()
        self.set_units_in_use()

    def crystal_geometry_tab_visibility(self):
        # self.set_mosaic()
        self.set_asymmetric_cut()
        self.set_thickness()
        # self.set_johansson_geometry()


    # todo: change next methods name from CamelCase to undercore...
    # def set_BraggLaue(self):
    #     self.asymmetric_cut_box_1_order.setVisible(self.diffraction_geometry==1) #LAUE
    #     if self.diffraction_geometry==1:
    #         self.asymmetric_cut = 1
    #         self.set_AsymmetricCut()
    #         self.asymmetric_cut_combo.setEnabled(False)
    #     else:
    #         self.asymmetric_cut_combo.setEnabled(True)

    def set_diffraction_calculation(self):
        self.crystal_box_1.setVisible(False)
        self.crystal_box_2.setVisible(False)
        self.crystal_box_3.setVisible(False)

        if (self.diffraction_calculation == 0):   # internal xraylib
            self.crystal_box_3.setVisible(True)
        elif (self.diffraction_calculation == 1): # internal
            self.crystal_box_3.setVisible(True)
        elif (self.diffraction_calculation == 2): # preprocessor bragg v1
            self.crystal_box_1.setVisible(True)
        elif (self.diffraction_calculation == 3): # preprocessor bragg v2
            self.crystal_box_1.setVisible(True)
        elif (self.diffraction_calculation == 4): # user file, E-independent
            self.crystal_box_2.setVisible(True)
        elif (self.diffraction_calculation == 5): # user file, E-dependent
            self.crystal_box_2.setVisible(True)

        if self.diffraction_calculation in (4,5):
            self.incidence_angle_deg_le.setEnabled(True)
            self.incidence_angle_rad_le.setEnabled(True)
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)

    def select_file_crystal_parameters(self):
        self.le_file_crystal_parameters.setText(oasysgui.selectFileFromDialog(self, self.file_crystal_parameters, "Select File With Crystal Parameters"))

    def set_autosetting(self):
        self.autosetting_box_empty.setVisible(self.crystal_auto_setting == 0)
        self.autosetting_box.setVisible(self.crystal_auto_setting == 1)

        if self.crystal_auto_setting == 0:
            self.incidence_angle_deg_le.setEnabled(True)
            self.incidence_angle_rad_le.setEnabled(True)
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)
        else:
            self.incidence_angle_deg_le.setEnabled(False)
            self.incidence_angle_rad_le.setEnabled(False)
            self.reflection_angle_deg_le.setEnabled(False)
            self.reflection_angle_rad_le.setEnabled(False)
            self.set_units_in_use()

    def set_units_in_use(self):
        self.autosetting_box_units_1.setVisible(self.units_in_use == 0)
        self.autosetting_box_units_2.setVisible(self.units_in_use == 1)

    def select_file_diffraction_profile(self):
        self.le_file_diffraction_profile.setText(oasysgui.selectFileFromDialog(self, self.file_diffraction_profile, "Select File With User Defined Diffraction Profile"))

    # def set_mosaic(self):
    #     self.mosaic_box_1.setVisible(self.mosaic_crystal == 0)
    #     self.mosaic_box_2.setVisible(self.mosaic_crystal == 1)
    #
    #     if self.mosaic_crystal == 0:
    #         self.set_asymmetric_cut()
    #         self.set_johansson_geometry()

    def set_asymmetric_cut(self):
        self.asymmetric_cut_box_1.setVisible(self.asymmetric_cut == 1)
        self.asymmetric_cut_box_1_empty.setVisible(self.asymmetric_cut == 0)

    def set_thickness(self):
        self.thickness_box_1.setVisible(self.is_thick == 0)
        self.thickness_box_1_empty.setVisible(self.is_thick == 1)

    # def set_johansson_geometry(self):
    #     self.johansson_box_1.setVisible(self.johansson_geometry == 1)
    #     self.johansson_box_1_empty.setVisible(self.johansson_geometry == 0)

    #########################################################
    # Preprocessors
    #########################################################

    def setBraggProcessorData(self, data):
        if data is not None:
            if data.bragg_data_file != BraggPreProcessorData.NONE:
                self.file_crystal_parameters = data.bragg_data_file
                self.diffraction_calculation = 3
                self.crystal_diffraction_tab_visibility()
            else:
                QMessageBox.warning(self, "Warning", "Incompatible Preprocessor Data", QMessageBox.Ok)

    #########################################################
    # S4 objects
    #########################################################

    def get_optical_element_instance(self):

        if self.surface_shape_type > 0 and self.surface_shape_parameters == 0:
            raise ValueError("Curved crystal with internal calculation not allowed.")

        try:    name = self.getNode().title
        except: name = "Crystal"

        if self.surface_shape_type == 0:
            crystal = S4PlaneCrystal(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                material=self.CRYSTALS[self.user_defined_crystal],
                miller_index_h=self.user_defined_h,  #todo: check if this is needed if material_constants_library_flag in (2,3)
                miller_index_k=self.user_defined_k,  #todo: check if this is needed if material_constants_library_flag in (2,3)
                miller_index_l=self.user_defined_l,  #todo: check if this is needed if material_constants_library_flag in (2,3)
                asymmetry_angle=0.0 if not self.asymmetric_cut else numpy.radians(self.planes_angle),
                is_thick=self.is_thick,
                thickness=self.thickness,
                f_central=self.crystal_auto_setting,
                f_phot_cent=self.units_in_use,
                phot_cent=(self.photon_energy if (self.units_in_use == 0) else self.photon_wavelength),
                file_refl=self.file_crystal_parameters,
                f_bragg_a=True if self.asymmetric_cut else False,
                f_ext=0,
                material_constants_library_flag=self.diffraction_calculation,
                method_efields_management=self.method_efields_management,
            )

        elif self.surface_shape_type == 1:
            print("FOCUSING DISTANCES: convexity:  ", numpy.logical_not(self.surface_curvature).astype(int))
            print("FOCUSING DISTANCES: radius:  ", self.spherical_radius)

            crystal = S4SphereCrystal(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                material=self.CRYSTALS[self.user_defined_crystal],
                miller_index_h=self.user_defined_h,
                miller_index_k=self.user_defined_k,
                miller_index_l=self.user_defined_l,
                asymmetry_angle=0.0 if not self.asymmetric_cut else numpy.radians(self.planes_angle),
                is_thick=self.is_thick,
                thickness=self.thickness,
                f_central=self.crystal_auto_setting,
                f_phot_cent=self.units_in_use,
                phot_cent=(self.photon_energy if (self.units_in_use == 0) else self.photon_wavelength),
                file_refl=self.file_crystal_parameters,
                f_bragg_a=True if self.asymmetric_cut else False,
                f_ext=0,
                material_constants_library_flag=self.diffraction_calculation,
                radius=self.spherical_radius,
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
            )
        elif self.surface_shape_type == 2:
            crystal = S4EllipsoidCrystal(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                material=self.CRYSTALS[self.user_defined_crystal],
                miller_index_h=self.user_defined_h,
                miller_index_k=self.user_defined_k,
                miller_index_l=self.user_defined_l,
                asymmetry_angle=0.0 if not self.asymmetric_cut else numpy.radians(self.planes_angle),
                is_thick=self.is_thick,
                thickness=self.thickness,
                f_central=self.crystal_auto_setting,
                f_phot_cent=self.units_in_use,
                phot_cent=(self.photon_energy if (self.units_in_use == 0) else self.photon_wavelength),
                file_refl=self.file_crystal_parameters,
                f_bragg_a=True if self.asymmetric_cut else False,
                f_ext=0,
                material_constants_library_flag=self.diffraction_calculation,
                min_axis=self.ellipse_hyperbola_semi_minor_axis * 2, # todo: check factor 2
                maj_axis=self.ellipse_hyperbola_semi_major_axis * 2, # todo: check factor 2
                pole_to_focus=self.angle_of_majax_and_pole, # todo: change variable name,
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
            )
        elif self.surface_shape_type == 3:
            crystal = S4HyperboloidCrystal(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                material=self.CRYSTALS[self.user_defined_crystal],
                miller_index_h=self.user_defined_h,
                miller_index_k=self.user_defined_k,
                miller_index_l=self.user_defined_l,
                asymmetry_angle=0.0 if not self.asymmetric_cut else numpy.radians(self.planes_angle),
                is_thick=self.is_thick,
                thickness=self.thickness,
                f_central=self.crystal_auto_setting,
                f_phot_cent=self.units_in_use,
                phot_cent=(self.photon_energy if (self.units_in_use == 0) else self.photon_wavelength),
                file_refl=self.file_crystal_parameters,
                f_bragg_a=True if self.asymmetric_cut else False,
                f_ext=0,
                material_constants_library_flag=self.diffraction_calculation,
                min_axis=self.ellipse_hyperbola_semi_minor_axis * 2, # todo: check factor 2
                maj_axis=self.ellipse_hyperbola_semi_major_axis * 2, # todo: check factor 2
                pole_to_focus=self.angle_of_majax_and_pole, # todo: change variable name
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
            )
        elif self.surface_shape_type == 4:
            crystal = S4ParaboloidCrystal(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                material=self.CRYSTALS[self.user_defined_crystal],
                miller_index_h=self.user_defined_h,
                miller_index_k=self.user_defined_k,
                miller_index_l=self.user_defined_l,
                asymmetry_angle=0.0 if not self.asymmetric_cut else numpy.radians(self.planes_angle),
                is_thick=self.is_thick,
                thickness=self.thickness,
                f_central=self.crystal_auto_setting,
                f_phot_cent=self.units_in_use,
                phot_cent=(self.photon_energy if (self.units_in_use == 0) else self.photon_wavelength),
                file_refl=self.file_crystal_parameters,
                f_bragg_a=True if self.asymmetric_cut else False,
                f_ext=0,
                material_constants_library_flag=self.diffraction_calculation,
                at_infinity=self.focus_location,  # Side:  Side.SOURCE: SOURCE = 0  IMAGE = 1
                parabola_parameter=self.paraboloid_parameter,
                pole_to_focus=self.angle_of_majax_and_pole,
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
            )
        elif self.surface_shape_type == 5:
            crystal = S4ToroidCrystal(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                material=self.CRYSTALS[self.user_defined_crystal],
                miller_index_h=self.user_defined_h,
                miller_index_k=self.user_defined_k,
                miller_index_l=self.user_defined_l,
                asymmetry_angle=0.0 if not self.asymmetric_cut else numpy.radians(self.planes_angle),
                is_thick=self.is_thick,
                thickness=self.thickness,
                f_central=self.crystal_auto_setting,
                f_phot_cent=self.units_in_use,
                phot_cent=(self.photon_energy if (self.units_in_use == 0) else self.photon_wavelength),
                file_refl=self.file_crystal_parameters,
                f_bragg_a=True if self.asymmetric_cut else False,
                f_ext=0,
                material_constants_library_flag=self.diffraction_calculation,
                min_radius=self.torus_minor_radius,
                maj_radius=self.torus_major_radius,
                f_torus=self.toroidal_mirror_pole_location,
                # is_cylinder=self.is_cylinder,
                # cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                # convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
            )
        elif self.surface_shape_type == 6:
            crystal = S4ConicCrystal(
                name=name,
                boundary_shape=self.get_boundary_shape(),
                material=self.CRYSTALS[self.user_defined_crystal],
                miller_index_h=self.user_defined_h,
                miller_index_k=self.user_defined_k,
                miller_index_l=self.user_defined_l,
                asymmetry_angle=0.0 if not self.asymmetric_cut else numpy.radians(self.planes_angle),
                is_thick=self.is_thick,
                thickness=self.thickness,
                f_central=self.crystal_auto_setting,
                f_phot_cent=self.units_in_use,
                phot_cent=(self.photon_energy if (self.units_in_use == 0) else self.photon_wavelength),
                file_refl=self.file_crystal_parameters,
                f_bragg_a=True if self.asymmetric_cut else False,
                f_ext=0,
                material_constants_library_flag=self.diffraction_calculation,
                conic_coefficients=[
                     self.conic_coefficient_0,self.conic_coefficient_1,self.conic_coefficient_2,
                     self.conic_coefficient_3,self.conic_coefficient_4,self.conic_coefficient_5,
                     self.conic_coefficient_6,self.conic_coefficient_7,self.conic_coefficient_8,
                     self.conic_coefficient_9],
            )

        # if error is selected...

        if self.modified_surface:
            return S4AdditionalNumericalMeshCrystal(name=name,
                        ideal_crystal=crystal,
                        numerical_mesh_crystal=S4NumericalMeshCrystal(
                            surface_data_file=self.ms_defect_file_name,
                            boundary_shape=None,
                            material=self.CRYSTALS[self.user_defined_crystal],
                            miller_index_h=self.user_defined_h,
                            miller_index_k=self.user_defined_k,
                            miller_index_l=self.user_defined_l,
                            asymmetry_angle=0.0 if not self.asymmetric_cut else numpy.radians(self.planes_angle),
                            is_thick=self.is_thick,
                            thickness=self.thickness,
                            f_central=self.crystal_auto_setting,
                            f_phot_cent=self.units_in_use,
                            phot_cent=(self.photon_energy if (
                            self.units_in_use == 0) else self.photon_wavelength),
                            file_refl=self.file_crystal_parameters,
                            f_bragg_a=True if self.asymmetric_cut else False,
                            f_ext=0,
                            material_constants_library_flag=self.diffraction_calculation,
                            )
                        )
        else:
            return crystal



    def get_beamline_element_instance(self):

        if self.modified_surface:
            return S4AdditionalNumericalMeshCrystalElement()
        else:
            if self.surface_shape_type == 0:   return S4PlaneCrystalElement()
            elif self.surface_shape_type == 1: return S4SphereCrystalElement()
            elif self.surface_shape_type == 2: return S4EllipsoidCrystalElement()
            elif self.surface_shape_type == 3: return S4HyperboloidCrystalElement()
            elif self.surface_shape_type == 4: return S4ParaboloidCrystalElement()
            elif self.surface_shape_type == 5: return S4ToroidCrystalElement()
            elif self.surface_shape_type == 6: return S4ConicCrystalElement()

    def _post_trace_operations(self, output_beam, footprint, element, beamline):
        angle_radial, angle_radial_out, _ = element.get_coordinates().get_angles()

        self.incidence_angle_deg   = numpy.round(numpy.degrees(angle_radial),5)
        self.reflection_angle_deg  = numpy.round(numpy.degrees(angle_radial_out),5)
        self.incidence_angle_mrad  = numpy.round(1e3 * (numpy.pi / 2 - angle_radial),5)
        self.reflection_angle_mrad = numpy.round(1e3 * (numpy.pi / 2 - angle_radial_out),5)

class OWCrystal(_OWCrystal):
    name = "Generic Crystal"
    description = "Shadow Crystal"
    icon = "icons/plane_crystal.png"

    priority = 1.3

    def get_oe_type(self):
        return "crystal", "Crystal"

    inputs = copy.deepcopy(OWOpticalElementWithSurfaceShape.inputs)
    inputs.append(("Bragg PreProcessor Data", BraggPreProcessorData, "setBraggProcessorData"))

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
    ow = OWCrystal()
    ow.set_shadow_data(get_test_beam())
    ow.show()
    a.exec_()
    ow.saveSettings()
