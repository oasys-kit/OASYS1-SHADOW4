import numpy
import sys
import xraylib

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from syned.beamline.optical_elements.crystals.crystal import DiffractionGeometry

from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal, S4PlaneCrystalElement
from shadow4.beamline.optical_elements.crystals.s4_sphere_crystal import S4SphereCrystal, S4SphereCrystalElement

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.widgets.gui.ow_optical_element_with_surface_shape import OWOpticalElementWithSurfaceShape

class OWCrystal(OWOpticalElementWithSurfaceShape):
    name = "Generic Crystal"
    description = "Shadow Crystal"
    icon = "icons/plane_crystal.png"

    priority = 1.3

    def get_oe_type(self):
        return "crystal", "Crystal"

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

    def __init__(self):
        super(OWCrystal, self).__init__()
        # with crystals no "internal surface parameters" allowed. Fix value and hide selecting combo:
        self.surface_shape_parameters = 1
        self.surface_shape_parameters_box.setVisible(False)

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
                                                "thickness", "Crystal thickness [m]",tooltip="thickness",
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
    # S4 objects
    #########################################################

    def get_optical_element_instance(self):

        if self.surface_shape_type > 0 and self.surface_shape_parameters == 0:
            raise ValueError("Curved crystal with internal calculation not allowed.")


        if self.surface_shape_type == 0:
            crystal = S4PlaneCrystal(
                name="Plane Crystal",
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
            )

        elif self.surface_shape_type == 1:
            print("FOCUSING DISTANCES: convexity:  ", numpy.logical_not(self.surface_curvature).astype(int))
            # print("FOCUSING DISTANCES: internal/external:  ", self.surface_shape_parameters)
            print("FOCUSING DISTANCES: radius:  ", self.spherical_radius)
            # print("FOCUSING DISTANCES: p:  ", self.get_focusing_p())
            # print("FOCUSING DISTANCES: q:  ", self.get_focusing_q())
            # print("FOCUSING DISTANCES: grazing angle:  ", self.get_focusing_grazing_angle())

            crystal = S4SphereCrystal(
                name="Sphere Crystal",
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
                # p_focus=self.get_focusing_p(),
                # q_focus=self.get_focusing_q(),
                # grazing_angle=self.get_focusing_grazing_angle(),
            )
        elif self.surface_shape_type == 2:
            raise ValueError("Curved crystal not implemented")
            # mirror = S4EllipsoidMirror(
            #     name="Ellipsoid Mirror",
            #     boundary_shape=self.get_boundary_shape(),
            #     surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
            #     is_cylinder=self.is_cylinder,
            #     cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
            #     convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
            #     min_axis=0.0,
            #     maj_axis=0.0,
            #     p_focus=self.get_focusing_p(),
            #     q_focus=self.get_focusing_q(),
            #     grazing_angle=self.get_focusing_grazing_angle(),
            #     # inputs related to mirror reflectivity
            #     f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
            #     f_refl=self.reflectivity_source,  # 0=prerefl file
            #                                     # 1=electric susceptibility
            #                                     # 2=user defined file (1D reflectivity vs angle)
            #                                     # 3=user defined file (1D reflectivity vs energy)
            #                                     # 4=user defined file (2D reflectivity vs energy and angle)
            #                                     # 5=direct calculation using xraylib
            #                                     # 6=direct calculation using dabax
            #     file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
            #     refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
            #     # refraction index (complex) for f_refl=1
            #     coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
            #     coating_density=self.coating_density,      # coating material density for f_refl=5,6
            #     coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            # )
        elif self.surface_shape_type == 3:
            raise ValueError("Curved crystal not implemented")
            # mirror = S4HyperboloidMirror(
            #     name="Hyperboloid Mirror",
            #     boundary_shape=self.get_boundary_shape(),
            #     surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
            #     is_cylinder=self.is_cylinder,
            #     cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
            #     convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
            #     min_axis=0.0,
            #     maj_axis=0.0,
            #     p_focus=self.get_focusing_p(),
            #     q_focus=self.get_focusing_q(),
            #     grazing_angle=self.get_focusing_grazing_angle(),
            #     # inputs related to mirror reflectivity
            #     f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
            #     f_refl=self.reflectivity_source,  # 0=prerefl file
            #                                     # 1=electric susceptibility
            #                                     # 2=user defined file (1D reflectivity vs angle)
            #                                     # 3=user defined file (1D reflectivity vs energy)
            #                                     # 4=user defined file (2D reflectivity vs energy and angle)
            #                                     # 5=direct calculation using xraylib
            #                                     # 6=direct calculation using dabax
            #     file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
            #     refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
            #     # refraction index (complex) for f_refl=1
            #     coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
            #     coating_density=self.coating_density,      # coating material density for f_refl=5,6
            #     coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            # )
        elif self.surface_shape_type == 4:
            raise ValueError("Curved crystal not implemented")
            # mirror = S4ParaboloidMirror(
            #     name="Paraboloid Mirror",
            #     boundary_shape=self.get_boundary_shape(),
            #     surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
            #     is_cylinder=self.is_cylinder,
            #     cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
            #     convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
            #     parabola_parameter=0.0,
            #     at_infinity=Side.SOURCE, #  Side:  SOURCE = 0  IMAGE = 1
            #     pole_to_focus=0.0,
            #     p_focus=self.get_focusing_p(),
            #     q_focus=self.get_focusing_q(),
            #     grazing_angle=self.get_focusing_grazing_angle(),
            #     # inputs related to mirror reflectivity
            #     f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
            #     f_refl=self.reflectivity_source,  # 0=prerefl file
            #                                     # 1=electric susceptibility
            #                                     # 2=user defined file (1D reflectivity vs angle)
            #                                     # 3=user defined file (1D reflectivity vs energy)
            #                                     # 4=user defined file (2D reflectivity vs energy and angle)
            #                                     # 5=direct calculation using xraylib
            #                                     # 6=direct calculation using dabax
            #     file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
            #     refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
            #     # refraction index (complex) for f_refl=1
            #     coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
            #     coating_density=self.coating_density,      # coating material density for f_refl=5,6
            #     coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            # )
        elif self.surface_shape_type == 5:
            raise ValueError("Curved crystal not implemented")
            # mirror = S4ToroidMirror(
            #     name="Toroid Mirror",
            #     boundary_shape=self.get_boundary_shape(),
            #     surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
            #     min_radius=0.1,
            #     maj_radius=1.0,
            #     p_focus=self.get_focusing_p(),
            #     q_focus=self.get_focusing_q(),
            #     grazing_angle=self.get_focusing_grazing_angle(),
            #     # inputs related to mirror reflectivity
            #     f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
            #     f_refl=self.reflectivity_source,  # 0=prerefl file
            #                                     # 1=electric susceptibility
            #                                     # 2=user defined file (1D reflectivity vs angle)
            #                                     # 3=user defined file (1D reflectivity vs energy)
            #                                     # 4=user defined file (2D reflectivity vs energy and angle)
            #                                     # 5=direct calculation using xraylib
            #                                     # 6=direct calculation using dabax
            #     file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
            #     refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
            #     # refraction index (complex) for f_refl=1
            #     coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
            #     coating_density=self.coating_density,      # coating material density for f_refl=5,6
            #     coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            # )
        elif self.surface_shape_type == 6:
            raise ValueError("Curved crystal not implemented")
            # mirror = S4ConicMirror(
            #     name="Conic coefficients Mirror",
            #     boundary_shape=self.get_boundary_shape(),
            #     conic_coefficients=[
            #          self.conic_coefficient_0,self.conic_coefficient_1,self.conic_coefficient_2,
            #          self.conic_coefficient_3,self.conic_coefficient_4,self.conic_coefficient_5,
            #          self.conic_coefficient_6,self.conic_coefficient_7,self.conic_coefficient_8,
            #          self.conic_coefficient_9],
            #     # inputs related to mirror reflectivity
            #     f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
            #     f_refl=self.reflectivity_source,  # 0=prerefl file
            #                                     # 1=electric susceptibility
            #                                     # 2=user defined file (1D reflectivity vs angle)
            #                                     # 3=user defined file (1D reflectivity vs energy)
            #                                     # 4=user defined file (2D reflectivity vs energy and angle)
            #                                     # 5=direct calculation using xraylib
            #                                     # 6=direct calculation using dabax
            #     file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
            #     refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
            #     # refraction index (complex) for f_refl=1
            #     coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
            #     coating_density=self.coating_density,      # coating material density for f_refl=5,6
            #     coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
            # )

        # if error is selected...

        # if self.modified_surface:
        #     return S4AdditionalNumericalMeshMirror(name="ideal + error Mirror",
        #                                            ideal_mirror=mirror,
        #                                            numerical_mesh_mirror=S4NumericalMeshMirror(
        #                                                surface_data_file=self.ms_defect_file_name,
        #                                                boundary_shape=None),
        #                                            )
        # else:
        #     return mirror


        return crystal

    def get_beamline_element_instance(self):

        if self.modified_surface:
            ValueError("Curved crystal not implemented")
            # return S4AdditionalNumericalMeshMirrorElement()
        else:
            if self.surface_shape_type == 0:   return S4PlaneCrystalElement()
            elif self.surface_shape_type == 1: return S4SphereCrystalElement()
            elif self.surface_shape_type == 2: ValueError("Curved crystal not implemented")
            elif self.surface_shape_type == 3: ValueError("Curved crystal not implemented")
            elif self.surface_shape_type == 4: ValueError("Curved crystal not implemented")
            elif self.surface_shape_type == 5: ValueError("Curved crystal not implemented")
            elif self.surface_shape_type == 6: ValueError("Curved crystal not implemented")

        # optical_element = S4PlaneCrystalElement()
        #
        # if self.surface_shape_type > 0: ValueError("Curved crystal not implemented")  # todo: complete for curved crystals
        #
        # # if self.surface_shape_type == 0: optical_element = S4PlaneCrystalElement()
        # '''
        # elif self.surface_shape_type == 1: optical_element = S4SphereCrystalElement()
        # elif self.surface_shape_type == 2: optical_element = S4EllipsoidCrystalElement()
        # elif self.surface_shape_type == 3: optical_element = S4HyperboloidCrystalElement()
        # elif self.surface_shape_type == 4: optical_element = S4ParaboloidCrystalElement()
        # elif self.surface_shape_type == 5: optical_element = S4ToroidCrystalElement()
        # '''
        #
        # return optical_element


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
