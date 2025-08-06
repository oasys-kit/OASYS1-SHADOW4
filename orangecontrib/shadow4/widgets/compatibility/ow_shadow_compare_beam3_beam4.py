import os, sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QTextCursor

from orangewidget import gui
from orangewidget.settings import Setting


from oasys.widgets import widget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import TriggerIn, TriggerOut, EmittingStream

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence as ShadowCongruence4

import Shadow
from shadow4.beam.s4_beam import S4Beam

"""
Tools to compare beams from shadow3 and Shadow4
"""
import numpy
from srxraylib.plot.gol import plot_scatter
from numpy.testing import assert_almost_equal

def check_six_columns_mean_and_std(beam3, beam4, do_plot=True, do_assert=False, assert_value=1e-2, to_meters=1.0, good_only=True):

    raysnew = beam4.rays
    rays = beam3.rays

    if good_only:
        indices = numpy.where(rays[:,9] > 0 )[0]
        rays = rays[indices, :].copy()
        raysnew = raysnew[indices, :].copy()

    if do_plot:

        plot_scatter(rays[:,3],rays[:,5],title="Divergences shadow3",show=False)
        plot_scatter(raysnew[:,3],raysnew[:,5],title="Divergences shadow4")

        plot_scatter(rays[:,0],rays[:,2],title="Real Space shadow3",show=False)
        plot_scatter(raysnew[:,0],raysnew[:,2],title="Real Space shadow4")

        #
        b3 = Shadow.Beam()
        b3.rays = rays

        b4 = Shadow.Beam()
        b4.rays = raysnew
        Shadow.ShadowTools.histo1(b3,11,ref=23,nolost=1)
        Shadow.ShadowTools.histo1(b4,11,ref=23,nolost=1)


    print("Comparing...")
    for i in range(6):
        m0 = (raysnew[:,i]).mean()
        m1 = (rays[:,i]*to_meters).mean()
        print("\ncol %d, mean sh3, sh4, |sh4-sh3|: %10g  %10g  %10g"%(i+1,m1,m0,numpy.abs(m0-m1)))
        std0 = raysnew[:,i].std()
        std1 = (rays[:,i]*to_meters).std()
        print("col %d, stdv sh3, sh4, |sh4-sh3|: %10g  %10g  %10g"%(i+1,std1,std0,numpy.abs(std0-std1)))

    if do_assert:
        print("\n\n\n\n")
        for i in range(6):
            m0 = (raysnew[:, i]).mean()
            m1 = (rays[:, i] * to_meters).mean()
            std0 = raysnew[:, i].std()
            std1 = (rays[:, i] * to_meters).std()
            try:
                assert(numpy.abs(m0-m1) < assert_value)
                assert(numpy.abs(std0-std1) < assert_value)
                print("col %d **passed**" % (i + 1))
            except:
                print("col %d **failed**" % (i + 1))

def check_almost_equal(beam3, beam4, do_assert=True, display_ray_number=10, level=1, skip_columns=[], good_only=1):

    print("\ncol#          shadow3         shadow4         (showing ray index=%d)" % display_ray_number)

    # display
    for i in range(18):
        txt = "col%d   %20.10f  %20.10f  " % (i + 1, beam3.rays[display_ray_number, i], beam4.rays[display_ray_number, i])
        print(txt)

    if do_assert:
        rays3 = beam3.rays.copy()
        rays4 = beam4.get_rays()
        if good_only:
            f  = numpy.where(rays4[:,9] > 0.0)
            if len(f[0])==0:
                print ('Warning: no GOOD rays, using ALL rays')
            else:
                rays3 = rays3[f[0], :].copy()
                rays4 = rays4[f[0], :].copy()

        print("\n\n\n\n")
        for i in range(18):
            txt = "col%d  " % (i + 1)
            if (i+1) in skip_columns:
                print(txt+"**column not asserted**")
            else:
                if i in [13,14]: # angles
                    try:
                        assert_almost_equal( numpy.mod(rays3[:, i], numpy.pi), numpy.mod(rays4[:, i], numpy.pi), level)
                        print(txt + "**passed**")
                    except:
                        print(txt + "********failed********", S4Beam.column_short_names_with_column_number()[i])
                else:
                    try:
                        assert_almost_equal(rays3[:,i], rays4[:,i], level)
                        print(txt + "**passed**")
                    except:
                        print(txt + "********failed********", S4Beam.column_short_names_with_column_number()[i])


