import sys
import numpy

from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import TriggerIn

from shadow4.beam.s4_beam import S4Beam
from orangecontrib.shadow4.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowPlot, ShadowCongruence
from orangecontrib.shadow4.util.python_script import PythonScript

class GenericElement(AutomaticElement):
    IMAGE_WIDTH  = 860
    IMAGE_HEIGHT = 545

    view_type = Setting(0)

    plotted_beam   = None
    footprint_beam = None
    has_footprint  = True

    def __init__(self, show_automatic_box=True, has_footprint=True):
        super().__init__(show_automatic_box)
        self.has_footprint = has_footprint

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        view_box = oasysgui.widgetBox(plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="Select level of Plotting",
                                            labelWidth=220,
                                            items=["Detailed Plot", "Preview", "None"],
                                            callback=self._set_plot_quality, sendSelectedValue=False, orientation="horizontal")


        # script tab
        script_tab = oasysgui.createTabPage(self.main_tabs, "Script")
        self.shadow4_script = PythonScript()
        self.shadow4_script.code_area.setFixedHeight(400)

        script_box = gui.widgetBox(script_tab, "Python script", addSpace=True, orientation="horizontal")
        script_box.layout().addWidget(self.shadow4_script)

        self.tab = []
        self.tabs = oasysgui.tabWidget(plot_tab)

        self._initialize_tabs()

        self.shadow_output = oasysgui.textArea(height=580, width=800)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

    def _initialize_tabs(self):
        current_tab = self.tabs.currentIndex()

        size = len(self.tab)
        indexes = range(0, size)
        for index in indexes: self.tabs.removeTab(size-1-index)

        titles = self._get_titles()
        if self.has_footprint: self.plot_canvas = [None]*(len(titles) + 1)
        else:                  self.plot_canvas = [None]*len(titles)
        self.tab = []

        for title in titles: self.tab.append(oasysgui.createTabPage(self.tabs, title))
        if self.has_footprint: self.tab.append(gui.createTabPage(self.tabs, "Footprint"))

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.tabs.setCurrentIndex(current_tab)

    def _check_not_interactive_conditions(self, input_data : ShadowData):
        not_interactive = False

        if not (input_data is None or input_data.scanning_data is None):
            not_interactive = input_data.scanning_data.has_additional_parameter("total_power")

        return not_interactive

    def _send_empty_beam(self):
        empty_beam      = S4Beam(N=1)
        empty_beam.rays = numpy.array([])

        self.send("Shadow Data", ShadowData(beam=empty_beam))
        self.send("Trigger",    TriggerIn(new_object=True))

    def _set_plot_quality(self):
        self.progressBarInit()

        if not self.plotted_beam is None:
            try:
                self._initialize_tabs()
                self._plot_results(self.plotted_beam, self.footprint_beam, progressBarValue=80)
            except Exception as exception:
                self.prompt_exception(exception)

        self.progressBarFinished()

    def _plot_xy_preview(self, beam, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, is_footprint=False):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = oasysgui.plotWindow(roi=False, control=False, position=True)
            self.plot_canvas[plot_canvas_index].setDefaultPlotLines(False)
            self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='blue')

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        ShadowPlot.plotxy_preview(self.plot_canvas[plot_canvas_index], beam, var_x, var_y, nolost=1, title=title, xtitle=xtitle, ytitle=ytitle, is_footprint=is_footprint)

        self.progressBarSet(progressBarValue)

    def _plot_xy_detailed(self, beam, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, xum="", yum="", is_footprint=False):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ShadowPlot.DetailedPlotWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_xy(beam, var_x, var_y, title, xtitle, ytitle, xum=xum, yum=yum, is_footprint=is_footprint)

        self.progressBarSet(progressBarValue)

    def _plot_histo_preview(self, beam, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = oasysgui.plotWindow(roi=False, control=False, position=True)
            self.plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
            self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='blue')

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        ShadowPlot.plot_histo_preview(self.plot_canvas[plot_canvas_index], beam, var, 1, 23, title, xtitle, ytitle)

        self.progressBarSet(progressBarValue)

    def _plot_histo_detailed(self, beam, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle, xum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ShadowPlot.DetailedHistoWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_histo(beam, var, 1, None, 23, title, xtitle, ytitle, xum=xum)

        self.progressBarSet(progressBarValue)

    def _plot_results(self, output_beam, footprint, progressBarValue=80):
        if not self.view_type == 2:
            if ShadowCongruence.check_empty_beam(output_beam):
                self.view_type_combo.setEnabled(False)

                ShadowPlot.set_conversion_active(self._is_conversion_active())

                variables = self._get_variables_to_plot()
                titles    = self._get_titles()
                xtitles   = self._get_x_titles()
                ytitles   = self._get_y_titles()
                xums      = self._get_x_um()
                yums      = self._get_y_um()

                try:
                    if self.view_type == 1:
                        self._plot_xy_preview(output_beam, progressBarValue + 4, variables[0][0], variables[0][1], plot_canvas_index=0, title=titles[0], xtitle=xtitles[0], ytitle=ytitles[0])
                        self._plot_xy_preview(output_beam, progressBarValue + 8, variables[1][0], variables[1][1], plot_canvas_index=1, title=titles[1], xtitle=xtitles[1], ytitle=ytitles[1])
                        self._plot_xy_preview(output_beam, progressBarValue + 12, variables[2][0], variables[2][1], plot_canvas_index=2, title=titles[2], xtitle=xtitles[2], ytitle=ytitles[2])
                        self._plot_xy_preview(output_beam, progressBarValue + 16, variables[3][0], variables[3][1], plot_canvas_index=3, title=titles[3], xtitle=xtitles[3], ytitle=ytitles[3])
                        self._plot_histo_preview(output_beam, progressBarValue + 20, variables[4], plot_canvas_index=4, title=titles[4], xtitle=xtitles[4], ytitle=ytitles[4])
                        if self.has_footprint: self._plot_xy_preview(footprint, progressBarValue + 20, 2, 1, plot_canvas_index=5, title="Footprint", xtitle="Y [m]", ytitle="X [m]", is_footprint=True)


                    elif self.view_type == 0:
                        self._plot_xy_detailed(output_beam, progressBarValue + 4, variables[0][0], variables[0][1], plot_canvas_index=0, title=titles[0], xtitle=xtitles[0], ytitle=ytitles[0], xum=xums[0], yum=yums[0])
                        self._plot_xy_detailed(output_beam, progressBarValue + 8, variables[1][0], variables[1][1], plot_canvas_index=1, title=titles[1], xtitle=xtitles[1], ytitle=ytitles[1], xum=xums[1], yum=yums[1])
                        self._plot_xy_detailed(output_beam, progressBarValue + 12, variables[2][0], variables[2][1], plot_canvas_index=2, title=titles[2], xtitle=xtitles[2], ytitle=ytitles[2], xum=xums[2], yum=yums[2])
                        self._plot_xy_detailed(output_beam, progressBarValue + 16, variables[3][0], variables[3][1], plot_canvas_index=3, title=titles[3], xtitle=xtitles[3], ytitle=ytitles[3], xum=xums[3], yum=yums[3])
                        self._plot_histo_detailed(output_beam, progressBarValue + 20, variables[4], plot_canvas_index=4, title=titles[4], xtitle=xtitles[4], ytitle=ytitles[4], xum=xums[4])
                        if self.has_footprint: self._plot_xy_detailed(footprint, progressBarValue + 20, 2, 1, plot_canvas_index=5, title="Footprint", xtitle="Y [m]", ytitle="X [m]", xum=("Y [m]"), yum=("X [m]"), is_footprint=True)

                except Exception as e:
                    self.view_type_combo.setEnabled(True)

                    raise Exception("Data not plottable: No good rays or bad content\nexception: " + str(e))

                self.view_type_combo.setEnabled(True)
            else:
                raise Exception("Empty Beam")

        self.plotted_beam   = output_beam
        self.footprint_beam = footprint

    def _write_stdout(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def _on_receiving_input(self):
        self._initialize_tabs()

    def _get_variables_to_plot(self):
        return [[1, 3], [4, 6], [1, 4], [3, 6], 26]

    def _get_titles(self):
        return ["X,Z", "X',Z'", "X,X'", "Z,Z'", "Energy"]

    def _get_x_titles(self):
        return [r'X [$\mu$m]', "X' [$\mu$rad]", r'X [$\mu$m]', r'Z [$\mu$m]', "Energy [eV]"]

    def _get_y_titles(self):
        return [r'Z [$\mu$m]', "Z' [$\mu$rad]", "X' [$\mu$rad]", "Z' [$\mu$rad]", "Number of Rays"]

    def _get_x_um(self):
        return ["X [" + u"\u03BC" + "m]", "X' [" + u"\u03BC" + "rad]", "X [" + u"\u03BC" + "m]", "Z [" + u"\u03BC" + "m]", "[eV]"]

    def _get_y_um(self):
        return ["Z [" + u"\u03BC" + "m]", "Z' [" + u"\u03BC" + "rad]", "X' [" + u"\u03BC" + "rad]", "Z' [" + u"\u03BC" + "rad]", None]

    def _is_conversion_active(self):
        return True

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = GenericElement()
    ow.show()
    a.exec_()
    ow.saveSettings()
