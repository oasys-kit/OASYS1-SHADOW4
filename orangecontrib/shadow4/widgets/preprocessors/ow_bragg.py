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
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.util.shadow4_objects import BraggPreProcessorData

from xoppylib.decorators.dabax_decorated import DabaxDecorated
from xoppylib.crystals.create_bragg_preprocessor_file_v2 import create_bragg_preprocessor_file_v2

from urllib.error import HTTPError

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

    want_main_area = False

    DESCRIPTOR = Setting(0)
    H_MILLER_INDEX = Setting(1)
    K_MILLER_INDEX = Setting(1)
    L_MILLER_INDEX = Setting(1)
    TEMPERATURE_FACTOR = Setting(1.0)
    E_MIN = Setting(5000.0)
    E_MAX = Setting(15000.0)
    E_STEP = Setting(100.0)
    SHADOW_FILE = Setting("bragg.dat")

    PREPROCESSOR_FILE_VERSION = Setting(0)
    DESCRIPTOR_DABAX = Setting(0)
    DESCRIPTOR_XRAYSERVER = Setting(0)


    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui"), "misc", "bragg_usage.png")

    def __init__(self):
        super().__init__()

        self.populate_crystal_lists()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(650)
        self.setFixedHeight(550)

        idx = -1 
        
        gui.separator(self.controlArea)

        box0 = oasysgui.widgetBox(self.controlArea, "",orientation="horizontal")
        #widget buttons: compute, set defaults, help
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Defaults", callback=self.defaults)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Help", callback=self.help1)
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Crystal Settings")
        tab_out = oasysgui.createTabPage(tabs_setting, "Output")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

        box = oasysgui.widgetBox(tab_bas, "Crystal Parameters", orientation="vertical")

        #widget index -0.1
        idx += 1
        gui.comboBox(box, self, "PREPROCESSOR_FILE_VERSION",
                     label=self.unitLabels()[idx], addSpace=True,
                     # items=["v1 [default]","v2 [from DABAX list]","v2 [from XRayServer list]"],
                     items=["from DABAX list (version 2)", "from XRayServer list (version 2)"],
                     sendSelectedValue=False,
                     valueType=int, orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box)


        #widget index 0.1
        idx += 1
        box2 = oasysgui.widgetBox(box, "", orientation="vertical")
        gui.comboBox(box2, self, "DESCRIPTOR_DABAX",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=self.crystals_dabax, sendSelectedValue=False,
                     valueType=int, orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box2)

        #widget index 0.2
        idx += 1
        box3 = oasysgui.widgetBox(box, "", orientation="vertical")
        gui.comboBox(box3, self, "DESCRIPTOR_XRAYSERVER",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=self.crystals_xrayserver, sendSelectedValue=False,
                     valueType=int, orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box3)


        #widget index 1 
        idx += 1 
        box_miller = oasysgui.widgetBox(box, "", orientation = "horizontal")
        oasysgui.lineEdit(box_miller, self, "H_MILLER_INDEX",
                     label="Miller Indices [h k l]", addSpace=True,
                    valueType=int, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_miller)
        
        #widget index 2 
        idx += 1 
        oasysgui.lineEdit(box_miller, self, "K_MILLER_INDEX", addSpace=True,
                    valueType=int)
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 3 
        idx += 1 
        oasysgui.lineEdit(box_miller, self, "L_MILLER_INDEX",
                     addSpace=True,
                    valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 

        gui.separator(box)

        #widget index 4 
        idx += 1 
        oasysgui.lineEdit(box, self, "TEMPERATURE_FACTOR",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 5 
        idx += 1 
        oasysgui.lineEdit(box, self, "E_MIN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 6 
        idx += 1 
        oasysgui.lineEdit(box, self, "E_MAX",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 7 
        idx += 1 
        oasysgui.lineEdit(box, self, "E_STEP",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 8 
        idx += 1
        box_2 = oasysgui.widgetBox(box, "", addSpace=True, orientation="horizontal")

        self.le_SHADOW_FILE = oasysgui.lineEdit(box_2, self, "SHADOW_FILE",
                                                 label=self.unitLabels()[idx], addSpace=True, labelWidth=180, orientation="horizontal")

        gui.button(box_2, self, "...", callback=self.selectFile)

        self.show_at(self.unitFlags()[idx], box)

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

    def unitLabels(self):
         return ['Preprocessor file version','Crystal descriptor [DABAX list]','Crystal descriptor [XRayServer list]','H miller index','K miller index','L miller index','Temperature factor','Minimum energy [eV]','Maximum energy [eV]','Energy step [eV]','File name (for SHADOW)']

    def unitFlags(self):
         return ['True','self.PREPROCESSOR_FILE_VERSION == 0','self.PREPROCESSOR_FILE_VERSION == 1','True','True','True','True','True','True','True','True']

    def selectFile(self):
        self.le_SHADOW_FILE.setText(oasysgui.selectFileFromDialog(self, self.SHADOW_FILE, "Select Output File"))

    def compute(self):
        sys.stdout = EmittingStream(textWritten=self.writeStdOut)
        self.checkFields()

        if self.PREPROCESSOR_FILE_VERSION == 0:
            descriptor=self.crystals_dabax[self.DESCRIPTOR_DABAX]
            material_constants_library = DabaxDecorated(file_Crystals="Crystals.dat")
        else:
            descriptor = self.crystals_xrayserver[self.DESCRIPTOR_XRAYSERVER]
            material_constants_library = DabaxDecorated(file_Crystals="Crystals_xrayserver.dat")

        create_bragg_preprocessor_file_v2(interactive=False,
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

    def defaults(self):
         self.resetSettings()
         self.compute()
         return

    def help1(self):
        print("help pressed. To be implemented.")

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
