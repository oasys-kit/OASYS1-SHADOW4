import os, sys
import numpy

from PyQt5.QtWidgets import QLabel, QApplication, QMessageBox, QSizePolicy
from PyQt5.QtGui import QTextCursor, QIntValidator, QDoubleValidator, QPixmap
from PyQt5.QtCore import Qt

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.util.shadow4_objects import BraggPreProcessorData

from xoppylib.decorators.dabax_decorated import DabaxDecorated
from xoppylib.crystals.create_bragg_preprocessor_file_v2 import create_bragg_preprocessor_file_v2

from urllib.error import HTTPError
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D, plot_multi_data1D

from crystalpy.diffraction.GeometryType import BraggDiffraction
from crystalpy.diffraction.DiffractionSetupShadowPreprocessorV1 import DiffractionSetupShadowPreprocessorV1
from crystalpy.diffraction.DiffractionSetupShadowPreprocessorV2 import DiffractionSetupShadowPreprocessorV2
from crystalpy.diffraction.Diffraction import Diffraction
from crystalpy.util.ComplexAmplitudePhotonBunch import ComplexAmplitudePhotonBunch
from crystalpy.util.ComplexAmplitudePhoton import ComplexAmplitudePhoton
from crystalpy.util.Vector import Vector
from crystalpy.util.Photon import Photon

