__author__ = 'labx'

import os, sys

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QRect

from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

from syned.storage_ring.light_source import LightSource, ElectronBeam
from syned.beamline.beamline import Beamline
from syned.util.json_tools import load_from_json_file, load_from_json_url

class OWLightSource(OWWidget):

    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    category = "Syned Light Sources"
    keywords = ["data", "file", "load", "read"]

    outputs = [{"name":"SynedData",
                "type":Beamline,
                "doc":"Syned Beamline",
                "id":"data"}]

    syned_file_name = Setting("Select *.json file")

    source_name         = Setting("Undefined")

    electron_energy_in_GeV = Setting(2.0)
    electron_energy_spread = Setting(0.001)
    ring_current           = Setting(0.4)
    number_of_bunches      = Setting(400)

    moment_xx           = Setting(0.0)
    moment_xxp          = Setting(0.0)
    moment_xpxp         = Setting(0.0)
    moment_yy           = Setting(0.0)
    moment_yyp          = Setting(0.0)
    moment_ypyp         = Setting(0.0)

    electron_beam_size_h       = Setting(0.0)
    electron_beam_divergence_h = Setting(0.0)
    electron_beam_size_v       = Setting(0.0)
    electron_beam_divergence_v = Setting(0.0)

    type_of_properties = Setting(0)

    want_main_area=0

    MAX_WIDTH = 460
    MAX_HEIGHT = 700

    TABS_AREA_HEIGHT = 625
    CONTROL_AREA_WIDTH = 450

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Send Data", self)
        self.runaction.triggered.connect(self.send_data)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Send Data", callback=self.send_data)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_sou = oasysgui.createTabPage(self.tabs_setting, "Light Source Setting")

        box_json =  oasysgui.widgetBox(self.tab_sou, "Read/Write File", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(box_json, "", addSpace=False, orientation="horizontal")

        self.le_syned_file_name = oasysgui.lineEdit(file_box, self, "syned_file_name", "Syned File Name/URL",
                                                    labelWidth=150, valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.select_syned_file, width=25)

        button_box = oasysgui.widgetBox(box_json, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Read Syned File", callback=self.read_syned_file)
        button.setFixedHeight(25)

        button = gui.button(button_box, self, "Write Syned File", callback=self.write_syned_file)
        button.setFixedHeight(25)


        oasysgui.lineEdit(self.tab_sou, self, "source_name", "Light Source Name", labelWidth=260, valueType=str, orientation="horizontal")

        self.electron_beam_box = oasysgui.widgetBox(self.tab_sou, "Electron Beam/Machine Parameters", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.electron_beam_box, self, "electron_energy_in_GeV", "Energy [GeV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.electron_beam_box, self, "electron_energy_spread", "Energy Spread", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.electron_beam_box, self, "ring_current", "Ring Current [A]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(self.electron_beam_box, self, "type_of_properties", label="Electron Beam Properties", labelWidth=350,
                     items=["From 2nd Moments", "From Size/Divergence"],
                     callback=self.set_TypeOfProperties,
                     sendSelectedValue=False, orientation="horizontal")

        self.left_box_2_1 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=150)

        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xx", "Moment xx   [m^2]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xxp", "Moment xxp  [m.rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xpxp", "Moment xpxp [rad^2]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yy", "Moment yy   [m^2]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yyp", "Moment yyp  [m.rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_ypyp", "Moment ypyp [rad^2]", labelWidth=260, valueType=float, orientation="horizontal")


        self.left_box_2_2 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=150)

        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_h",       "Horizontal Beam Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_v",       "Vertical Beam Size [m]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_h", "Horizontal Beam Divergence [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_v", "Vertical Beam Divergence [rad]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_TypeOfProperties()

        gui.rubber(self.controlArea)


    def set_TypeOfProperties(self):
        self.left_box_2_1.setVisible(self.type_of_properties==0)
        self.left_box_2_2.setVisible(self.type_of_properties==1)


    def check_data(self):
        congruence.checkStrictlyPositiveNumber(self.electron_energy_in_GeV , "Energy")
        congruence.checkStrictlyPositiveNumber(self.electron_energy_spread, "Energy Spread")
        congruence.checkStrictlyPositiveNumber(self.ring_current, "Ring Current")

        if self.type_of_properties == 0:
            congruence.checkPositiveNumber(self.moment_xx   , "Moment xx")
            congruence.checkPositiveNumber(self.moment_xpxp , "Moment xpxp")
            congruence.checkPositiveNumber(self.moment_yy   , "Moment yy")
            congruence.checkPositiveNumber(self.moment_ypyp , "Moment ypyp")
        else:
            congruence.checkPositiveNumber(self.electron_beam_size_h       , "Horizontal Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_divergence_h , "Vertical Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_size_v       , "Horizontal Beam Divergence")
            congruence.checkPositiveNumber(self.electron_beam_divergence_v , "Vertical Beam Divergence")

        self.check_magnetic_structure()


    def send_data(self):
        try:
            self.check_data()

            self.send("SynedData", Beamline(light_source=self.get_light_source()))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

            self.setStatusMessage("")
            self.progressBarFinished()


    def get_light_source(self):
        electron_beam = ElectronBeam(energy_in_GeV=self.electron_energy_in_GeV,
                                     energy_spread=self.electron_energy_spread,
                                     current=self.ring_current,
                                     number_of_bunches=self.number_of_bunches)

        if self.type_of_properties == 0:
            electron_beam._moment_xx   = self.moment_xx
            electron_beam._moment_xxp  = self.moment_xxp
            electron_beam._moment_xpxp = self.moment_xpxp
            electron_beam._moment_yy   = self.moment_yy
            electron_beam._moment_yyp  = self.moment_yyp
            electron_beam._moment_ypyp = self.moment_ypyp

            x, xp, y, yp = electron_beam.get_sigmas_all()

            self.electron_beam_size_h = x
            self.electron_beam_size_v = y
            self.electron_beam_divergence_h = xp
            self.electron_beam_divergence_v = yp
        else:
            electron_beam.set_sigmas_all(sigma_x=self.electron_beam_size_h,
                                         sigma_y=self.electron_beam_size_v,
                                         sigma_xp=self.electron_beam_divergence_h,
                                         sigma_yp=self.electron_beam_divergence_v)

            self.moment_xx = electron_beam._moment_xx
            self.moment_xpxp = electron_beam._moment_xpxp
            self.moment_yy = electron_beam._moment_yy
            self.moment_ypyp = electron_beam._moment_ypyp

        return LightSource(name=self.source_name,
                           electron_beam = electron_beam,
                           magnetic_structure = self.get_magnetic_structure())

    def check_magnetic_structure(self):
        raise NotImplementedError("Shoudl be implemented in subclasses")

    def get_magnetic_structure(self):
        raise NotImplementedError("Shoudl be implemented in subclasses")

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
            except:
                pass

    def select_syned_file(self):
        self.le_syned_file_name.setText(oasysgui.selectFileFromDialog(self, self.syned_file_name, "Open Syned File"))

    def read_syned_file(self):
        try:
            congruence.checkEmptyString(self.syned_file_name, "Syned File Name/Url")

            if len(self.syned_file_name) > 7 and self.syned_file_name[:7] == "http://":
                is_remote = True
            else:
                congruence.checkFile(self.syned_file_name)
                is_remote = False

            try:
                if is_remote:
                    content = load_from_json_url(self.syned_file_name)
                else:
                    content = load_from_json_file(self.syned_file_name)

                if isinstance(content, LightSource):
                    self.populate_fields(content)
                elif isinstance(content, Beamline) and not content._light_source is None:
                    self.populate_fields(content._light_source)
                else:
                    raise Exception("json file must contain a SYNED LightSource")
            except Exception as e:
                raise Exception("Error reading SYNED LightSource from file: " + str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)


    def populate_fields(self, light_source):
        electron_beam = light_source._electron_beam
        magnetic_structure = light_source._magnetic_structure

        self.check_magnetic_structure_instance(magnetic_structure)

        self.source_name = light_source._name

        self.electron_energy_in_GeV = electron_beam._energy_in_GeV
        self.electron_energy_spread = electron_beam._energy_spread
        self.ring_current = electron_beam._current
        self.number_of_bunches = electron_beam._number_of_bunches

        self.type_of_properties = 0

        self.moment_xx   = electron_beam._moment_xx
        self.moment_xxp  = electron_beam._moment_xxp
        self.moment_xpxp = electron_beam._moment_xpxp
        self.moment_yy   = electron_beam._moment_yy
        self.moment_yyp  = electron_beam._moment_yyp
        self.moment_ypyp = electron_beam._moment_ypyp

        x, xp, y, yp = electron_beam.get_sigmas_all()

        self.electron_beam_size_h = x
        self.electron_beam_size_v = y
        self.electron_beam_divergence_h = xp
        self.electron_beam_divergence_v = yp

        self.populate_magnetic_structure(magnetic_structure)

        self.set_TypeOfProperties()

    def check_magnetic_structure_instance(self, magnetic_structure):
        raise NotImplementedError()

    def populate_magnetic_structure(self, magnetic_structure):
        raise NotImplementedError()

    def write_syned_file(self):
        try:
            congruence.checkDir(self.syned_file_name)

            self.get_light_source().to_json(self.syned_file_name)

            QMessageBox.information(self, "File Read", "JSON file correctly written to disk", QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

