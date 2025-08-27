import numpy, copy, os

from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout
from PyQt5.QtCore import Qt

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog
from orangecontrib.shadow4.util.shadow4_util import ShadowPhysics
import orangecanvas.resources as resources

from syned.beamline.shape import Circle, Rectangle
from syned.beamline.element_coordinates import ElementCoordinates

from shadow4.beamline.optical_elements.refractors.s4_transfocator import S4Transfocator, S4TransfocatorElement

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData # TODO: remove
from orangecontrib.shadow4.util.shadow4_objects import PreReflPreProcessorData
from orangecontrib.shadow4.widgets.gui.ow_optical_element import OWOpticalElement


class OWTransfocator(OWOpticalElement):
    name = "Transfocator"
    description = "Transfocator"
    icon = "icons/transfocator.png"
    priority = 2.3

    NONE_SPECIFIED = "NONE SPECIFIED"

    n_lenses = Setting([4, 2])
    slots_empty = Setting([0, 0])
    piling_thickness = Setting([2.5, 2.5])

    empty_space_after_last_interface = Setting([0.0, 0.0])
    surface_shape = Setting([1, 1])
    convex_to_the_beam = Setting([0, 0])

    has_finite_diameter = Setting([0, 0])
    diameter = Setting([0.632, 0.894])

    is_cylinder = Setting([0, 0])
    cylinder_angle = Setting([0.0, 0.0])

    ri_calculation_mode = Setting([0, 0])
    prerefl_file = Setting([NONE_SPECIFIED, NONE_SPECIFIED])
    refraction_index = Setting([1.0, 1.0])
    attenuation_coefficient = Setting([0.0, 0.0])
    material = Setting(["Be", "Al"])
    density =  Setting([1.848, 2.7])

    radius = Setting([100.0, 200.0])
    thickness = Setting([30.0, 30.0])

    input_data = None

    inputs = copy.deepcopy(OWOpticalElement.inputs)
    inputs.append(("PreRefl PreProcessor Data", PreReflPreProcessorData, "set_PreReflPreProcessorData"))

    help_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui"), "misc", "crl_help.png")

    def __init__(self):
        super().__init__(has_footprint=False, show_tab_advanced_settings=False, show_tab_help=True)

    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True,
                                                  orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance",
                          "Source Plane Distance to First Interface (P) [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance",
                          "Last Interface Distance to Image plane (Q) [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="image_plane_distance")

    def create_basic_settings_subtabs(self, tabs_basic_settings):
        return oasysgui.createTabPage(tabs_basic_settings, "Transfocator")  # to be populated

    def populate_basic_setting_subtabs(self, basic_setting_subtabs):
        tabs_button_box = oasysgui.widgetBox(basic_setting_subtabs, "", addSpace=False, orientation="horizontal")
        btns = [gui.button(tabs_button_box, self, "Insert CRL Before", callback=self.crl_insert_before),
                gui.button(tabs_button_box, self, "Insert CRL After", callback=self.crl_insert_after),
                gui.button(tabs_button_box, self, "Remove CRL", callback=self.crl_remove)]
        for btn in btns: btn.setFixedHeight(40)

        self.tab_crls = oasysgui.tabWidget(basic_setting_subtabs)
        self.crl_box_array = []

        for index in range(len(self.material)):
            tab_crl = oasysgui.createTabPage(self.tab_crls, "CRL " + str(index + 1))

            crl_box = CRLBox(transfocator=self,
                             parent=tab_crl,
                             n_lenses=self.n_lenses[index],
                             slots_empty=self.slots_empty[index],
                             piling_thickness=self.piling_thickness[index],
                             empty_space_after_last_interface=self.empty_space_after_last_interface[index],
                             surface_shape=self.surface_shape[index],
                             convex_to_the_beam=self.convex_to_the_beam[index],
                             has_finite_diameter=self.has_finite_diameter[index],
                             diameter=self.diameter[index],
                             is_cylinder=self.is_cylinder[index],
                             cylinder_angle=self.cylinder_angle[index],
                             ri_calculation_mode=self.ri_calculation_mode[index],
                             prerefl_file=self.prerefl_file[index],
                             refraction_index=self.refraction_index[index],
                             attenuation_coefficient=self.attenuation_coefficient[index],
                             material=self.material[index],
                             density=self.density[index],
                             radius=self.radius[index],
                             thickness=self.thickness[index],
                             )

            self.crl_box_array.append(crl_box)

    def get_optical_element_instance(self):
        try:
            name = self.getNode().title
        except:
            name = "Transfocator"

        um_to_si = 1e-6
        mm_to_si = 1e-3

        if self.has_finite_diameter[0] == 0:
            boundary_shape = None
        elif self.has_finite_diameter[0] == 1:
            boundary_shape = Circle(radius=um_to_si * self.diameter[0] * 0.5)
        elif self.has_finite_diameter[0] == 2:
            rr = um_to_si * self.diameter[0] * 0.5
            boundary_shape = Rectangle() (x_left=-rr, x_right=rr, y_bottom=-rr, y_top=rr)


        n = len(self.n_lenses)
        cylinder_angle = [0] * n
        piling_thickness = [0] * n
        thickness = [0] * n
        radius = [0] * n
        for i in range(n):
            if self.is_cylinder[i] == 1: cylinder_angle[i] = self.cylinder_angle[i] + 1
            thickness[i] = self.thickness[i] * um_to_si
            piling_thickness[i] = self.piling_thickness[i] * mm_to_si
            radius[i] = self.radius[i] * um_to_si

        try:    name = self.getNode().title
        except: name = "Transfocator"

        optical_element = S4Transfocator(name=name,
                                        n_lens=self.n_lenses,
                                        thickness=thickness,  # syned stuff
                                        boundary_shape=boundary_shape,
                                        material=self.material,
                                        density=self.density,
                                        piling_thickness=piling_thickness,
                                        surface_shape=self.surface_shape,
                                        convex_to_the_beam=self.convex_to_the_beam,
                                        cylinder_angle=cylinder_angle,
                                        ri_calculation_mode=self.ri_calculation_mode,
                                        prerefl_file=self.prerefl_file,
                                        refraction_index=self.refraction_index,
                                        attenuation_coefficient=self.attenuation_coefficient,
                                        dabax=None,
                                        radius=radius,
                                        conic_coefficients1=[[0] * 10] * n,
                                        conic_coefficients2=[[0] * 10] * n,
                                        empty_space_after_last_interface=[0.0] * n,
                                        )
        return optical_element

    def get_beamline_element_instance(self):

        beamline_element = S4TransfocatorElement(optical_element=self.get_optical_element_instance(),
                                                 coordinates=self.get_coordinates_instance(),
                                                 movements=self.get_movements_instance(),
                                                 input_beam=self.input_data.beam)
        return beamline_element

    def get_movements_instance(self): return None

    def get_coordinates_instance(self):
        return ElementCoordinates(
                p=self.source_plane_distance,
                q=self.image_plane_distance,
                angle_radial=0.0,
                angle_azimuthal=0.0,
                angle_radial_out=numpy.pi,
                )

    def crl_insert_before(self):
        current_index = self.tab_crls.currentIndex()

        if ConfirmDialog.confirmed(parent=self, message="Confirm Insertion of a new element before " + self.tab_crls.tabText(current_index) + "?"):
            tab_crl = oasysgui.widgetBox(self.tab_crls, addToLayout=0, margin=4)
            crl_box = CRLBox(transfocator=self, parent=tab_crl)

            self.tab_crls.insertTab(current_index, tab_crl, "TEMP")
            self.crl_box_array.insert(current_index, crl_box)
            self.dumpSettings()

            for index in range(current_index, self.tab_crls.count()):
                self.tab_crls.setTabText(index, "CRL " + str(index + 1))

            self.tab_crls.setCurrentIndex(current_index)

    def crl_insert_after(self):
        current_index = self.tab_crls.currentIndex()

        if ConfirmDialog.confirmed(parent=self, message="Confirm Insertion of a new element after " + self.tab_crls.tabText(current_index) + "?"):
            tab_crl = oasysgui.widgetBox(self.tab_crls, addToLayout=0, margin=4)
            crl_box = CRLBox(transfocator=self, parent=tab_crl)

            if current_index == self.tab_crls.count() - 1:  # LAST
                self.tab_crls.addTab(tab_crl, "TEMP")
                self.crl_box_array.append(crl_box)
            else:
                self.tab_crls.insertTab(current_index + 1, tab_crl, "TEMP")
                self.crl_box_array.insert(current_index + 1, crl_box)

            self.dumpSettings()

            for index in range(current_index, self.tab_crls.count()):
                self.tab_crls.setTabText(index, "CRL " + str(index + 1))

            self.tab_crls.setCurrentIndex(current_index + 1)

    def crl_remove(self):
        if self.tab_crls.count() <= 1:
            QMessageBox.critical(self, "Error",
                                       "Remove not possible, transfocator needs at least 1 element",
                                       QMessageBox.Ok)
        else:
            current_index = self.tab_crls.currentIndex()

            if ConfirmDialog.confirmed(parent=self, message="Confirm Removal of " + self.tab_crls.tabText(current_index) + "?"):
                self.tab_crls.removeTab(current_index)
                self.crl_box_array.pop(current_index)
                self.dumpSettings()

                for index in range(current_index, self.tab_crls.count()):
                    self.tab_crls.setTabText(index, "CRL " + str(index + 1))

                self.tab_crls.setCurrentIndex(current_index)

    def dumpSettings(self):
        bkp_n_lenses = copy.deepcopy(self.n_lenses)
        bkp_slots_empty = copy.deepcopy(self.slots_empty)
        bkp_piling_thickness = copy.deepcopy(self.piling_thickness)
        bkp_empty_space_after_last_interface = copy.deepcopy(self.empty_space_after_last_interface)
        bkp_surface_shape = copy.deepcopy(self.surface_shape)
        bkp_convex_to_the_beam = copy.deepcopy(self.convex_to_the_beam)
        bkp_has_finite_diameter = copy.deepcopy(self.has_finite_diameter)
        bkp_diameter = copy.deepcopy(self.diameter)
        bkp_is_cylinder = copy.deepcopy(self.is_cylinder)
        bkp_cylinder_angle = copy.deepcopy(self.cylinder_angle)
        bkp_ri_calculation_mode = copy.deepcopy(self.ri_calculation_mode)
        bkp_prerefl_file = copy.deepcopy(self.prerefl_file)
        bkp_refraction_index = copy.deepcopy(self.refraction_index)
        bkp_attenuation_coefficient = copy.deepcopy(self.attenuation_coefficient)
        bkp_material = copy.deepcopy(self.material)
        bkp_density = copy.deepcopy(self.density)
        bkp_radius = copy.deepcopy(self.radius)
        bkp_thickness = copy.deepcopy(self.thickness)

        try:
            self.n_lenses = []
            self.slots_empty = []
            self.piling_thickness = []
            self.empty_space_after_last_interface = []
            self.surface_shape = []
            self.convex_to_the_beam = []
            self.has_finite_diameter = []
            self.diameter = []
            self.is_cylinder = []
            self.cylinder_angle = []
            self.ri_calculation_mode = []
            self.prerefl_file = []
            self.refraction_index = []
            self.attenuation_coefficient = []
            self.material = []
            self.density = []
            self.radius = []
            self.thickness = []

            for index in range(len(self.crl_box_array)):
                self.n_lenses.append(self.crl_box_array[index].n_lenses)
                self.slots_empty.append(self.crl_box_array[index].slots_empty)
                self.piling_thickness.append(self.crl_box_array[index].piling_thickness)
                self.empty_space_after_last_interface.append(self.crl_box_array[index].empty_space_after_last_interface)
                self.surface_shape.append(self.crl_box_array[index].surface_shape)
                self.convex_to_the_beam.append(self.crl_box_array[index].convex_to_the_beam)
                self.has_finite_diameter.append(self.crl_box_array[index].has_finite_diameter)
                self.diameter.append(self.crl_box_array[index].diameter)
                self.is_cylinder.append(self.crl_box_array[index].is_cylinder)
                self.cylinder_angle.append(self.crl_box_array[index].cylinder_angle)
                self.ri_calculation_mode.append(self.crl_box_array[index].ri_calculation_mode)
                self.prerefl_file.append(self.crl_box_array[index].prerefl_file)
                self.refraction_index.append(self.crl_box_array[index].refraction_index)
                self.attenuation_coefficient.append(self.crl_box_array[index].attenuation_coefficient)
                self.material.append(self.crl_box_array[index].material)
                self.density.append(self.crl_box_array[index].density)
                self.radius.append(self.crl_box_array[index].radius)
                self.thickness.append(self.crl_box_array[index].thickness)
        except:
            self.n_lenses = copy.deepcopy(bkp_n_lenses)
            self.slots_empty = copy.deepcopy(bkp_slots_empty)
            self.piling_thickness = copy.deepcopy(bkp_piling_thickness)
            self.empty_space_after_last_interface = copy.deepcopy(bkp_empty_space_after_last_interface)
            self.surface_shape = copy.deepcopy(bkp_surface_shape)
            self.convex_to_the_beam = copy.deepcopy(bkp_convex_to_the_beam)
            self.has_finite_diameter = copy.deepcopy(bkp_has_finite_diameter)
            self.diameter = copy.deepcopy(bkp_diameter)
            self.is_cylinder = copy.deepcopy(bkp_is_cylinder)
            self.cylinder_angle = copy.deepcopy(bkp_cylinder_angle)
            self.ri_calculation_mode = copy.deepcopy(bkp_ri_calculation_mode)
            self.prerefl_file = copy.deepcopy(bkp_prerefl_file)
            self.refraction_index = copy.deepcopy(bkp_refraction_index)
            self.attenuation_coefficient = copy.deepcopy(bkp_attenuation_coefficient)
            self.material = copy.deepcopy(bkp_material)
            self.density = copy.deepcopy(bkp_density)
            self.radius = copy.deepcopy(bkp_radius)
            self.thickness = copy.deepcopy(bkp_thickness)

    ##############################
    # SINGLE FIELDS SIGNALS
    ##############################

    def dump_n_lenses(self):
        bkp_n_lenses = copy.deepcopy(self.n_lenses)

        try:
            self.n_lenses = []

            for index in range(len(self.crl_box_array)):
                self.n_lenses.append(self.crl_box_array[index].n_lenses)
        except:
            self.n_lenses = copy.deepcopy(bkp_n_lenses)

    def dump_slots_empty(self):
        bkp_slots_empty = copy.deepcopy(self.slots_empty)

        try:
            self.slots_empty = []

            for index in range(len(self.crl_box_array)):
                self.slots_empty.append(self.crl_box_array[index].slots_empty)
        except:
            self.slots_empty = copy.deepcopy(bkp_slots_empty)

    def dump_piling_thickness(self):
        bkp_piling_thickness = copy.deepcopy(self.piling_thickness)

        try:
            self.piling_thickness = []

            for index in range(len(self.crl_box_array)):
                self.piling_thickness.append(self.crl_box_array[index].piling_thickness)
        except:
            self.piling_thickness = copy.deepcopy(bkp_piling_thickness)

    def dump_empty_space_after_last_interface(self):
        bkp_empty_space_after_last_interface = copy.deepcopy(self.empty_space_after_last_interface)

        try:
            self.empty_space_after_last_interface = []

            for index in range(len(self.crl_box_array)):
                self.empty_space_after_last_interface.append(self.crl_box_array[index].empty_space_after_last_interface)
        except:
            self.empty_space_after_last_interface = copy.deepcopy(bkp_empty_space_after_last_interface)

    def dump_surface_shape(self):
        bkp_surface_shape = copy.deepcopy(self.surface_shape)

        try:
            self.surface_shape = []

            for index in range(len(self.crl_box_array)):
                self.surface_shape.append(self.crl_box_array[index].surface_shape)
        except:
            self.surface_shape = copy.deepcopy(bkp_surface_shape)

    def dump_convex_to_the_beam(self):
        bkp_convex_to_the_beam = copy.deepcopy(self.convex_to_the_beam)

        try:
            self.convex_to_the_beam = []

            for index in range(len(self.crl_box_array)):
                self.convex_to_the_beam.append(self.crl_box_array[index].convex_to_the_beam)
        except:
            self.convex_to_the_beam = copy.deepcopy(bkp_convex_to_the_beam)

    def dump_has_finite_diameter(self):
        bkp_has_finite_diameter = copy.deepcopy(self.has_finite_diameter)

        try:
            self.has_finite_diameter = []

            for index in range(len(self.crl_box_array)):
                self.has_finite_diameter.append(self.crl_box_array[index].has_finite_diameter)
        except:
            self.has_finite_diameter = copy.deepcopy(bkp_has_finite_diameter)

    def dump_diameter(self):
        bkp_diameter = copy.deepcopy(self.diameter)

        try:
            self.diameter = []

            for index in range(len(self.crl_box_array)):
                self.diameter.append(self.crl_box_array[index].diameter)
        except:
            self.diameter = copy.deepcopy(bkp_diameter)

    def dump_is_cylinder(self):
        bkp_is_cylinder = copy.deepcopy(self.is_cylinder)

        try:
            self.is_cylinder = []

            for index in range(len(self.crl_box_array)):
                self.is_cylinder.append(self.crl_box_array[index].is_cylinder)
        except:
            self.is_cylinder = copy.deepcopy(bkp_is_cylinder)

    def dump_cylinder_angle(self):
        bkp_cylinder_angle = copy.deepcopy(self.cylinder_angle)

        try:
            self.cylinder_angle = []

            for index in range(len(self.crl_box_array)):
                self.cylinder_angle.append(self.crl_box_array[index].cylinder_angle)
        except:
            self.cylinder_angle = copy.deepcopy(bkp_cylinder_angle)

    def dump_ri_calculation_mode(self):
        bkp_ri_calculation_mode = copy.deepcopy(self.ri_calculation_mode)

        try:
            self.ri_calculation_mode = []

            for index in range(len(self.crl_box_array)):
                self.ri_calculation_mode.append(self.crl_box_array[index].ri_calculation_mode)
        except:
            self.ri_calculation_mode = copy.deepcopy(bkp_ri_calculation_mode)

    def dump_prerefl_file(self):
        bkp_prerefl_file = copy.deepcopy(self.prerefl_file)

        try:
            self.prerefl_file = []

            for index in range(len(self.crl_box_array)):
                self.prerefl_file.append(self.crl_box_array[index].prerefl_file)
        except:
            self.prerefl_file = copy.deepcopy(bkp_prerefl_file)

    def dump_refraction_index(self):
        bkp_refraction_index = copy.deepcopy(self.refraction_index)

        try:
            self.refraction_index = []

            for index in range(len(self.crl_box_array)):
                self.refraction_index.append(self.crl_box_array[index].refraction_index)
        except:
            self.refraction_index = copy.deepcopy(bkp_refraction_index)

    def dump_attenuation_coefficient(self):
        bkp_attenuation_coefficient = copy.deepcopy(self.attenuation_coefficient)

        try:
            self.attenuation_coefficient = []

            for index in range(len(self.crl_box_array)):
                self.attenuation_coefficient.append(self.crl_box_array[index].attenuation_coefficient)
        except:
            self.attenuation_coefficient = copy.deepcopy(bkp_attenuation_coefficient)

    def dump_material(self):
        bkp_material = copy.deepcopy(self.material)

        try:
            self.material = []

            for index in range(len(self.crl_box_array)):
                self.material.append(self.crl_box_array[index].material)
        except:
            self.material = copy.deepcopy(bkp_material)

        self.set_Density()

    def set_Density(self):
        index = self.tab_crls.currentIndex()
        mm = self.material[index]
        if not mm is None:
            if not mm.strip() == "":
                mm = mm.strip()
                new_density = ShadowPhysics.getMaterialDensity(mm)
                self.crl_box_array[index].density = new_density
                self.dump_density()
                # Next line is added to display the value in the widget: I do not know why this is not automatic!
                self.crl_box_array[index].le_density.setText(str(new_density))

    def dump_density(self):
        bkp_density = copy.deepcopy(self.density)

        try:
            self.density = []

            for index in range(len(self.crl_box_array)):
                self.density.append(self.crl_box_array[index].density)
        except:
            self.density = copy.deepcopy(bkp_density)


    def dump_radius(self):
        bkp_radius = copy.deepcopy(self.radius)

        try:
            self.radius = []

            for index in range(len(self.crl_box_array)):
                self.radius.append(self.crl_box_array[index].radius)
        except:
            self.radius = copy.deepcopy(bkp_radius)

    def dump_thickness(self):
        bkp_thickness = copy.deepcopy(self.thickness)

        try:
            self.thickness = []

            for index in range(len(self.crl_box_array)):
                self.thickness.append(self.crl_box_array[index].thickness)
        except:
            self.thickness = copy.deepcopy(bkp_thickness)


    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################

    def checkFields(self):
        for box in self.crl_box_array:
            box.checkFields()

    def setPreProcessorData(self, data): # TODO: remove
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                for box in self.crl_box_array:
                    box.prerefl_file = data.prerefl_data_file
                    box.le_prerefl_file.setText(data.prerefl_data_file)
                    box.ri_calculation_mode = 1
                    box.ri_calculation_mode_combo.setCurrentIndex(1)

                    box.set_ri_calculation_mode()
            else:
                QMessageBox.warning(self, "Warning", "Incompatible Preprocessor Data", QMessageBox.Ok)

                self.dump_prerefl_file()

    def set_PreReflPreProcessorData(self, data):
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                for box in self.crl_box_array:
                    box.prerefl_file = data.prerefl_data_file
                    box.le_prerefl_file.setText(data.prerefl_data_file)
                    box.ri_calculation_mode = 1
                    box.ri_calculation_mode_combo.setCurrentIndex(1)

                    box.set_ri_calculation_mode()
            else:
                QMessageBox.warning(self, "Warning", "Incompatible PreReflPreprocessor Data", QMessageBox.Ok)

                self.dump_prerefl_file()

    def setupUI(self):
        for box in self.crl_box_array:
            box.setupUI()


