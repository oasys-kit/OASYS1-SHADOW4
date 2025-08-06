import os, sys
import numpy

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
from orangecontrib.shadow4.util.shadow4_util import ShadowPhysics
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D, plot_data2D, plot_multi_data1D


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

    want_main_area = True

    symbol = Setting("SiC")
    density = Setting(3.217)
    prerefl_file = Setting("reflec.dat")
    e_min = Setting(100.0)
    e_max = Setting(20000.0)
    e_step = Setting(100.0)

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


    IMAGE_WIDTH  = 860
    IMAGE_HEIGHT = 545

    MAX_WIDTH          = 1320
    MAX_HEIGHT         = 700
    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT   = 630

    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui") , "misc", "prerefl_usage.png")

    prerefl_instance = None

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

        tab_bas = oasysgui.createTabPage(tabs_setting, "Reflectivity Settings")

        tab_input_plots = oasysgui.createTabPage(tabs_setting, "Plots")

        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")

        self.populate_tab_basic_settings(tab_bas)

        self.populate_tab_plots(tab_input_plots)

        self.populate_tab_use_of_widget(tab_usa)

        self.shadow_output = oasysgui.textArea()
        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.TABS_AREA_HEIGHT)
        out_box.layout().addWidget(self.shadow_output)

        self.process_showers()

        gui.rubber(self.controlArea)

        self.set_visibility()

    def populate_tab_basic_settings(self, tab_bas):
        box = oasysgui.widgetBox(tab_bas, "Reflectivity Parameters", orientation="vertical")
        idx = -1

        # widget index 0
        idx += 1
        oasysgui.lineEdit(box, self, "symbol", tooltip="symbol",
                          label=self.unitLabels()[idx], addSpace=True, labelWidth=200, orientation="horizontal",
                          callback=self.set_Density)
        self.show_at(self.unitFlags()[idx], box)

        # widget index 1
        idx += 1
        oasysgui.lineEdit(box, self, "density", tooltip="density",
                          label=self.unitLabels()[idx], addSpace=True, valueType=float, labelWidth=200,
                          orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 2
        idx += 1
        box_2 = oasysgui.widgetBox(box, "", addSpace=True, orientation="horizontal")

        self.le_prerefl_file = oasysgui.lineEdit(box_2, self, "prerefl_file", tooltip="prerefl_file",
                                                 label=self.unitLabels()[idx], addSpace=True, labelWidth=180,
                                                 orientation="horizontal")

        gui.button(box_2, self, "...", callback=self.selectFile)

        self.show_at(self.unitFlags()[idx], box)

        # widget index 3
        idx += 1
        oasysgui.lineEdit(box, self, "e_min", tooltip="e_min",
                          label=self.unitLabels()[idx], addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 4
        idx += 1
        oasysgui.lineEdit(box, self, "e_max", tooltip="e_max",
                          label=self.unitLabels()[idx], addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 5
        idx += 1
        oasysgui.lineEdit(box, self, "e_step", tooltip="e_step",
                          label=self.unitLabels()[idx], addSpace=True,
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

    def populate_tab_plots(self, tab_plots):

        box = gui.widgetBox(tab_plots, "Optional scan plots", orientation="vertical")

        gui.comboBox(box, self, "plot_flag", tooltip="plot_flag",
                     label="Scan plot", addSpace=True,
                     items=['No', 'refraction index', 'attenuation coefficient',
                            'mirror reflectivity energy-scan',
                            'mirror reflectivity grazing angle-scan',
                            'mirror reflectivity energy-angle-scan'],
                     valueType=int, orientation="horizontal", labelWidth=270, callback=self.do_plots)

        self.box_plots = gui.widgetBox(tab_plots, "Optional scan plots", orientation="vertical")

        self.box_plot_e = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_e, self, "scan_e_from", label="from [eV]", tooltip="scan_e_from",
                          valueType=float, addSpace=True, labelWidth=100, orientation="horizontal",
                          callback=self.do_plots)
        oasysgui.lineEdit(self.box_plot_e, self, "scan_e_to", label="to [eV]", tooltip="scan_e_to",
                          valueType=float, addSpace=True, labelWidth=20, orientation="horizontal",
                          callback=self.do_plots)
        oasysgui.lineEdit(self.box_plot_e, self, "scan_e_n", label="points", tooltip="scan_e_n",
                          valueType=int, addSpace=True, labelWidth=50, orientation="horizontal",
                          callback=self.do_plots)
        self.box_plot_a0 = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_a0, self, "scan_a0", label="Fixed angle [mdeg]", tooltip="scan_a0",
                          valueType=float, addSpace=True, labelWidth=200, orientation="horizontal",
                          callback=self.do_plots)

        self.box_plot_a = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_a, self, "scan_a_from", label="from [deg]", tooltip="scan_a_from",
                          valueType=float, addSpace=True, labelWidth=100, orientation="horizontal",
                          callback=self.do_plots)
        oasysgui.lineEdit(self.box_plot_a, self, "scan_a_to", label="to [deg]", tooltip="scan_a_to",
                          valueType=float, addSpace=True, labelWidth=20, orientation="horizontal",
                          callback=self.do_plots)
        oasysgui.lineEdit(self.box_plot_a, self, "scan_a_n", label="points", tooltip="scan_a_n",
                          valueType=int, addSpace=True, labelWidth=50, orientation="horizontal",
                          callback=self.do_plots)
        self.box_plot_e0 = oasysgui.widgetBox(self.box_plots, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_e0, self, "scan_e0", label="Fixed energy [eV]", tooltip="scan_e0",
                          valueType=float, addSpace=True, labelWidth=200, orientation="horizontal",
                          callback=self.do_plots)


    def populate_tab_use_of_widget(self, tab_usa):
        tab_usa.setStyleSheet("background-color: white;")
        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")
        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))
        usage_box.layout().addWidget(label)

    def set_visibility(self):
        self.box_plots.setVisible(self.plot_flag > 0)
        self.box_plot_e.setVisible(False)
        self.box_plot_a0.setVisible(False)
        self.box_plot_a.setVisible(False)
        self.box_plot_e0.setVisible(False)

        if self.plot_flag == 1:
            self.box_plot_e.setVisible(True)
        elif self.plot_flag == 2:
            self.box_plot_e.setVisible(True)
        elif self.plot_flag == 3:
            self.box_plot_e.setVisible(True)
            self.box_plot_a0.setVisible(True)
        elif self.plot_flag == 4:
            self.box_plot_a.setVisible(True)
            self.box_plot_e0.setVisible(True)
        elif self.plot_flag == 5:
            self.box_plot_a.setVisible(True)
            self.box_plot_e.setVisible(True)

    def unitLabels(self):
         return ['Element/Compound formula','Density [ g/cm3 ]','File name (for SHADOW):','Minimum energy [eV]','Maximum energy [eV]','Energy step [eV]']

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

            self.prerefl_instance = PreRefl()
            self.prerefl_instance.read_preprocessor_file(self.prerefl_file)
            self.prerefl_instance.preprocessor_info()
            self.do_plots()
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)
            if self.IS_DEVELOP: raise exception

    def checkFields(self):
        self.symbol = ShadowPhysics.checkCompoundName(self.symbol)
        self.density = congruence.checkStrictlyPositiveNumber(self.density, "Density")
        self.e_min  = congruence.checkPositiveNumber(self.e_min , "Minimum Energy")
        self.e_max  = congruence.checkStrictlyPositiveNumber(self.e_max , "Maximum Energy")
        self.e_step = congruence.checkStrictlyPositiveNumber(self.e_step, "Energy step")
        congruence.checkLessOrEqualThan(self.e_min, self.e_max, "Minimum Energy", "Maximum Energy")
        congruence.checkDir(self.prerefl_file)

    def do_plots(self):

        self.set_visibility()

        self.plot_tab.layout().removeItem(self.plot_tab.layout().itemAt(0))

        if self.prerefl_instance is None: return

        if self.plot_flag == 0:
            plot_widget_id = plot_data1D([0], [0], xtitle="", ytitle="")
        elif self.plot_flag == 1:
            energy_array = numpy.linspace(self.scan_e_from, self.scan_e_to, self.scan_e_n)
            refraction_index = self.prerefl_instance.get_refraction_index(energy_array)
            delta = 1.0 - refraction_index.real
            beta = refraction_index.imag

            plot_widget_id = plot_multi_data1D(energy_array, [delta, beta],
                                         xtitle="Photon energy [eV]",
                                         ytitle="(n = 1 - delta + i beta)",
                                         ytitles=['delta', 'beta'])
        elif self.plot_flag == 2:
            energy_array = numpy.linspace(self.scan_e_from, self.scan_e_to, self.scan_e_n)
            att = self.prerefl_instance.get_attenuation_coefficient(energy_array)

            plot_widget_id = plot_data1D(energy_array, att,
                                         xtitle="Photon energy [eV]",
                                         ytitle="mu - attenuation coefficient cm^-1",
                                         )
        elif self.plot_flag == 3:
            energy_array = numpy.linspace(self.scan_e_from, self.scan_e_to, self.scan_e_n)
            RS, RP, _ = self.prerefl_instance.reflectivity_fresnel(grazing_angle_mrad=self.scan_a0,
                                                                           photon_energy_ev=energy_array,
                                                                           roughness_rms_A=0.0,
                                                                           )

            plot_widget_id = plot_multi_data1D(energy_array, [RS, RP],
                                         xtitle="Photon energy [eV]",
                                         ytitle="Mirror reflectivity @ %.3f mrad" % self.scan_a0,
                                         ytitles=['S-polarized', 'P-polarized'])
        elif self.plot_flag == 4:
            angle_array = numpy.linspace(self.scan_a_from, self.scan_a_to, self.scan_a_n)
            RS, RP, _ = self.prerefl_instance.reflectivity_fresnel(grazing_angle_mrad=angle_array,
                                                                           photon_energy_ev=self.scan_e0,
                                                                           roughness_rms_A=0.0,
                                                                           )

            plot_widget_id = plot_multi_data1D(angle_array, [RS, RP],
                                         xtitle="Grazing angle [mrad]",
                                         ytitle="Mirror reflectivity @ %.3f eV" % self.scan_e0,
                                         ytitles=['S-polarized', 'P-polarized'])

        elif self.plot_flag == 5:
            angle_array = numpy.linspace(self.scan_a_from, self.scan_a_to, self.scan_a_n)
            energy_array = numpy.linspace(self.scan_e_from, self.scan_e_to, self.scan_e_n)
            E = numpy.outer(energy_array, numpy.ones_like(angle_array))
            A = numpy.outer(numpy.ones_like(energy_array), angle_array)
            RS, RP, _ = self.prerefl_instance.reflectivity_fresnel(grazing_angle_mrad=A,
                                                                   photon_energy_ev=E,
                                                                   roughness_rms_A=0.0,
                                                                   )
            RS.shape = (energy_array.size, angle_array.size)
            # R_S_array = RS.reshape((energyN, thetaN))
            # A.shape = (energy_array.size, angle_array.shape)

            plot_widget_id = plot_data2D(RS, energy_array, angle_array,
                                         xtitle="Photon energy [eV]",
                                         ytitle="Grazing angle [mrad]",
                                         title="Mirror reflectivity (S-pol)",
                                         )

            # energyN = 1
            # energy1 = self.scan_e0
            # energy2 = self.scan_e0
            # thetaN = int(self.scan_a_n)
            # theta1 = self.scan_a_from
            # theta2 = self.scan_a_to
            # R_S_array, R_P_array, energy_array, theta_array = self.mlayer_instance.scan(
            #     energyN=energyN, energy1=energy1, energy2=energy2,
            #     thetaN=thetaN, theta1=theta1, theta2=theta2)
            # plot_widget_id = plot_data1D(theta_array, R_S_array[0, :]**2, xtitle="grazing angle [deg]", ytitle="Reflectivity")
        # elif self.plot_flag == 3:
        #     energyN = self.scan_e_n
        #     energy1 = self.scan_e_from
        #     energy2 = self.scan_e_to
        #     thetaN = self.scan_a_n
        #     theta1 = self.scan_a_from
        #     theta2 = self.scan_a_to
        #     R_S_array, R_P_array, energy_array, theta_array = self.mlayer_instance.scan(
        #         energyN=energyN, energy1=energy1, energy2=energy2,
        #         thetaN=thetaN, theta1=theta1, theta2=theta2)
        #     plot_widget_id = plot_data2D(R_S_array**2, energy_array, theta_array, title="title",
        #                                  xtitle="photon energy [eV]", ytitle="grazing angle [deg]")

        self.plot_tab.layout().addWidget(plot_widget_id)

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
