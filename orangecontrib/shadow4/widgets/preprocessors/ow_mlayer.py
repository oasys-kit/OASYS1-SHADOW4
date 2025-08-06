import os, sys

from PyQt5.QtWidgets import QLabel, QApplication, QMessageBox, QSizePolicy
from PyQt5.QtGui import QTextCursor, QIntValidator, QDoubleValidator, QPixmap
from PyQt5.QtCore import Qt

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from shadow4.physical_models.mlayer.mlayer import MLayer


from oasys.util.oasys_util import EmittingStream
from orangecontrib.shadow4.util.shadow4_objects import MLayerPreProcessorData
from orangecontrib.shadow4.util.shadow4_util import ShadowPhysics

from orangecontrib.shadow4.widgets.gui.plots import plot_data1D, plot_data2D


class OWMLayer(OWWidget):
    name = "MLayer"
    id = "pre_mlayer"
    description = "Calculation of multilayer mirror reflectivity profile"
    icon = "icons/premlayer.png"
    author = "M Sanchez del Rio"
    maintainer_email = "srio@esrf.eu"
    priority = 30
    category = ""
    keywords = ["preprocessor", "pre_mlayer"]

    outputs = [{"name":"MLayerPreProcessorData",
                "type":MLayerPreProcessorData,
                "doc":"MLayer PreProcessor Data",
                "id":"MLayerPreProcessorData"}]

    want_main_area = True

    #
    # Basic
    #
    FILE = Setting("mlayer.dat")
    E_MIN = Setting(5000.0)
    E_MAX = Setting(20000.0)

    flag_graded = Setting(0)

    structure = Setting('[W,B]x50+Si')
    THICKNESS = Setting(33.1)
    GAMMA = Setting(0.483)

    N_PAIRS = Setting(70)

    O_DENSITY = Setting("9.40")
    O_MATERIAL = Setting("Ru")
    ROUGHNESS_ODD = Setting(3.1)

    E_DENSITY = Setting("2.40")
    E_MATERIAL = Setting("B4C")
    ROUGHNESS_EVEN = Setting(3.3)

    S_DENSITY = Setting("2.33")
    S_MATERIAL = Setting("Si")

    #
    # graded
    #
    grade_coeffs_flag = Setting(0)

    AA0 = Setting(1.0)
    AA1 = Setting(0.0)
    AA2 = Setting(0.0)
    AA3 = Setting(0.0)

    ell_p = Setting(10.0)
    ell_q = Setting(3.0)
    ell_theta_deg = Setting(0.8)
    ell_length = Setting(0.1)
    ell_photon_energy = Setting(10000.0)

    #
    # Plots
    #
    plot_flag = Setting(0)
    scan_e_n = Setting(100)
    scan_e_from = Setting(5000.0)
    scan_e_to = Setting(10000.0)
    scan_a0 = Setting(5.0)

    scan_a_n = Setting(100)
    scan_a_from = Setting(0)
    scan_a_to = Setting(10.0)
    scan_e0 = Setting(8000.0)

    graded_depth_text_list = Setting("[\n[10,10,0.5,0,0],\n[15,20,0.6,0,0],\n]")

    IMAGE_WIDTH  = 860
    IMAGE_HEIGHT = 545

    MAX_WIDTH          = 1320
    MAX_HEIGHT         = 700
    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT   = 630

    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui"), "misc", "premlayer_usage.png")

    mlayer_instance = None

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(self.MAX_WIDTH)
        self.setFixedHeight(self.MAX_HEIGHT)

        gui.separator(self.controlArea)

        box0 = gui.widgetBox(self.controlArea, "",orientation="horizontal")

        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(35)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        tab_out = oasysgui.createTabPage(self.main_tabs, "Output")

        self.plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots (optional scan)")


        #
        #
        #
        tab_input = oasysgui.createTabPage(tabs_setting, "Basic Settings")
        self.populate_tab_basic_settings(tab_input)

        tab_input_2 = oasysgui.createTabPage(tabs_setting, "Graded-ML")
        self.populate_tab_graded(tab_input_2)

        tab_input_3 = oasysgui.createTabPage(tabs_setting, "Plots")
        self.populate_tab_plots(tab_input_3)

        tab_input_4 = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        self.populate_tab_use_of_widget(tab_input_4)


        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.TABS_AREA_HEIGHT)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)

        self.set_visibility()

    def populate_tab_basic_settings(self, tab_input):
        #
        # Basic Settings
        #
        box = gui.widgetBox(tab_input, "", orientation="vertical")

        box_file = oasysgui.widgetBox(box, "", addSpace=True, orientation="horizontal", height=25)
        self.le_FILE = oasysgui.lineEdit(box_file, self, "FILE",
                                         label="File name (for SHADOW): ", addSpace=True, labelWidth=150, orientation="horizontal")
        gui.button(box_file, self, "...", callback=self.selectFile)


        box_e = gui.widgetBox(box, "", orientation="horizontal")
        oasysgui.lineEdit(box_e, self, "E_MIN", label='Min Energy [eV]', tooltip="E_MIN", addSpace=True,
                          valueType=float, labelWidth=125, orientation="horizontal")

        oasysgui.lineEdit(box_e, self, "E_MAX", label='Max', tooltip="E_MAX", addSpace=True,
                          valueType=float, labelWidth=55, orientation="horizontal")



        gui.comboBox(box, self, "flag_graded", label="graded ML", tooltip="flag_graded", addSpace=True,
                     items=['No (Constant)', 'laterally graded', 'depth graded', 'both'],
                     valueType=int, orientation="horizontal", labelWidth=270, callback=self.set_visibility)


        #
        # structure
        #
        self.box_structure = gui.widgetBox(tab_input, "", orientation="vertical")

        oasysgui.lineEdit(self.box_structure, self, "structure", label="ML structure [Odd,Even]xN+Substrate", tooltip="structure", addSpace=True,
                          labelWidth=250, orientation="horizontal", callback=self.set_structure)


        box_thick_gamma = oasysgui.widgetBox(self.box_structure, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(box_thick_gamma, self, "THICKNESS", label="Bilayer thickness [A]", tooltip="THICKNESS",
                          addSpace=True, labelWidth=125, orientation="horizontal", valueType=float)
        oasysgui.lineEdit(box_thick_gamma, self, "GAMMA", label="gamma=even/total", tooltip="GAMMA",
                          addSpace=True, labelWidth=115, orientation="horizontal", valueType=float)


        #
        box = gui.widgetBox(tab_input, "Sublayers", orientation="vertical")

        self.box_number_of_bilayers = gui.widgetBox(box, orientation="horizontal")
        oasysgui.lineEdit(self.box_number_of_bilayers, self, "N_PAIRS", tooltip="N_PAIRS", label="Number of bilayers", addSpace=True,
                    valueType=int, labelWidth=200, orientation="horizontal", callback=self.get_structure)

        # odd sublayer
        box_odd = gui.widgetBox(box, "Odd sublayer", orientation="vertical")
        oasysgui.lineEdit(box_odd, self, "O_MATERIAL", label='Material [formula]', tooltip="O_MATERIAL",
                           addSpace=True, labelWidth=200, orientation="horizontal", callback=self.set_ODensity)
        bb = gui.widgetBox(box_odd, "", orientation="horizontal")
        oasysgui.lineEdit(bb, self, "O_DENSITY", label='Density [g/cm3]', tooltip="O_DENISTY",
                          addSpace=True, valueType=float, labelWidth=105, orientation="horizontal")
        self.box_roughnessO = gui.widgetBox(bb, orientation="horizontal")
        oasysgui.lineEdit(self.box_roughnessO, self, "ROUGHNESS_ODD", label='Roughness [A]', tooltip="ROUGHNESS_ODD",
                          addSpace=True, valueType=float, labelWidth=95, orientation="horizontal")

        # even sublayer
        box_even = gui.widgetBox(box, "Even sublayer", orientation="vertical")
        oasysgui.lineEdit(box_even, self, "E_MATERIAL", label='Material [formula]', tooltip="E_MATERIAL",
                          addSpace=True, labelWidth=200, orientation="horizontal", callback=self.set_EDensity)
        bb = gui.widgetBox(box_even, "", orientation="horizontal")
        oasysgui.lineEdit(bb, self, "E_DENSITY", label='Density [g/cm3]', tooltip="E_DENISTY",
                          addSpace=True, valueType=float, labelWidth=105, orientation="horizontal")
        self.box_roughnessE = gui.widgetBox(bb, orientation="horizontal")
        oasysgui.lineEdit(self.box_roughnessE, self, "ROUGHNESS_EVEN", label='Roughness [A]', tooltip="ROUGHNESS_EVEN",
                          addSpace=True, valueType=float, labelWidth=95, orientation="horizontal")


        # substrate sublayer
        box_substrate = gui.widgetBox(box, "Substrate", orientation="vertical")
        oasysgui.lineEdit(box_substrate, self, "S_MATERIAL", label='Material [formula]', tooltip="S_MATERIAL",
                           addSpace=True, labelWidth=200, orientation="horizontal", callback=self.set_SDensity)
        oasysgui.lineEdit(box_substrate, self, "S_DENSITY", label='Density [g/cm3]', tooltip="S_DENISTY",
                          addSpace=True, valueType=float, labelWidth=200, orientation="horizontal")


    def populate_tab_graded(self, tab_input_2):

        self.box_lateral = gui.widgetBox(tab_input_2, "laterally graded coeffs F=a[0]+a[1] Y+a[2] Y^2+a[3] Y^3",
                                    orientation="vertical")

        gui.comboBox(self.box_lateral, self, "grade_coeffs_flag", tooltip="grade_coeffs_flag",
                     label="Coeffs from", addSpace=True,
                     items=['External definition', 'Calculate for an ellipse'],
                     valueType=int, orientation="horizontal", labelWidth=270, callback=self.set_visibility)

        self.box_lateral_coeffs = gui.widgetBox(self.box_lateral, "laterally graded coeffs F=a[0]+a[1] Y+a[2] Y^2+a[3] Y^3",
                                         orientation="vertical")
        oasysgui.lineEdit(self.box_lateral_coeffs, self, "AA0", tooltip="AA0", label='a[0]', addSpace=True,
                    valueType=float, labelWidth=150, orientation="horizontal")
        oasysgui.lineEdit(self.box_lateral_coeffs, self, "AA1", tooltip="AA1", label='a[1]', addSpace=True,
                     valueType=float, labelWidth=150, orientation="horizontal")
        oasysgui.lineEdit(self.box_lateral_coeffs, self, "AA2", tooltip="AA2", label='a[2]', addSpace=True,
                    valueType=float, labelWidth=150, orientation="horizontal")
        oasysgui.lineEdit(self.box_lateral_coeffs, self, "AA3", tooltip="AA3", label='a[3]', addSpace=True,
                    valueType=float, labelWidth=150, orientation="horizontal")

        self.box_lateral_ellipse = gui.widgetBox(self.box_lateral, "Ellipse parameters", orientation="vertical")
        oasysgui.lineEdit(self.box_lateral_ellipse, self, "ell_p", tooltip="ell_p", label='p [m]', addSpace=True,
                    valueType=float, labelWidth=150, orientation="horizontal")
        oasysgui.lineEdit(self.box_lateral_ellipse, self, "ell_q", tooltip="ell_q", label='q [m]', addSpace=True,
                     valueType=float, labelWidth=150, orientation="horizontal")
        oasysgui.lineEdit(self.box_lateral_ellipse, self, "ell_theta_deg", tooltip="ell_theta_deg", label='grazing angle [deg]',
                          addSpace=True, valueType=float, labelWidth=200, orientation="horizontal")
        oasysgui.lineEdit(self.box_lateral_ellipse, self, "ell_length", tooltip="ell_length", label='lateral length [m]',
                          addSpace=True, valueType=float, labelWidth=200, orientation="horizontal")
        oasysgui.lineEdit(self.box_lateral_ellipse, self, "ell_photon_energy", tooltip="ell_photon_energy", label='main photon energy [eV]',
                          addSpace=True, valueType=float, labelWidth=200, orientation="horizontal")

        #
        # depth graded
        #
        self.depth_graded_box = gui.widgetBox(tab_input_2, "Depth graded: [ [N,thck,gmma,rouE,rouO], ...]", orientation="vertical")
        self.depth_graded_text_area = oasysgui.textArea(readOnly=False)
        self.depth_graded_box.layout().addWidget(self.depth_graded_text_area)
        self.depth_graded_text_area.setText(self.graded_depth_text_list)

    def populate_tab_plots(self, tab_plots):

        box = gui.widgetBox(tab_plots, "Optional scan plots", orientation="vertical")

        gui.comboBox(box, self, "plot_flag", tooltip="plot_flag",
                     label="Scan plot", addSpace=True,
                     items=['No', 'energy-scan', 'grazing angle-scan', 'energy-angle-scan'],
                     valueType=int, orientation="horizontal", labelWidth=270, callback=self.do_plots)

        self.box_plots = gui.widgetBox(tab_plots, "Optional scan plots", orientation="vertical")

        self.box_plot_e = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_e, self, "scan_e_from", label="from [eV]", tooltip="scan_e_from",
                          valueType=float, addSpace=True, labelWidth=100, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_e, self, "scan_e_to", label="to [eV]", tooltip="scan_e_to",
                          valueType=float, addSpace=True, labelWidth=20, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_e, self, "scan_e_n", label="points", tooltip="scan_e_n",
                          valueType=int, addSpace=True, labelWidth=50, orientation="horizontal")
        self.box_plot_a0 = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_a0, self, "scan_a0", label="Fixed angle [deg]", tooltip="scan_a0",
                          valueType=float, addSpace=True, labelWidth=200, orientation="horizontal")

        self.box_plot_a = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_a, self, "scan_a_from", label="from [deg]", tooltip="scan_a_from",
                          valueType=float, addSpace=True, labelWidth=100, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_a, self, "scan_a_to", label="to [deg]", tooltip="scan_a_to",
                          valueType=float, addSpace=True, labelWidth=20, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_a, self, "scan_a_n", label="points", tooltip="scan_a_n",
                          valueType=int, addSpace=True, labelWidth=50, orientation="horizontal")
        self.box_plot_e0 = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_e0, self, "scan_e0", label="Fixed energy [eV]", tooltip="scan_e0",
                          valueType=float, addSpace=True, labelWidth=200, orientation="horizontal")


    def populate_tab_use_of_widget(self, tab_usa):

        tab_usa.setStyleSheet("background-color: white;")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)


    def set_structure(self):
        #
        # parse
        #
        structure = self.structure
        i0 = structure.find('[')
        i1 = structure.find(',')
        i2 = structure.find(']')
        i3 = structure.find('x')
        i4 = structure.find('+')
        if i0 * i2 * i3 * i4 < 0:
            raise Exception("Bad format for multilayer structure %s (must be: %s)" % (structure, ['[W,B]x50+Si']))
        material_O = structure[(i0+1):(i1)]
        material_E = structure[(i1+1):(i2)]
        npair =  int(structure[(i3+1):(i4)])
        material_S = structure[(i4+1)::]

        print("[%s,%s]x%d+%s" % (material_O, material_E, npair, material_S))

        self.N_PAIRS = npair
        self.O_MATERIAL = material_O
        self.E_MATERIAL = material_E
        self.S_MATERIAL = material_S

        self.set_EDensity()
        self.set_ODensity()
        self.set_SDensity()

    def get_structure(self):
        structure = "[%s,%s]x%d+%s" % (self.O_MATERIAL, self.E_MATERIAL, self.N_PAIRS, self.S_MATERIAL)
        self.structure = structure

    def set_visibility(self):
        self.box_lateral_coeffs.setVisible(self.flag_graded in [1,3] and self.grade_coeffs_flag == 0)
        self.box_lateral_ellipse.setVisible(self.flag_graded in [1,3] and self.grade_coeffs_flag == 1)
        self.box_lateral.setVisible(self.flag_graded in [1,3])

        if self.flag_graded in [2,3]:
            self.depth_graded_box.setVisible(True)
            self.box_structure.setVisible(False)
            self.box_number_of_bilayers.setVisible(False)
            self.box_roughnessE.setVisible(False)
            self.box_roughnessO.setVisible(False)
        else:
            self.depth_graded_box.setVisible(False)
            self.box_structure.setVisible(True)
            self.box_number_of_bilayers.setVisible(True)
            self.box_roughnessE.setVisible(True)
            self.box_roughnessO.setVisible(True)


        self.box_plots.setVisible(self.plot_flag > 0)
        if self.plot_flag == 1:
            self.box_plot_e.setVisible(True)
            self.box_plot_a0.setVisible(True)
            self.box_plot_a.setVisible(False)
            self.box_plot_e0.setVisible(False)
        elif self.plot_flag == 2:
            self.box_plot_e.setVisible(False)
            self.box_plot_a0.setVisible(False)
            self.box_plot_a.setVisible(True)
            self.box_plot_e0.setVisible(True)
        elif self.plot_flag == 3:
            self.box_plot_e.setVisible(True)
            self.box_plot_a0.setVisible(False)
            self.box_plot_a.setVisible(True)
            self.box_plot_e0.setVisible(False)

    def set_SDensity(self):
        if not self.S_MATERIAL is None:
            if not self.S_MATERIAL.strip() == "":
                self.S_MATERIAL = self.S_MATERIAL.strip()
                self.S_DENSITY = ShadowPhysics.getMaterialDensity(self.S_MATERIAL)

    def set_EDensity(self):
        if not self.E_MATERIAL is None:
            if not self.E_MATERIAL.strip() == "":
                self.E_MATERIAL = self.E_MATERIAL.strip()
                self.E_DENSITY = ShadowPhysics.getMaterialDensity(self.E_MATERIAL)
                
    def set_ODensity(self):
        if not self.O_MATERIAL is None:
            if not self.O_MATERIAL.strip() == "":
                self.O_MATERIAL = self.O_MATERIAL.strip()
                self.O_DENSITY = ShadowPhysics.getMaterialDensity(self.O_MATERIAL)

    def compute(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)
            self.shadow_output.setText("")
            self.checkFields()

            if self.flag_graded == 0:
                GRADE_SURFACE = 0
                GRADE_DEPTH = 0
                LIST_N_THICK_GAMMA_ROUGHE_ROUGHO_FROM_TOP_TO_BOTTOM = None
            elif self.flag_graded == 1: # lateral
                if self.grade_coeffs_flag == 0: # external coefficients in m
                    GRADE_SURFACE = 3  # S4 coeffs
                else:
                    GRADE_SURFACE = 4
                GRADE_DEPTH = 0
                LIST_N_THICK_GAMMA_ROUGHE_ROUGHO_FROM_TOP_TO_BOTTOM = None
            elif self.flag_graded == 2:  # depth
                GRADE_SURFACE = 0
                GRADE_DEPTH = 1
                LIST_N_THICK_GAMMA_ROUGHE_ROUGHO_FROM_TOP_TO_BOTTOM = self.depth_graded_text_area.toPlainText()
                self.graded_depth_text_list = self.depth_graded_text_area.toPlainText()
            elif self.flag_graded == 3:  # both
                if self.grade_coeffs_flag == 0: # external coefficients in m
                    GRADE_SURFACE = 3  # S4 coeffs
                else:
                    GRADE_SURFACE = 4
                GRADE_DEPTH = 1
                LIST_N_THICK_GAMMA_ROUGHE_ROUGHO_FROM_TOP_TO_BOTTOM = self.depth_graded_text_area.toPlainText()
                self.graded_depth_text_list = self.depth_graded_text_area.toPlainText()
            else:
                raise NotImplementedError()

            self.mlayer_instance = MLayer.pre_mlayer(
                             FILE=congruence.checkFileName(self.FILE),
                             E_MIN=self.E_MIN,
                             E_MAX=self.E_MAX,
                             S_DENSITY=self.S_DENSITY,
                             S_MATERIAL=self.S_MATERIAL,
                             E_DENSITY=self.E_DENSITY,
                             E_MATERIAL=self.E_MATERIAL,
                             O_DENSITY=self.O_DENSITY,
                             O_MATERIAL=self.O_MATERIAL,
                             N_PAIRS=self.N_PAIRS,
                             THICKNESS=self.THICKNESS,
                             GAMMA=self.GAMMA,
                             ROUGHNESS_EVEN=self.ROUGHNESS_EVEN,
                             ROUGHNESS_ODD=self.ROUGHNESS_ODD,
                             GRADE_SURFACE=GRADE_SURFACE,
                             AA0=self.AA0,
                             AA1=self.AA1,
                             AA2=self.AA2,
                             AA3=self.AA3,
                             ell_p=self.ell_p,
                             ell_q=self.ell_q,
                             ell_theta_grazing_deg=self.ell_theta_deg,
                             ell_length=self.ell_length,
                             ell_photon_energy=self.ell_photon_energy,
                             GRADE_DEPTH=GRADE_DEPTH,
                             LIST_N_THICK_GAMMA_ROUGHE_ROUGHO_FROM_TOP_TO_BOTTOM=LIST_N_THICK_GAMMA_ROUGHE_ROUGHO_FROM_TOP_TO_BOTTOM,
                             )

            # this is for just info
            if self.flag_graded == 1 and self.grade_coeffs_flag == 1:
                _ = self.mlayer_instance._fit_ellipse_laterally_graded_coeffs(verbose=1)

            # plots
            self.do_plots()

            self.send("MLayerPreProcessorData", MLayerPreProcessorData(mlayer_data_file=self.FILE))
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)
            if self.IS_DEVELOP: raise exception

    def checkFields(self):
        congruence.checkDir(self.FILE)
        self.E_MIN  = congruence.checkPositiveNumber(self.E_MIN , "Min Energy")
        self.E_MAX  = congruence.checkStrictlyPositiveNumber(self.E_MAX , "Max Energy")
        congruence.checkLessOrEqualThan(self.E_MIN, self.E_MAX, "Minimum Energy", "Maximum Energy")
        self.S_MATERIAL = ShadowPhysics.checkCompoundName(self.S_MATERIAL)
        self.S_DENSITY = congruence.checkStrictlyPositiveNumber(float(self.S_DENSITY), "Density (substrate)")
        self.E_MATERIAL = ShadowPhysics.checkCompoundName(self.E_MATERIAL)
        self.E_DENSITY = congruence.checkStrictlyPositiveNumber(float(self.E_DENSITY), "Density (even sublayer)")
        self.O_MATERIAL = ShadowPhysics.checkCompoundName(self.O_MATERIAL)
        self.O_DENSITY = congruence.checkStrictlyPositiveNumber(float(self.O_DENSITY), "Density (odd sublayer)")

        if self.flag_graded in [0,1,3]:
            self.N_PAIRS = congruence.checkStrictlyPositiveNumber(int(self.N_PAIRS), "Number of bilayers")
            self.THICKNESS = congruence.checkStrictlyPositiveNumber(float(self.THICKNESS), "bilayer thickness t")
            self.GAMMA = congruence.checkStrictlyPositiveNumber(float(self.GAMMA), "gamma ratio")
            self.ROUGHNESS_EVEN = congruence.checkPositiveNumber(float(self.ROUGHNESS_EVEN), "Roughness even layer")
            self.ROUGHNESS_ODD = congruence.checkPositiveNumber(float(self.ROUGHNESS_ODD), "Roughness odd layer")

        if self.flag_graded in [1,3]:
            self.AA0 = congruence.checkNumber(float(self.AA0), "zero-order coefficient")
            self.AA1 = congruence.checkNumber(float(self.AA1), "linear coefficient")
            self.AA2 = congruence.checkNumber(float(self.AA2), "2nd degree coefficient")
            self.AA3 = congruence.checkNumber(float(self.AA3), "3rd degree coefficient")
            # todo add ellipse

    def selectFile(self):
        self.le_FILE.setText(oasysgui.selectFileFromDialog(self, self.FILE, "Select Output File", file_extension_filter="Data Files (*.dat)"))

    def selectFileDepth(self):
        self.le_FILE_DEPTH.setText(oasysgui.selectFileFromDialog(self, self.FILE_DEPTH, "Open File with list of t_bilayer,gamma,roughness_even,roughness_odd", file_extension_filter="Data Files (*.dat)"))

    def do_plots(self):

        self.set_visibility()

        self.plot_tab.layout().removeItem(self.plot_tab.layout().itemAt(0))

        if self.mlayer_instance is None: return

        if self.plot_flag == 0:
            plot_widget_id = plot_data1D([0], [0], xtitle="", ytitle="")
        elif self.plot_flag == 1:
            energyN = int(self.scan_e_n)
            energy1 = self.scan_e_from
            energy2 = self.scan_e_to
            thetaN = 1
            theta1 = self.scan_a0
            theta2 = self.scan_a0
            R_S_array, R_P_array, energy_array, theta_array = self.mlayer_instance.scan(
                energyN=energyN, energy1=energy1, energy2=energy2,
                thetaN=thetaN, theta1=theta1, theta2=theta2)
            plot_widget_id = plot_data1D(energy_array, R_S_array[:, 0] ** 2, xtitle="Photon energy [eV]",
                                         ytitle="Reflectivity")
        elif self.plot_flag == 2:
            energyN = 1
            energy1 = self.scan_e0
            energy2 = self.scan_e0
            thetaN = int(self.scan_a_n)
            theta1 = self.scan_a_from
            theta2 = self.scan_a_to
            R_S_array, R_P_array, energy_array, theta_array = self.mlayer_instance.scan(
                energyN=energyN, energy1=energy1, energy2=energy2,
                thetaN=thetaN, theta1=theta1, theta2=theta2)
            plot_widget_id = plot_data1D(theta_array, R_S_array[0, :]**2, xtitle="grazing angle [deg]", ytitle="Reflectivity")
        elif self.plot_flag == 3:
            energyN = self.scan_e_n
            energy1 = self.scan_e_from
            energy2 = self.scan_e_to
            thetaN = self.scan_a_n
            theta1 = self.scan_a_from
            theta2 = self.scan_a_to
            R_S_array, R_P_array, energy_array, theta_array = self.mlayer_instance.scan(
                energyN=energyN, energy1=energy1, energy2=energy2,
                thetaN=thetaN, theta1=theta1, theta2=theta2)
            plot_widget_id = plot_data2D(R_S_array**2, energy_array, theta_array, title="title",
                                         xtitle="photon energy [eV]", ytitle="grazing angle [deg]")

        self.plot_tab.layout().addWidget(plot_widget_id)

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWMLayer()
    w.show()
    app.exec_()
    w.saveSettings()