class OWBragg(OWWidget):
    name = "Bragg"
    id = "xsh_bragg"
    description = "Calculation of crystal diffraction profile"
    icon = "icons/bragg.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 20
    category = ""
    keywords = ["oasys", "bragg"]

    outputs = [{"name":"BraggPreProcessorData",
                "type":BraggPreProcessorData,
                "doc":"Bragg PreProcessor Data",
                "id":"BraggPreProcessorData"}]

    want_main_area = True

    DESCRIPTOR = Setting(0)
    H_MILLER_INDEX = Setting(1)
    K_MILLER_INDEX = Setting(1)
    L_MILLER_INDEX = Setting(1)
    TEMPERATURE_FACTOR = Setting(1.0)
    E_MIN = Setting(5000.0)
    E_MAX = Setting(15000.0)
    E_STEP = Setting(100.0)
    SHADOW_FILE = Setting("bragg.dat")

    PREPROCESSOR_FILE_VERSION = Setting(1)
    DESCRIPTOR_DABAX = Setting(0)
    DESCRIPTOR_XRAYSERVER = Setting(129)

    IMAGE_WIDTH  = 860
    IMAGE_HEIGHT = 545

    MAX_WIDTH          = 1320
    MAX_HEIGHT         = 700
    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT   = 630

    #
    # Plots
    #
    plot_flag = Setting(0)
    scan_e_n = Setting(100)
    scan_e_delta = Setting(10.0)

    scan_a_n = Setting(100)
    scan_a_delta = Setting(100)
    scan_e0 = Setting(10000.0)

    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui"), "misc", "bragg_usage.png")

    bragg_dict = None

    #crystalpy (plots)
    calculation_method = 1         # 0=Zachariasen, 1=Guigay
    calculation_strategy_flag = 2  # 0=mpmath 1=numpy 2=numpy-truncated

    def __init__(self):
        super().__init__()

        self.populate_crystal_lists()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(self.MAX_WIDTH)
        self.setFixedHeight(self.MAX_HEIGHT)

        gui.separator(self.controlArea)

        box0 = oasysgui.widgetBox(self.controlArea, "",orientation="horizontal")
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(35)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Crystal Settings")
        self.populate_crystal_settings(tab_bas)

        tab_input_plot = oasysgui.createTabPage(tabs_setting, "Plots")
        self.populate_tab_plots(tab_input_plot)

        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        self.populate_tab_use_of_widget(tab_usa)

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        tab_out = oasysgui.createTabPage(self.main_tabs, "Output")
        self.plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots (optional scan)")

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=400)
        out_box.layout().addWidget(self.shadow_output)

        self.process_showers()

        gui.rubber(self.controlArea)

    def populate_crystal_lists(self):
        dx1 = DabaxDecorated(file_Crystals="Crystals.dat")
        try: list1 = dx1.Crystal_GetCrystalsList()
        except HTTPError as e: # Anti-bot policies can block this call
            if "UserAgentBlocked" in str(e): list1 = {}
            else: raise e
        self.crystals_dabax = list1

        dx2 = DabaxDecorated(file_Crystals="Crystals_xrayserver.dat")
        try: list2 = dx2.Crystal_GetCrystalsList()
        except HTTPError as e: # Anti-bot policies can block this call
            if "UserAgentBlocked" in str(e): list2 = {}
            else: raise e
        self.crystals_xrayserver = list2

    def populate_tab_use_of_widget(self, tab_usa):
        tab_usa.setStyleSheet("background-color: white;")
        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")
        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))
        usage_box.layout().addWidget(label)

    def populate_tab_plots(self, tab_plots):
        box = gui.widgetBox(tab_plots, "Optional scan plots", orientation="vertical")

        gui.comboBox(box, self, "plot_flag", tooltip="plot_flag",
                     label="Scan plot", addSpace=True,
                     items=['No', 'energy-scan', 'grazing angle-scan'],
                     valueType=int, orientation="horizontal", labelWidth=270, callback=self.do_plots)

        self.box_plots = gui.widgetBox(tab_plots, "Optional scan plots", orientation="vertical")

        self.box_plot_e = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_e, self, "scan_e_delta", label="delta [eV]", tooltip="scan_e_delta",
                          valueType=float, addSpace=True, labelWidth=100, orientation="horizontal",
                          callback=self.do_plots)
        oasysgui.lineEdit(self.box_plot_e, self, "scan_e_n", label="points", tooltip="scan_e_n",
                          valueType=int, addSpace=True, labelWidth=50, orientation="horizontal",
                          callback=self.do_plots)

        self.box_plot_a = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_a, self, "scan_a_delta", label="delta [urad]", tooltip="scan_a_delta",
                          valueType=float, addSpace=True, labelWidth=100, orientation="horizontal",
                          callback=self.do_plots)
        oasysgui.lineEdit(self.box_plot_a, self, "scan_a_n", label="points", tooltip="scan_a_n",
                          valueType=int, addSpace=True, labelWidth=50, orientation="horizontal",
                          callback=self.do_plots)

        self.box_plot_e0 = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_e0, self, "scan_e0", label="Fixed energy [eV]", tooltip="scan_e0",
                          valueType=float, addSpace=True, labelWidth=200, orientation="horizontal",
                          callback=self.do_plots)

    def populate_crystal_settings(self, tab_bas):
        #
        # basic settings
        #
        idx = -1

        box = oasysgui.widgetBox(tab_bas, "Crystal Parameters", orientation="vertical")

        # widget index -0.1
        idx += 1
        gui.comboBox(box, self, "PREPROCESSOR_FILE_VERSION", tooltip="PREPROCESSOR_FILE_VERSION",
                     label=self.unitLabels()[idx], addSpace=True,
                     # items=["v1 [default]","v2 [from DABAX list]","v2 [from XRayServer list]"],
                     items=["from DABAX list (version 2)", "from XRayServer list (version 2)"],
                     sendSelectedValue=False,
                     valueType=int, orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box)

        # widget index 0.1
        idx += 1
        box2 = oasysgui.widgetBox(box, "", orientation="vertical")
        gui.comboBox(box2, self, "DESCRIPTOR_DABAX", tooltip="DESCRIPTOR_DABAX",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=self.crystals_dabax, sendSelectedValue=False,
                     valueType=int, orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box2)

        # widget index 0.2
        idx += 1
        box3 = oasysgui.widgetBox(box, "", orientation="vertical")
        gui.comboBox(box3, self, "DESCRIPTOR_XRAYSERVER", tooltip="DESCRIPTOR_XRAYSERVER",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=self.crystals_xrayserver, sendSelectedValue=False,
                     valueType=int, orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box3)

        # widget index 1
        idx += 1
        box_miller = oasysgui.widgetBox(box, "", orientation="horizontal")
        oasysgui.lineEdit(box_miller, self, "H_MILLER_INDEX", tooltip="H_MILLER_INDEX",
                          label="Miller Indices [h k l]", addSpace=True,
                          valueType=int, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_miller)

        # widget index 2
        idx += 1
        oasysgui.lineEdit(box_miller, self, "K_MILLER_INDEX", tooltip="K_MILLER_INDEX", addSpace=True,
                          valueType=int)
        self.show_at(self.unitFlags()[idx], box)

        # widget index 3
        idx += 1
        oasysgui.lineEdit(box_miller, self, "L_MILLER_INDEX", tooltip="L_MILLER_INDEX",
                          addSpace=True,
                          valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        gui.separator(box)

        # widget index 4
        idx += 1
        oasysgui.lineEdit(box, self, "TEMPERATURE_FACTOR", tooltip="TEMPERATURE_FACTOR",
                          label=self.unitLabels()[idx], addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 5
        idx += 1
        oasysgui.lineEdit(box, self, "E_MIN", tooltip="E_MIN",
                          label=self.unitLabels()[idx], addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 6
        idx += 1
        oasysgui.lineEdit(box, self, "E_MAX", tooltip="E_MAX",
                          label=self.unitLabels()[idx], addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 7
        idx += 1
        oasysgui.lineEdit(box, self, "E_STEP", tooltip="E_STEP",
                          label=self.unitLabels()[idx], addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 8
        idx += 1
        box_2 = oasysgui.widgetBox(box, "", addSpace=True, orientation="horizontal")

        self.le_SHADOW_FILE = oasysgui.lineEdit(box_2, self, "SHADOW_FILE", tooltip="SHADOW_FILE",
                                                label=self.unitLabels()[idx], addSpace=True, labelWidth=180,
                                                orientation="horizontal")

        gui.button(box_2, self, "...", callback=self.selectFile)

        self.show_at(self.unitFlags()[idx], box)

    def unitLabels(self):
         return ['Preprocessor file version','Crystal descriptor [DABAX list]','Crystal descriptor [XRayServer list]','H miller index','K miller index','L miller index','Temperature factor','Minimum energy [eV]','Maximum energy [eV]','Energy step [eV]','File name (for SHADOW)']

    def unitFlags(self):
         return ['True','self.PREPROCESSOR_FILE_VERSION == 0','self.PREPROCESSOR_FILE_VERSION == 1','True','True','True','True','True','True','True','True']

    def selectFile(self):
        self.le_SHADOW_FILE.setText(oasysgui.selectFileFromDialog(self, self.SHADOW_FILE, "Select Output File"))

    def set_visibility(self):
        self.box_plots.setVisible(self.plot_flag > 0)
        if self.plot_flag == 1:
            self.box_plot_e.setVisible(True)
            self.box_plot_a.setVisible(False)
            self.box_plot_e0.setVisible(True)
        elif self.plot_flag == 2:
            self.box_plot_e.setVisible(False)
            self.box_plot_a.setVisible(True)
            self.box_plot_e0.setVisible(True)

    def compute(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.checkFields()

            if self.PREPROCESSOR_FILE_VERSION == 0:
                descriptor=self.crystals_dabax[self.DESCRIPTOR_DABAX]
                material_constants_library = DabaxDecorated(file_Crystals="Crystals.dat")
            else:
                descriptor = self.crystals_xrayserver[self.DESCRIPTOR_XRAYSERVER]
                material_constants_library = DabaxDecorated(file_Crystals="Crystals_xrayserver.dat")

            self.bragg_dict = create_bragg_preprocessor_file_v2(interactive=False,
                                              DESCRIPTOR=descriptor,
                                              H_MILLER_INDEX=self.H_MILLER_INDEX,
                                              K_MILLER_INDEX=self.K_MILLER_INDEX,
                                              L_MILLER_INDEX=self.L_MILLER_INDEX,
                                              TEMPERATURE_FACTOR=self.TEMPERATURE_FACTOR,
                                              E_MIN=self.E_MIN,
                                              E_MAX=self.E_MAX,
                                              E_STEP=self.E_STEP,
                                              SHADOW_FILE=congruence.checkFileName(self.SHADOW_FILE),
                                              material_constants_library=material_constants_library,
                                              )

            self.send("BraggPreProcessorData", BraggPreProcessorData(bragg_data_file=self.SHADOW_FILE))
            self.do_plots()
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)
            if self.IS_DEVELOP: raise exception

    def checkFields(self):
        self.H_MILLER_INDEX = congruence.checkNumber(self.H_MILLER_INDEX, "H miller index")
        self.K_MILLER_INDEX = congruence.checkNumber(self.K_MILLER_INDEX, "K miller index")
        self.L_MILLER_INDEX = congruence.checkNumber(self.L_MILLER_INDEX, "L miller index")
        self.TEMPERATURE_FACTOR = congruence.checkNumber(self.TEMPERATURE_FACTOR, "Temperature factor")
        self.E_MIN  = congruence.checkPositiveNumber(self.E_MIN , "Minimum energy")
        self.E_MAX  = congruence.checkStrictlyPositiveNumber(self.E_MAX , "Maximum Energy")
        self.E_STEP = congruence.checkStrictlyPositiveNumber(self.E_STEP, "Energy step")
        congruence.checkLessOrEqualThan(self.E_MIN, self.E_MAX, "From Energy", "To Energy")
        congruence.checkDir(self.SHADOW_FILE)

    def do_plots(self):
        self.set_visibility()
        if self.bragg_dict is None: self.compute()
        self.plot_tab.layout().removeItem(self.plot_tab.layout().itemAt(0))

        if self.plot_flag == 0:
            plot_widget_id = plot_data1D([0], [0], xtitle="", ytitle="")
        elif self.plot_flag == 1:
            energy_array, R_S_array, R_P_array = self.calculate_simple_diffraction_energy_scan()
            plot_widget_id = plot_multi_data1D(energy_array, [R_S_array, R_P_array], xtitle="Photon energy [eV]",
                                         ytitle="Reflectivity", ytitles=['S-polaized','P-polarized'])
        elif self.plot_flag == 2:
            theta_array, R_S_array, R_P_array = self.calculate_simple_diffraction_theta_scan()
            plot_widget_id = plot_multi_data1D(1e6 * numpy.array(theta_array),
                                        [numpy.array(R_S_array, dtype=float), numpy.array(R_P_array, dtype=float)],
                                        xtitle="theta - theta_B [urad]", ytitle="Reflectivity-S",
                                        ytitles=['S-polaized','P-polarized'])
        self.plot_tab.layout().addWidget(plot_widget_id)

    def calculate_simple_diffraction_theta_scan(self):
        print("\nCreating a diffraction setup (shadow preprocessor file V2)...")
        diffraction_setup = DiffractionSetupShadowPreprocessorV2(geometry_type=BraggDiffraction(),  # todo: use oe._diffraction_geometry
                                             crystal_name="",  # string
                                             thickness=1e-2,  # meters
                                             miller_h=self.H_MILLER_INDEX,          # int
                                             miller_k=self.K_MILLER_INDEX,          # int
                                             miller_l=self.L_MILLER_INDEX,          # int
                                             asymmetry_angle=0.0,  # radians
                                             azimuthal_angle=0.0,
                                             preprocessor_file=self.SHADOW_FILE)

        angle_deviation_min = -0.5 * self.scan_a_delta * 1e-6  # radians
        angle_deviation_max = 0.5 * self.scan_a_delta * 1e-6 # radians
        angle_deviation_points = self.scan_a_n
        angle_step = (angle_deviation_max - angle_deviation_min) / angle_deviation_points
        #
        # gets Bragg angle needed to create deviation's scan
        #
        bragg_angle = diffraction_setup.angleBragg(self.scan_e0)
        print("Bragg angle for E=%f eV is %f deg" % (self.scan_e0, bragg_angle * 180.0 / numpy.pi))
        deviations = numpy.zeros(angle_deviation_points)
        bunch_in = ComplexAmplitudePhotonBunch()
        K0 = diffraction_setup.vectorK0(self.scan_e0)
        K0unitary = K0.getNormalizedVector()

        for ia in range(angle_deviation_points):
            deviation = angle_deviation_min + ia * angle_step
            # minus sign in angle is to perform cw rotation when deviation increses
            Vin = K0unitary.rotateAroundAxis(Vector(1, 0, 0), -deviation)
            photon = ComplexAmplitudePhoton(energy_in_ev=self.scan_e0, direction_vector=Vin)

            bunch_in.addPhoton(photon)
            deviations[ia] = angle_deviation_min + ia * angle_step

        coeffs = Diffraction.calculateDiffractedComplexAmplitudes(diffraction_setup,
                                                                  bunch_in,
                                                                  is_thick=1,
                                                                  calculation_method=self.calculation_method,
                                                                  calculation_strategy_flag=self.calculation_strategy_flag)
        intensityS = numpy.abs(coeffs["S"]) ** 2
        intensityP = numpy.abs(coeffs["P"]) ** 2

        return deviations, intensityS, intensityP

    def calculate_simple_diffraction_energy_scan(self):
        print("\nCreating a diffraction setup (shadow preprocessor file V2)...")
        diffraction_setup = DiffractionSetupShadowPreprocessorV2(geometry_type=BraggDiffraction(),  # todo: use oe._diffraction_geometry
                                             crystal_name="",  # string
                                             thickness=1e-2,  # meters
                                             miller_h=self.H_MILLER_INDEX,          # int
                                             miller_k=self.K_MILLER_INDEX,          # int
                                             miller_l=self.L_MILLER_INDEX,          # int
                                             asymmetry_angle=0.0,  # radians
                                             azimuthal_angle=0.0,
                                             preprocessor_file=self.SHADOW_FILE)

        diffraction = Diffraction()
        energies = numpy.linspace(self.scan_e0 - 0.5 * self.scan_e_delta,
                                  self.scan_e0 + 0.5 * self.scan_e_delta,
                                  self.scan_e_n)
        scan = numpy.zeros_like(energies)
        intensityS = numpy.zeros_like(scan, dtype=float)
        intensityP = numpy.zeros_like(scan, dtype=float)
        r = numpy.zeros_like(energies)
        bragg_angle = diffraction_setup.angleBragg(self.scan_e0)
        print("Bragg angle for E=%f eV is %f deg" % (self.scan_e0, bragg_angle * 180.0 / numpy.pi))

        for i in range(energies.size):
            #
            # gets Bragg angle needed to create deviation's scan
            #
            energy = energies[i]
            # Create a Diffraction object (the calculator)
            deviation = 0.0 # angle_deviation_min + ia * angle_step
            angle = deviation  + bragg_angle
            # calculate the components of the unitary vector of the incident photon scan
            # Note that diffraction plane is YZ
            yy = numpy.cos(angle)
            zz = - numpy.abs(numpy.sin(angle))
            photon = Photon(energy_in_ev=energy,direction_vector=Vector(0.0,yy,zz))
            # perform the calculation
            coeffs_r = Diffraction.calculateDiffractedComplexAmplitudes(diffraction_setup,
                                                                        photon,
                                                                        is_thick=1,
                                                                        calculation_method=self.calculation_method,
                                                                        calculation_strategy_flag=self.calculation_strategy_flag)
            scan[i] = energy
            intensityS[i] = numpy.abs(coeffs_r["S"]) ** 2
            intensityP[i] = numpy.abs(coeffs_r["P"]) ** 2
        return scan, intensityS, intensityP


    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWBragg()
    w.PREPROCESSOR_FILE_VERSION = 1
    w.show()
    app.exec()
    w.saveSettings()