class CRLBox(QWidget):
    n_lenses = 30
    slots_empty = 0
    piling_thickness = 625e-4

    empty_space_after_last_interface = 0.0
    surface_shape = 1
    convex_to_the_beam = 1

    has_finite_diameter = 0
    diameter = 0.0

    is_cylinder = 1
    cylinder_angle = 0.0

    ri_calculation_mode = 0
    prerefl_file = OWTransfocator.NONE_SPECIFIED
    refraction_index = 1.0
    attenuation_coefficient = 0.0
    material = "Be"
    density = 1.848

    radius = 500e-2
    thickness = 0.001

    transfocator = None

    is_on_init = True

    def __init__(self,
                 transfocator=None,
                 parent=None,
                 n_lenses=30,
                 slots_empty=0,
                 piling_thickness=625e-4,
                 # p=0.0,
                 # q=0.0,
                 empty_space_after_last_interface=0.0,
                 surface_shape=1,
                 convex_to_the_beam=1,
                 has_finite_diameter=0,
                 diameter=0.0,
                 is_cylinder=1,
                 cylinder_angle=0.0,
                 ri_calculation_mode=0,
                 prerefl_file=OWTransfocator.NONE_SPECIFIED,
                 refraction_index=1.0,
                 attenuation_coefficient=0.0,
                 material="Be",
                 density=1.848,
                 radius=500e-2,
                 thickness=0.001,
                 ):
        super().__init__(parent)

        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self.setFixedWidth(470)
        self.setFixedHeight(700)

        self.transfocator = transfocator

        self.n_lenses = n_lenses
        self.slots_empty = slots_empty
        self.piling_thickness = piling_thickness
        self.empty_space_after_last_interface = empty_space_after_last_interface

        self.surface_shape = surface_shape
        self.convex_to_the_beam = convex_to_the_beam
        self.has_finite_diameter = has_finite_diameter
        self.diameter = diameter
        self.is_cylinder = is_cylinder
        self.cylinder_angle = cylinder_angle

        self.ri_calculation_mode = ri_calculation_mode
        self.prerefl_file = prerefl_file
        self.refraction_index = refraction_index
        self.attenuation_coefficient = attenuation_coefficient
        self.material = material
        self.density = density

        self.radius = radius
        self.thickness = thickness

        tabs0 = oasysgui.tabWidget(self, height=420, width=self.transfocator.CONTROL_AREA_WIDTH-35)

        tabs = oasysgui.widgetBox(tabs0, "", addSpace=False, orientation="vertical",
                                     width=self.transfocator.CONTROL_AREA_WIDTH - 45)

        crl_box = tabs

        oasysgui.lineEdit(crl_box, self, "n_lenses", "Number of lenses", tooltip="n_lenses[i]", labelWidth=260, valueType=int,
                          orientation="horizontal", callback=self.transfocator.dump_n_lenses)

        self.le_empty_space_after_last_interface = oasysgui.lineEdit(crl_box, self, "empty_space_after_last_interface",
                                    "Empty space after last CRL interface [m]", tooltip="empty_space_after_last_interface[i]",
                                    labelWidth=290, valueType=float, orientation="horizontal",
                                    callback=self.transfocator.dump_empty_space_after_last_interface)

        # optical constants
        ###############
        self.ri_calculation_mode_combo = gui.comboBox(crl_box, self, "ri_calculation_mode", tooltip="ri_calculation_mode[i]",
                                                      label="Refraction Index calculation mode", labelWidth=260,
                                                      items=["User Parameters", "Prerefl File", \
                                                             "Internal (using xraylib)", "Internal (using dabax)"],
                                                      sendSelectedValue=False, orientation="horizontal",
                                                      callback=self.set_ri_calculation_mode)

        self.calculation_mode_1 = oasysgui.widgetBox(crl_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.calculation_mode_1, self, "refraction_index", "Refraction index", tooltip="refraction_index[i]",
                          labelWidth=260, valueType=float, orientation="horizontal",
                          callback=self.transfocator.dump_refraction_index)
        oasysgui.lineEdit(self.calculation_mode_1, self, "attenuation_coefficient", "Attenuation coefficient [m-1]", labelWidth=260, valueType=float,
                           orientation="horizontal", callback=self.transfocator.dump_attenuation_coefficient)

        self.calculation_mode_2 = oasysgui.widgetBox(crl_box, "", addSpace=False, orientation="vertical")
        file_box = oasysgui.widgetBox(self.calculation_mode_2, "", addSpace=False, orientation="horizontal", height=20)
        self.le_prerefl_file = oasysgui.lineEdit(file_box, self, "prerefl_file", "File Prerefl", tooltip="prerefl_file[i]",
                                                 labelWidth=100, valueType=str, orientation="horizontal",
                                                 callback=self.transfocator.dump_prerefl_file)

        self.calculation_mode_3 = oasysgui.widgetBox(crl_box, "", addSpace=False, orientation="vertical")
        mat_box = oasysgui.widgetBox(self.calculation_mode_3, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(mat_box, self, "material", "Lens material", tooltip="material[i]",
                          labelWidth=90, valueType=str, orientation="horizontal",
                          callback=self.transfocator.dump_material)
        self.le_density = oasysgui.lineEdit(mat_box, self, "density", "density [g/cm3]", tooltip="density[i]",
                        labelWidth=110, valueType=float, orientation="horizontal",
                        callback=self.transfocator.dump_density)

        gui.button(file_box, self, "...", callback=self.selectFilePrerefl)
        self.set_ri_calculation_mode()

        ###############

        lens_box = tabs

        diameter_box_outer = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="horizontal")

        gui.comboBox(diameter_box_outer, self, "has_finite_diameter", label="Lens aperture", tooltip="has_finite_diameter[i]",
                     labelWidth=110, #labelWidth=260,
                     items=["Infinite", "Circular", "Square"], sendSelectedValue=False, orientation="horizontal", callback=self.set_diameter)

        self.diameter_box = oasysgui.widgetBox(diameter_box_outer, "", addSpace=False, orientation="vertical")
        self.diameter_box_empty = oasysgui.widgetBox(diameter_box_outer, "", addSpace=False, orientation="vertical", height=20)

        self.le_diameter = oasysgui.lineEdit(self.diameter_box, self, "diameter", " 'A' [\u03bcm]", tooltip="diameter[i]",
                                             labelWidth=80, #labelWidth=260,
                                             valueType=float, orientation="horizontal", callback=self.transfocator.dump_diameter)

        self.set_diameter()

        surface_shape_box_outer = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="horizontal")

        gui.comboBox(surface_shape_box_outer, self, "surface_shape", label="Surface Shape", #labelWidth=260,
                     tooltip="surface_shape[i]",
                     items=[ "Plane", "Sphere", "Paraboloid"], sendSelectedValue=False, orientation="horizontal",
                     callback=self.set_surface_shape)

        self.surface_shape_box = oasysgui.widgetBox(surface_shape_box_outer, "", addSpace=False, orientation="vertical")
        self.surface_shape_box_empty = oasysgui.widgetBox(surface_shape_box_outer, "", addSpace=False, orientation="vertical")

        self.le_radius = oasysgui.lineEdit(self.surface_shape_box, self, "radius", " 'R' [\u03bcm]", tooltip="radius[i]",
                                           labelWidth=80, #labelWidth=260,
                                           valueType=float, orientation="horizontal", callback=self.transfocator.dump_radius)

        self.set_surface_shape()

        self.le_thickness = oasysgui.lineEdit(lens_box, self, "thickness", "Apex Thickness 'at' [\u03bcm]", labelWidth=260,
                                                   valueType=float, orientation="horizontal", tooltip="thickness[i]",
                                                   callback=self.transfocator.dump_thickness)

        self.le_piling_thickness = oasysgui.lineEdit(lens_box, self, "piling_thickness", "Piling thickness 'pt' [mm]", labelWidth=260,
                                              valueType=float, orientation="horizontal", tooltip="piling_thickness[i]",
                                              callback=self.transfocator.dump_piling_thickness)

        gui.comboBox(oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=40),
                     self, "convex_to_the_beam", label="1st interface exposed to the beam",
                            tooltip="convex_to_the_beam[i]", labelWidth=310,
                     items=["Concave", "Convex"], sendSelectedValue=False, orientation="horizontal", callback=self.transfocator.dump_convex_to_the_beam)


        gui.comboBox(lens_box, self, "is_cylinder", label="Cylindrical", tooltip="is_cylinder[i]", labelWidth=310,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.set_cylindrical)

        self.box_cyl = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")
        self.box_cyl_empty = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)

        gui.comboBox(self.box_cyl, self, "cylinder_angle", tooltip="cylinder_angle[i]", label="Cylinder Angle (deg)",
                     labelWidth=260, items=["0 (Meridional)", "90 (Sagittal)"], sendSelectedValue=False,
                     orientation="horizontal", callback=self.transfocator.dump_cylinder_angle)

        self.set_cylindrical()

        self.is_on_init = False


    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def selectFilePrerefl(self):
        self.le_prerefl_file.setText(oasysgui.selectFileFromDialog(self, self.prerefl_file, "Select File Prerefl", file_extension_filter="Data Files (*.dat)"))

        self.prerefl_file = self.le_prerefl_file.text()
        self.transfocator.dump_prerefl_file()

    def get_cylinder_angle(self):
        if self.is_cylinder:
            if self.cylinder_angle == 0:
                return 0.0
            elif self.cylinder_angle == 1:
                return 90.0
            else:
                raise ValueError("Cylinder Angle")
        else:
            return None

    def get_diameter(self):
        if self.has_finite_diameter > 0:
            return self.diameter
        else:
            return None

    def get_prerefl_file(self):
        if self.ri_calculation_mode == 1:
            return congruence.checkFileName(self.prerefl_file)
        else:
            return None

    def set_surface_shape(self):
        self.surface_shape_box.setVisible(self.surface_shape != 0)
        self.surface_shape_box_empty.setVisible(self.surface_shape == 0)

        if not self.is_on_init: self.transfocator.dump_surface_shape()

    def set_diameter(self):
        self.diameter_box.setVisible(self.has_finite_diameter > 0)
        self.diameter_box_empty.setVisible(self.has_finite_diameter == 0)

        if not self.is_on_init: self.transfocator.dump_has_finite_diameter()

    def set_cylindrical(self):
        self.box_cyl.setVisible(self.is_cylinder == 1)
        self.box_cyl_empty.setVisible(self.is_cylinder == 0)
        if not self.is_on_init: self.transfocator.dump_is_cylinder()

    def set_ri_calculation_mode(self):
        self.calculation_mode_1.setVisible(self.ri_calculation_mode == 0)
        self.calculation_mode_2.setVisible(self.ri_calculation_mode == 1)
        self.calculation_mode_3.setVisible(self.ri_calculation_mode > 1)

        if not self.is_on_init: self.transfocator.dump_ri_calculation_mode()

    def checkFields(self):
        congruence.checkPositiveNumber(self.n_lenses, "Number of lenses")
        congruence.checkPositiveNumber(self.slots_empty, "Number of empty slots")
        congruence.checkPositiveNumber(self.piling_thickness, "Piling thickness")

        congruence.checkNumber(self.p, "P")
        congruence.checkNumber(self.q, "Q")

        if self.has_finite_diameter == 0:
            congruence.checkStrictlyPositiveNumber(self.diameter, "Diameter")

        if self.ri_calculation_mode == 0:
            congruence.checkPositiveNumber(self.refraction_index, "Refraction Index")
            congruence.checkPositiveNumber(self.attenuation_coefficient, "Attenuation Coefficient")
        elif self.ri_calculation_mode == 1:
            congruence.checkFile(self.prerefl_file)
        else: # todo: check material
            congruence.checkPositiveNumber(self.density, "Density [g/cm3]")

        congruence.checkStrictlyPositiveNumber(self.radius, "Radius")
        congruence.checkPositiveNumber(self.thickness, "Lens Thickness")

    def setupUI(self):
        self.set_surface_shape()
        self.set_diameter()
        self.set_cylindrical()
        self.set_ri_calculation_mode()

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
    ow = OWTransfocator()
    ow.view_type = 2
    ow.set_shadow_data(get_test_beam())

    ow.show()
    a.exec_()
    ow.saveSettings()