class OWShadowCompareBeam3Beam4(widget.OWWidget):

    name = "Shadow3 Shadow4 Comparison"
    description = "Shadow3 Shadow4 Comparison"
    icon = "icons/compare3to4.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 30
    category = "Tools"
    keywords = ["script"]

    inputs = [("Input Beam", ShadowBeam, "setBeam3"),
              ("Shadow Data", ShadowData, "set_shadow_data")]

    input_shadow_data = None # shadow4
    input_beam = None # shadow3

    columns_6_flag = Setting(1)
    columns_6_assert = Setting(1)
    columns_6_good_only = Setting(1)
    columns_6_plot = Setting(0)

    columns_18_flag = Setting(1)
    columns_18_ray_index = Setting(10)
    columns_18_assert = Setting(1)
    columns_18_good_only = Setting(1)
    columns_18_level = Setting(6)
    columns_18_skip_columns = Setting("[]")

    IMAGE_WIDTH = 890
    IMAGE_HEIGHT = 680

    is_automatic_run = Setting(True)

    error_id = 0
    warning_id = 0
    info_id = 0

    MAX_WIDTH = 1320
    MAX_HEIGHT = 700

    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 560


    def __init__(self, show_automatic_box=True, show_general_option_box=True):
        super().__init__() # show_automatic_box=show_automatic_box)


        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.general_options_box = gui.widgetBox(self.controlArea, "General Options", addSpace=True, orientation="horizontal")
        self.general_options_box.setVisible(show_general_option_box)

        if show_automatic_box :
            gui.checkBox(self.general_options_box, self, 'is_automatic_run', 'Automatic Execution')

        #
        #
        #
        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Compare Beams", callback=self.compare_beams)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        gen_box6 = oasysgui.widgetBox(self.controlArea, "Compare 6 main columns",
                                     addSpace=False, orientation="vertical", height=200,
                                     width=self.CONTROL_AREA_WIDTH-5)

        gui.comboBox(gen_box6, self, "columns_6_flag", label="compare 6 cols mean & stdev",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        box60 = gui.widgetBox(gen_box6, orientation="horizontal")
        gui.comboBox(box60, self, "columns_6_assert", label="Assert?",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")
        self.show_at("self.columns_6_flag == 1", box60)

        box60b = gui.widgetBox(gen_box6, orientation="horizontal")
        gui.comboBox(box60b, self, "columns_6_good_only", label="used rays",
                     items=["All", "Good only"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")
        self.show_at("self.columns_6_flag == 1 and self.columns_6_assert == 1", box60b)

        box61 = gui.widgetBox(gen_box6, orientation="horizontal")
        gui.comboBox(box61, self, "columns_6_plot", label="show plots",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")
        self.show_at("self.columns_6_flag == 1", box61)

        gen_box18 = oasysgui.widgetBox(self.controlArea, "Compare all columns",
                                     addSpace=False, orientation="vertical", height=200,
                                     width=self.CONTROL_AREA_WIDTH-5)

        gui.comboBox(gen_box18, self, "columns_18_flag", label="compare 18 columns",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        box179 = gui.widgetBox(gen_box18, orientation="horizontal")
        oasysgui.lineEdit(box179, self, "columns_18_ray_index", "display ray index", labelWidth=300, valueType=int,
                          orientation="horizontal")
        self.show_at("self.columns_18_flag == 1", box179)

        box180 = gui.widgetBox(gen_box18, orientation="horizontal")
        gui.comboBox(box180, self, "columns_18_assert", label="Assert?",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")
        self.show_at("self.columns_18_flag == 1", box180)


        box180b = gui.widgetBox(gen_box18, orientation="horizontal")
        gui.comboBox(box180b, self, "columns_18_good_only", label="used rays",
                     items=["All", "Good only"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")
        self.show_at("self.columns_18_flag == 1 and self.columns_18_assert == 1", box180b)


        box181 = gui.widgetBox(gen_box18, orientation="horizontal")
        oasysgui.lineEdit(box181, self, "columns_18_level", "depth", labelWidth=150, valueType=int,
                          orientation="horizontal")
        self.show_at("self.columns_18_flag == 1 and self.columns_18_assert == 1", box181)

        box182 = gui.widgetBox(gen_box18, orientation="horizontal")
        oasysgui.lineEdit(box182, self, "columns_18_skip_columns", "skip columns (e.g. [10,11])", labelWidth=250, valueType=str,
                          orientation="horizontal")
        self.show_at("self.columns_18_flag == 1 and self.columns_18_assert == 1", box182)

        tabs_setting = oasysgui.tabWidget(self.mainArea)
        tabs_setting.setFixedHeight(self.IMAGE_HEIGHT)
        tabs_setting.setFixedWidth(self.IMAGE_WIDTH)

        tab_out = oasysgui.createTabPage(tabs_setting, "System Output")

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.IMAGE_WIDTH - 45)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)

        self.process_showers()

    def callResetSettings(self):
        pass

    def setBeam3(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                # sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                self.input_beam = beam

                if self.is_automatic_run:
                    self.compare_beams()

            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def set_shadow_data(self, input_data):

        if ShadowCongruence4.check_empty_data(input_data):
            self.input_data = input_data.duplicate()
            if self.is_automatic_run: self.compare_beams()

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def compare_beams(self):
        if self.input_beam is None:
            self.prompt_exception(ValueError("No Shadow3 input beam"))
            return

        if self.input_data is None:
            self.prompt_exception(ValueError("No Shadow4 input beam"))
            return

        try:

            self.shadow_output.setText("")
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            print("***** comparing shadow3 and shadow4 beams")

            fail = 0
            try:    beam3 = self.input_beam._beam.duplicate()
            except: print(">>> Error retrieving beam3"); fail = 1
            try:    beam4 = self.input_data.beam
            except: print(">>> Error retrieving beam4"); fail = 1

            if not fail:
                # pass to SI
                beam3.rays[:, 0:3] *= self.workspace_units_to_m
                beam3.rays[:, 12]  *= self.workspace_units_to_m

                if self.columns_6_flag:
                    print("\n\n***** comparing mean and stdev of 6 first columns")
                    check_six_columns_mean_and_std(beam3, beam4, do_assert=self.columns_6_assert, do_plot=self.columns_6_plot)

                if self.columns_18_flag:
                    print("\n\n***** comparing columns of all 18 columns")
                    if self.columns_18_skip_columns.strip() == "":
                        columns_18_skip_columns = "[]"
                    else:
                        columns_18_skip_columns = self.columns_18_skip_columns
                    skip_columns = eval(columns_18_skip_columns)

                    check_almost_equal(beam3, beam4,
                                       do_assert=self.columns_18_assert,
                                       level=self.columns_18_level,
                                       skip_columns=skip_columns,
                                       display_ray_number=self.columns_18_ray_index,
                                       good_only=self.columns_18_good_only)

            for i in range(20): print("") # needed to display correctly the full  text. Why?
        except Exception as exception:
            self.prompt_exception(exception)

if __name__ == "__main__":
    import sys
    import Shadow

    a = QApplication(sys.argv)
    ow = OWShadowCompareBeam3Beam4()
    ow.show()
    a.exec_()
    ow.saveSettings()