import os, sys

from PyQt5.QtWidgets import QLabel, QApplication, QMessageBox, QSizePolicy
from PyQt5.QtGui import QTextCursor, QPixmap, QDoubleValidator
from PyQt5.QtCore import Qt

from shadow4.physical_models.prerefl.prerefl import PreRefl

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from oasys.util.oasys_util import EmittingStream
from orangecontrib.shadow4.util.shadow4_objects import PreReflPreProcessorData
from orangecontrib.shadow.util.shadow_util import ShadowPhysics

class OWPrerefl(OWWidget):
    name = "PreRefl"
    id = "xsh_prerefl"
    description = "Calculation of mirror reflectivity profile"
    icon = "icons/prerefl.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 10
    category = ""
    keywords = ["xoppy", "xsh_prerefl"]

    outputs = [{"name":"PreReflPreProcessorData",
                "type":PreReflPreProcessorData,
                "doc":"PreRefl PreProcessor Data",
                "id":"PreReflPreProcessorData"}]

    want_main_area = False

    symbol = Setting("SiC")
    density = Setting(3.217)
    prerefl_file = Setting("reflec.dat")
    e_min = Setting(100.0)
    e_max = Setting(20000.0)
    e_step = Setting(100.0)

    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui") , "misc", "prerefl_usage.png")

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(550)
        self.setFixedHeight(550)

        gui.separator(self.controlArea)

        box0 = gui.widgetBox(self.controlArea, "",orientation="horizontal")

        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Defaults", callback=self.defaults)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Help", callback=self.help1)
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Reflectivity Settings")
        tab_out = oasysgui.createTabPage(tabs_setting, "Output")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

        box = oasysgui.widgetBox(tab_bas, "Reflectivity Parameters", orientation="vertical")
        
        idx = -1 
        
        #widget index 0 
        idx += 1 
        oasysgui.lineEdit(box, self, "symbol", tooltip="symbol",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal", callback=self.set_Density)
        self.show_at(self.unitFlags()[idx], box)

        #widget index 1
        idx += 1
        oasysgui.lineEdit(box, self, "density", tooltip="density",
                     label=self.unitLabels()[idx], addSpace=True, valueType=float, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 2
        idx += 1
        box_2 = oasysgui.widgetBox(box, "", addSpace=True, orientation="horizontal")

        self.le_prerefl_file = oasysgui.lineEdit(box_2, self, "prerefl_file", tooltip="prerefl_file",
                                                 label=self.unitLabels()[idx], addSpace=True, labelWidth=180, orientation="horizontal")

        gui.button(box_2, self, "...", callback=self.selectFile)

        self.show_at(self.unitFlags()[idx], box)

        #widget index 3
        idx += 1
        oasysgui.lineEdit(box, self, "e_min", tooltip="e_min",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 4
        idx += 1
        oasysgui.lineEdit(box, self, "e_max", tooltip="e_max",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 5
        idx += 1
        oasysgui.lineEdit(box, self, "e_step", tooltip="e_step",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        self.process_showers()

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=400)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)

    def unitLabels(self):
         return ['Element/Compound formula','Density [ g/cm3 ]','File for SHADOW (trace):','Minimum energy [eV]','Maximum energy [eV]','Energy step [eV]']

    def unitFlags(self):
         return ['True','True','True','True','True','True']

    def selectFile(self):
        self.le_prerefl_file.setText(oasysgui.selectFileFromDialog(self, self.prerefl_file, "Select Output File", file_extension_filter="Data Files (*.dat)"))

    def set_Density(self):
        if not self.symbol is None:
            if not self.symbol.strip() == "":
                self.symbol = self.symbol.strip()
                self.density = ShadowPhysics.getMaterialDensity(self.symbol)


    def compute(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.checkFields()

            PreRefl.prerefl(interactive=False,
                            SYMBOL=self.symbol,
                            DENSITY=self.density,
                            FILE=congruence.checkFileName(self.prerefl_file),
                            E_MIN=self.e_min,
                            E_MAX=self.e_max,
                            E_STEP=self.e_step)

            self.send("PreReflPreProcessorData", PreReflPreProcessorData(prerefl_data_file=self.prerefl_file))
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 str(exception),
                                 QMessageBox.Ok)

    def checkFields(self):
        self.symbol = ShadowPhysics.checkCompoundName(self.symbol)
        self.density = congruence.checkStrictlyPositiveNumber(self.density, "Density")
        self.e_min  = congruence.checkPositiveNumber(self.e_min , "Minimum Energy")
        self.e_max  = congruence.checkStrictlyPositiveNumber(self.e_max , "Maximum Energy")
        self.e_step = congruence.checkStrictlyPositiveNumber(self.e_step, "Energy step")
        congruence.checkLessOrEqualThan(self.e_min, self.e_max, "Minimum Energy", "Maximum Energy")
        congruence.checkDir(self.prerefl_file)

    def defaults(self):
         self.resetSettings()
         self.compute()
         return

    def help1(self):
        print("help pressed.")
        # xoppy_doc('xsh_prerefl')

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = OWPrerefl()
    w.show()
    app.exec()
    w.saveSettings()
