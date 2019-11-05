import sys

from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
from orangewidget.settings import Setting
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

from syned.storage_ring.light_source import ElectronBeam
from syned.beamline.beamline import Beamline
from syned.util.json_tools import load_from_json_file, load_from_json_url

class OWElectronBeam(GenericElement):

    # name = "Electron Beam"

    syned_file_name = Setting("Select *.json file")

    source_name         = Setting("Undefined")

    electron_energy_in_GeV = Setting(2.0)
    electron_energy_spread = Setting(0.001)
    ring_current           = Setting(0.5)
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

    electron_beam_emittance_h = Setting(0.0)
    electron_beam_emittance_v = Setting(0.0)
    electron_beam_beta_h = Setting(0.0)
    electron_beam_beta_v = Setting(0.0)
    electron_beam_alpha_h = Setting(0.0)
    electron_beam_alpha_v = Setting(0.0)
    electron_beam_eta_h = Setting(0.0)
    electron_beam_eta_v = Setting(0.0)
    electron_beam_etap_h = Setting(0.0)
    electron_beam_etap_v = Setting(0.0)


    type_of_properties = Setting(0)


    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Run Shadow4/Source", self)
        self.runaction.triggered.connect(self.run_shadow4)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run shadow4/source", callback=self.run_shadow4)
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


        self.tabs_control_area = oasysgui.tabWidget(self.controlArea)
        self.tabs_control_area.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_control_area.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_electron_beam = oasysgui.createTabPage(self.tabs_control_area, "Electron Beam Setting")



        oasysgui.lineEdit(self.tab_electron_beam, self, "source_name", "Electron Beam Name", labelWidth=260, valueType=str, orientation="horizontal")

        self.electron_beam_box = oasysgui.widgetBox(self.tab_electron_beam, "Electron Beam/Machine Parameters", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.electron_beam_box, self, "electron_energy_in_GeV", "Energy [GeV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.electron_beam_box, self, "electron_energy_spread", "Energy Spread", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.electron_beam_box, self, "ring_current", "Ring Current [A]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(self.electron_beam_box, self, "type_of_properties", label="Electron Beam Properties", labelWidth=350,
                     items=["From 2nd Moments", "From Size/Divergence", "From Twiss parameters","Zero emittance"],
                     callback=self.set_TypeOfProperties,
                     sendSelectedValue=False, orientation="horizontal")

        self.left_box_2_1 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=150)

        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xx",   "<x x>   [m^2]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xxp",  "<x x'>  [m.rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xpxp", "<x' x'> [rad^2]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yy",   "<y y>   [m^2]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yyp",  "<y y'>  [m.rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_ypyp", "<y' y'> [rad^2]", labelWidth=260, valueType=float, orientation="horizontal")


        self.left_box_2_2 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=150)

        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_h",       "Horizontal Beam Size \u03c3x [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_v",       "Vertical Beam Size \u03c3y [m]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_h", "Horizontal Beam Divergence \u03c3'x [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_v", "Vertical Beam Divergence \u03c3'y [rad]", labelWidth=260, valueType=float, orientation="horizontal")

        self.left_box_2_3 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="horizontal",height=150)
        self.left_box_2_3_l = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical")
        self.left_box_2_3_r = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_emittance_h", "\u03B5x [m.rad]",labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_alpha_h",     "\u03B1x",        labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_beta_h",      "\u03B2x [m]",    labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_eta_h",       "\u03B7x",        labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_etap_h",      "\u03B7'x",       labelWidth=75, valueType=float, orientation="horizontal")


        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_emittance_v", "\u03B5y [m.rad]",labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_alpha_v",     "\u03B1y",        labelWidth=75,valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_beta_v",      "\u03B2y [m]",    labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_eta_v",       "\u03B7y",        labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_etap_v",      "\u03B7'y",       labelWidth=75, valueType=float, orientation="horizontal")

        self.set_TypeOfProperties()

        gui.rubber(self.controlArea)


    def set_TypeOfProperties(self):
        self.left_box_2_1.setVisible(self.type_of_properties == 0)
        self.left_box_2_2.setVisible(self.type_of_properties == 1)
        self.left_box_2_3.setVisible(self.type_of_properties == 2)


    def check_data(self):
        congruence.checkStrictlyPositiveNumber(self.electron_energy_in_GeV , "Energy")
        congruence.checkStrictlyPositiveNumber(self.electron_energy_spread, "Energy Spread")
        congruence.checkStrictlyPositiveNumber(self.ring_current, "Ring Current")

        if self.type_of_properties == 0:
            congruence.checkPositiveNumber(self.moment_xx   , "Moment xx")
            congruence.checkPositiveNumber(self.moment_xpxp , "Moment xpxp")
            congruence.checkPositiveNumber(self.moment_yy   , "Moment yy")
            congruence.checkPositiveNumber(self.moment_ypyp , "Moment ypyp")
        elif self.type_of_properties == 1:
            congruence.checkPositiveNumber(self.electron_beam_size_h       , "Horizontal Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_divergence_h , "Vertical Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_size_v       , "Horizontal Beam Divergence")
            congruence.checkPositiveNumber(self.electron_beam_divergence_v , "Vertical Beam Divergence")
        elif self.type_of_properties == 2:
            congruence.checkPositiveNumber(self.electron_beam_emittance_h, "Horizontal Beam Emittance")
            congruence.checkPositiveNumber(self.electron_beam_emittance_v, "Vertical Beam Emittance")
            congruence.checkNumber(self.electron_beam_alpha_h, "Horizontal Beam Alpha")
            congruence.checkNumber(self.electron_beam_alpha_v, "Vertical Beam Alpha")
            congruence.checkNumber(self.electron_beam_beta_h, "Horizontal Beam Beta")
            congruence.checkNumber(self.electron_beam_beta_v, "Vertical Beam Beta")
            congruence.checkNumber(self.electron_beam_eta_h, "Horizontal Beam Dispersion Eta")
            congruence.checkNumber(self.electron_beam_eta_v, "Vertical Beam Dispersion Eta")
            congruence.checkNumber(self.electron_beam_etap_h, "Horizontal Beam Dispersion Eta'")
            congruence.checkNumber(self.electron_beam_etap_v, "Vertical Beam Dispersion Eta'")

        self.check_magnetic_structure()


    def run_shadow4(self):
        raise Exception("To be defined in the superclass")
        # try:
        #     self.check_data()
        #
        #     self.send("SynedData", Beamline(light_source=self.get_syned_light_source()))
        # except Exception as e:
        #     QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)
        #
        #     self.setStatusMessage("")
        #     self.progressBarFinished()


    def get_syned_electron_beam(self):
        electron_beam = ElectronBeam(energy_in_GeV=self.electron_energy_in_GeV,
                                     energy_spread=self.electron_energy_spread,
                                     current=self.ring_current,
                                     number_of_bunches=self.number_of_bunches)

        recalculate_fields = False

        if self.type_of_properties == 0:
            electron_beam.set_moments_horizontal(self.moment_xx,self.moment_xxp,self.moment_xpxp)
            electron_beam.set_moments_vertical(self.moment_yy, self.moment_yyp, self.moment_ypyp)

            if recalculate_fields:

                x, xp, y, yp = electron_beam.get_sigmas_all()

                self.electron_beam_size_h = x
                self.electron_beam_size_v = y
                self.electron_beam_divergence_h = xp
                self.electron_beam_divergence_v = yp

                twiss_all = electron_beam.get_twiss_no_dispersion_all()
                self.electron_beam_emittance_h = twiss_all[0]
                self.electron_beam_alpha_h     = twiss_all[1]
                self.electron_beam_beta_h      = twiss_all[2]
                self.electron_beam_eta_h       = 0.0
                self.electron_beam_etap_h      = 0.0
                self.electron_beam_emittance_v = twiss_all[3]
                self.electron_beam_alpha_v     = twiss_all[4]
                self.electron_beam_beta_v      = twiss_all[5]
                self.electron_beam_eta_v       = 0.0
                self.electron_beam_etap_v      = 0.0


        elif self.type_of_properties == 1:
            electron_beam.set_sigmas_all(sigma_x=self.electron_beam_size_h,
                                         sigma_y=self.electron_beam_size_v,
                                         sigma_xp=self.electron_beam_divergence_h,
                                         sigma_yp=self.electron_beam_divergence_v)

            if recalculate_fields:
                moments_all = electron_beam.get_moments_all()

                self.moment_xx   = moments_all[0]
                self.moment_xxp  = moments_all[1]
                self.moment_xpxp = moments_all[2]
                self.moment_yy   = moments_all[3]
                self.moment_yy   = moments_all[4]
                self.moment_ypyp = moments_all[5]

                twiss_all = electron_beam.get_twiss_no_dispersion_all()
                self.electron_beam_emittance_h = twiss_all[0]
                self.electron_beam_alpha_h     = twiss_all[1]
                self.electron_beam_beta_h      = twiss_all[2]
                self.electron_beam_eta_h       = 0.0
                self.electron_beam_etap_h      = 0.0
                self.electron_beam_emittance_v = twiss_all[3]
                self.electron_beam_alpha_v     = twiss_all[4]
                self.electron_beam_beta_v      = twiss_all[5]
                self.electron_beam_eta_v       = 0.0
                self.electron_beam_etap_v      = 0.0

        elif self.type_of_properties == 2:
            electron_beam.set_twiss_horizontal(self.electron_beam_emittance_h,
                                             self.electron_beam_alpha_h,
                                             self.electron_beam_beta_h,
                                             self.electron_beam_eta_h,
                                             self.electron_beam_etap_h)
            electron_beam.set_twiss_vertical(self.electron_beam_emittance_v,
                                             self.electron_beam_alpha_v,
                                             self.electron_beam_beta_v,
                                             self.electron_beam_eta_v,
                                             self.electron_beam_etap_v)

            if recalculate_fields:
                x, xp, y, yp = electron_beam.get_sigmas_all()

                self.electron_beam_size_h = x
                self.electron_beam_size_v = y
                self.electron_beam_divergence_h = xp
                self.electron_beam_divergence_v = yp

                moments_all = electron_beam.get_moments_all()

                self.moment_xx   = moments_all[0]
                self.moment_xxp  = moments_all[1]
                self.moment_xpxp = moments_all[2]
                self.moment_yy   = moments_all[3]
                self.moment_yy   = moments_all[4]
                self.moment_ypyp = moments_all[5]

        elif self.type_of_properties == 3:
            electron_beam.set_moments_all(0,0,0,0,0,0)


        return electron_beam

    # def check_magnetic_structure(self):
    #     raise NotImplementedError("Shoudl be implemented in subclasses")
    #
    # def get_magnetic_structure(self):
    #     raise NotImplementedError("Shoudl be implemented in subclasses")
    #
    # def callResetSettings(self):
    #     if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
    #         try:
    #             self.resetSettings()
    #         except:
    #             pass
    #
    # def select_syned_file(self):
    #     self.le_syned_file_name.setText(oasysgui.selectFileFromDialog(self, self.syned_file_name, "Open Syned File"))
    #
    # def read_syned_file(self):
    #     try:
    #         congruence.checkEmptyString(self.syned_file_name, "Syned File Name/Url")
    #
    #         if len(self.syned_file_name) > 7 and self.syned_file_name[:7] == "http://":
    #             is_remote = True
    #         else:
    #             congruence.checkFile(self.syned_file_name)
    #             is_remote = False
    #
    #         try:
    #             if is_remote:
    #                 content = load_from_json_url(self.syned_file_name)
    #             else:
    #                 content = load_from_json_file(self.syned_file_name)
    #
    #             if isinstance(content, LightSource):
    #                 self.populate_fields(content)
    #             elif isinstance(content, Beamline) and not content._light_source is None:
    #                 self.populate_fields(content._light_source)
    #             else:
    #                 raise Exception("json file must contain a SYNED LightSource")
    #         except Exception as e:
    #             raise Exception("Error reading SYNED LightSource from file: " + str(e))
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)


    def populate_fields_from_syned_electron_beam(self, electron_beam):

        self.check_magnetic_structure_instance(magnetic_structure)

        self.source_name = electron_beam._name

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

        self.set_TypeOfProperties()

    # def check_magnetic_structure_instance(self, magnetic_structure):
    #     raise NotImplementedError()
    #
    # def populate_magnetic_structure(self, magnetic_structure):
    #     raise NotImplementedError()
    #
    # def write_syned_file(self):
    #     try:
    #         congruence.checkDir(self.syned_file_name)
    #
    #         self.get_light_source().to_json(self.syned_file_name)
    #
    #         QMessageBox.information(self, "File Read", "JSON file correctly written to disk", QMessageBox.Ok)
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)




if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWElectronBeam()
    ow.show()
    a.exec_()
    ow.saveSettings()
