import sys
import time
import copy
import numpy

from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QSettings
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog, MessageDialog, selectSaveFileFromDialog
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow4.widgets.gui.ow_automatic_element import AutomaticElement
from shadow4.beam.s4_beam import S4Beam

class Histogram(AutomaticElement):

    name = "Histogram"
    description = "Display Data Tools: Histogram"
    icon = "icons/histogram.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1.0
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Shadow Data", ShadowData, "set_shadow_data")]

    IMAGE_WIDTH  = 878
    IMAGE_HEIGHT = 635

    want_main_area = 1

    plot_canvas = None
    input_data  = None

    image_plane                  = Setting(0)
    image_plane_new_position     = Setting(10.0)
    image_plane_rel_abs_position = Setting(0)

    x_column_index = Setting(25)

    x_range     = Setting(0)
    x_range_min = Setting(0.0)
    x_range_max = Setting(0.0)

    weight_column_index = Setting(22)
    rays                 = Setting(1)

    number_of_bins = Setting(100)

    title = Setting("Energy")

    autosave           = Setting(0)
    autosave_file_name = Setting("autosave_histogram_plot.hdf5")

    keep_result              = Setting(0)
    autosave_partial_results = Setting(0)

    conversion_active = Setting(1)

    cumulated_ticket = None
    plotted_ticket   = None
    autosave_file    = None
    autosave_prog_id = 0

    def __init__(self):
        super().__init__()

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        gui.button(button_box, self, "Refresh", callback=self.plot_results, height=45)
        gui.button(button_box, self, "Save Current Plot", callback=self.save_results, height=45)

        gui.separator(self.controlArea, 10)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        # graph tab
        tab_set = oasysgui.createTabPage(self.tabs_setting, "Plot Settings")
        tab_gen = oasysgui.createTabPage(self.tabs_setting, "Histogram Settings")

        screen_box = oasysgui.widgetBox(tab_set, "Screen Position Settings", addSpace=True, orientation="vertical", height=120)

        self.image_plane_combo = gui.comboBox(screen_box, self, "image_plane", label="Position of the Image",
                                              items=["On Image Plane", "Retraced"], labelWidth=260,
                                              callback=self.set_image_plane, sendSelectedValue=False, orientation="horizontal")

        self.image_plane_box = oasysgui.widgetBox(screen_box, "", addSpace=False, orientation="vertical", height=50)
        self.image_plane_box_empty = oasysgui.widgetBox(screen_box, "", addSpace=False, orientation="vertical", height=50)

        oasysgui.lineEdit(self.image_plane_box, self, "image_plane_new_position", "Image Plane new Position", labelWidth=220, valueType=float, orientation="horizontal")

        gui.comboBox(self.image_plane_box, self, "image_plane_rel_abs_position", label="Position Type", labelWidth=250,
                     items=["Absolute", "Relative"], sendSelectedValue=False, orientation="horizontal")

        self.set_image_plane()

        general_box = oasysgui.widgetBox(tab_set, "General Settings", addSpace=True, orientation="vertical", height=250)

        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="Column", labelWidth=70,
                                     items=S4Beam.column_names_with_column_number(),
                                     sendSelectedValue=False, orientation="horizontal", callback=self.set_column_index)

        gui.comboBox(general_box, self, "x_range", label="Range", labelWidth=250,
                     items=["<Default>", "Set.."],
                     callback=self.set_x_range, sendSelectedValue=False, orientation="horizontal")

        self.x_range_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.x_range_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        self.le_x_range_min = oasysgui.lineEdit(self.x_range_box, self, "x_range_min", "Min", labelWidth=220, valueType=float, orientation="horizontal")
        self.le_x_range_max = oasysgui.lineEdit(self.x_range_box, self, "x_range_max", "Max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_x_range()

        col_names = S4Beam.column_names_with_column_number()
        col_names.insert(0, "0: No Weight")
        self.weight_column = gui.comboBox(general_box, self, "weight_column_index", label="Weight", labelWidth=70,
                                         items=col_names,
                                         sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "rays", label="Rays", labelWidth=250,
                                     items=["All rays",
                                            "Good Only",
                                            "Lost Only"],
                                     sendSelectedValue=False, orientation="horizontal")

        autosave_box = oasysgui.widgetBox(tab_gen, "Autosave", addSpace=True, orientation="vertical", height=85)

        gui.comboBox(autosave_box, self, "autosave", label="Save automatically plot into file", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal", callback=self.set_autosave)

        self.autosave_box_1 = oasysgui.widgetBox(autosave_box, "", addSpace=False, orientation="horizontal", height=25)
        self.autosave_box_2 = oasysgui.widgetBox(autosave_box, "", addSpace=False, orientation="horizontal", height=25)

        self.le_autosave_file_name = oasysgui.lineEdit(self.autosave_box_1, self, "autosave_file_name", "File Name", labelWidth=100,  valueType=str, orientation="horizontal")

        gui.button(self.autosave_box_1, self, "...", callback=self.select_autosave_file)

        incremental_box = oasysgui.widgetBox(tab_gen, "Incremental Result", addSpace=True, orientation="vertical", height=120)

        gui.comboBox(incremental_box, self, "keep_result", label="Keep Result", labelWidth=250,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.set_autosave)

        self.cb_autosave_partial_results = gui.comboBox(incremental_box, self, "autosave_partial_results", label="Save partial plots into file", labelWidth=250,
                                                        items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        gui.button(incremental_box, self, "Clear", callback=self.clear_results)

        histograms_box = oasysgui.widgetBox(tab_gen, "Histograms settings", addSpace=True, orientation="vertical", height=90)

        oasysgui.lineEdit(histograms_box, self, "number_of_bins", "Number of Bins", labelWidth=250, valueType=int, orientation="horizontal")

        gui.comboBox(histograms_box, self, "conversion_active", label="Is U.M. conversion active", labelWidth=250,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.set_is_conversion_active)

        self.set_autosave()

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        self.image_box = gui.widgetBox(plot_tab, "Plot Result", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.shadow_output = oasysgui.textArea(height=580, width=800)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

    def clear_results(self, interactive=True):
        if not interactive: proceed = True
        else: proceed = ConfirmDialog.confirmed(parent=self)

        if proceed:
            self.input_data = ShadowData()
            self.cumulated_ticket = None
            self.plotted_ticket = None
            self.autosave_prog_id = 0
            if not self.autosave_file is None:
                self.autosave_file.close()
                self.autosave_file = None

            self.plot_canvas.clear()

    def set_column_index(self):
        self.__change_labels()

    def set_is_conversion_active(self):
        self.__change_labels()

    def set_x_range(self):
        self.x_range_box.setVisible(self.x_range == 1)
        self.x_range_box_empty.setVisible(self.x_range == 0)
        self.__change_labels()

    def __change_labels(self):
        def change_label(line_edit, index):
            label      = line_edit.parent().layout().itemAt(0).widget()
            label_text = label.text()
            if label_text[-1] == "]": label_text = label_text.split(sep="[")[0]
            else: label_text += " "
            if    index in [0, 1, 2] and self.is_conversion_active(): label_text += "[\u03BCm]"
            elif  index in [3, 4, 5] and self.is_conversion_active(): label_text += "[\u03BCrad]"
            else:                                                      label_text += S4Beam.column_units()[index]
            label.setText(label_text)

        if self.x_range == 1:
            change_label(self.le_x_range_min, self.x_column_index)
            change_label(self.le_x_range_max, self.x_column_index)

    def set_image_plane(self):
        self.image_plane_box.setVisible(self.image_plane==1)
        self.image_plane_box_empty.setVisible(self.image_plane==0)

    def set_autosave(self):
        self.autosave_box_1.setVisible(self.autosave==1)
        self.autosave_box_2.setVisible(self.autosave==0)

        self.cb_autosave_partial_results.setEnabled(self.autosave==1 and self.keep_result==1)

    def select_autosave_file(self):
        self.le_autosave_file_name.setText(oasysgui.selectFileFromDialog(self, self.autosave_file_name, "Select File", file_extension_filter="HDF5 Files (*.hdf5 *.h5 *.hdf)"))

    def replace_histo(self, beam, var, x_range, title, xtitle, ytitle, xum, flux):
        if self.plot_canvas is None:
            self.plot_canvas = ShadowPlot.DetailedHistoWidget(y_scale_factor=1.14)
            self.image_box.layout().addWidget(self.plot_canvas)

        try:
            if self.autosave == 1:
                if self.autosave_file is None:
                    self.autosave_file = ShadowPlot.HistogramHdf5File(congruence.checkDir(self.autosave_file_name))
                elif self.autosave_file.filename != congruence.checkFileName(self.autosave_file_name):
                    self.autosave_file.close()
                    self.autosave_file = ShadowPlot.HistogramHdf5File(congruence.checkDir(self.autosave_file_name))

            if self.keep_result == 1:
                self.cumulated_ticket, last_ticket = self.plot_canvas.plot_histo(beam, var, self.rays, x_range, self.weight_column_index, title, xtitle, ytitle,
                                                                                 nbins=self.number_of_bins,
                                                                                 xum=xum,
                                                                                 ticket_to_add=self.cumulated_ticket,
                                                                                 flux=flux)

                self.plotted_ticket = self.cumulated_ticket

                if self.autosave == 1:
                    self.autosave_prog_id += 1
                    self.autosave_file.write_coordinates(self.cumulated_ticket)
                    dataset_name = self.weight_column.itemText(self.weight_column_index)

                    self.autosave_file.add_histogram(self.cumulated_ticket, dataset_name=dataset_name)

                    if self.autosave_partial_results == 1:
                        if last_ticket is None: self.autosave_file.add_histogram(self.cumulated_ticket, plot_name="Histogram #" + str(self.autosave_prog_id), dataset_name=dataset_name)
                        else:                   self.autosave_file.add_histogram(last_ticket, plot_name="Histogram #" + str(self.autosave_prog_id), dataset_name=dataset_name)

                    self.autosave_file.flush()
            else:
                ticket, _ = self.plot_canvas.plot_histo(beam, var, self.rays, x_range, self.weight_column_index, title, xtitle, ytitle,
                                                        nbins=self.number_of_bins,
                                                        xum=xum,
                                                        flux=flux)

                self.cumulated_ticket = None
                self.plotted_ticket = ticket

                if self.autosave == 1:
                    self.autosave_prog_id += 1
                    self.autosave_file.write_coordinates(ticket)
                    self.autosave_file.add_histogram(ticket, dataset_name=self.weight_column.itemText(self.weight_column_index))
                    self.autosave_file.flush()

        except Exception as e:
            if not self.IS_DEVELOP:
                raise Exception("Data not plottable: Bad content")
            else:
                raise e

    def plot_histo(self, var_x, title, xtitle, ytitle, xum):
        beam_to_plot = self.input_data.beam
        flux         = self.input_data.get_flux(nolost=self.rays)

        if self.image_plane == 1:
            new_shadow_beam = self.input_data.beam.duplicate()
            dist = 0.0

            if self.image_plane_rel_abs_position == 1:  # relative
                dist = self.image_plane_new_position
            else:  # absolute
                if self.input_data.beamline is None == 0: beamline_element = None
                else:                                     beamline_element = self.input_data.beamline.get_beamline_element_at(-1)

                if beamline_element is None: image_plane = 0.0
                else:                        image_plane = beamline_element.get_coordinates().q()

                dist = self.image_plane_new_position - image_plane

            self.retrace_beam(new_shadow_beam, dist)

            beam_to_plot = new_shadow_beam

        x_range = self.get_range(beam_to_plot, var_x)

        self.replace_histo(beam_to_plot, var_x, x_range, title, xtitle, ytitle, xum, flux)

    def get_range(self, beam_to_plot : S4Beam, var_x):
        if self.x_range == 0 :
            x_max = 0
            x_min = 0

            x, good_only = beam_to_plot.get_columns((var_x, 10))

            x_to_plot = copy.deepcopy(x)

            go = numpy.where(good_only == 1)
            lo = numpy.where(good_only != 1)

            if self.rays == 0:
                x_max = numpy.array(x_to_plot[0:], float).max()
                x_min = numpy.array(x_to_plot[0:], float).min()
            elif self.rays == 1:
                x_max = numpy.array(x_to_plot[go], float).max()
                x_min = numpy.array(x_to_plot[go], float).min()
            elif self.rays == 2:
                x_max = numpy.array(x_to_plot[lo], float).max()
                x_min = numpy.array(x_to_plot[lo], float).min()

            x_range = [x_min, x_max]
        else:
            congruence.checkLessThan(self.x_range_min, self.x_range_max, "X range min", "X range max")

            factor = ShadowPlot.get_factor(var_x)
            x_range = [self.x_range_min / factor, self.x_range_max / factor]

        return x_range

    def save_results(self):
        if not self.plotted_ticket is None:
            try:
                file_name = oasysgui.selectSaveFileFromDialog(self, message="Save Current Plot", file_extension_filter="HDF5 Files (*.hdf5 *.h5 *.hdf)")

                if not file_name is None and not file_name.strip() == "":
                    if not (file_name.endswith("hd5") or file_name.endswith("hdf5") or file_name.endswith("hdf")): file_name += ".hdf5"

                    save_file = ShadowPlot.HistogramHdf5File(congruence.checkDir(file_name))
                    save_file.write_coordinates(self.plotted_ticket)
                    save_file.add_histogram(self.plotted_ticket, dataset_name=self.weight_column.itemText(self.weight_column_index))

                    save_file.close()
            except Exception as exception:
                self.prompt_exception(exception)

    def plot_results(self):
        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.write_stdout)

            if ShadowCongruence.check_empty_data(self.input_data):
                ShadowPlot.set_conversion_active(self.is_conversion_active())

                self.number_of_bins = congruence.checkPositiveNumber(self.number_of_bins, "Number of Bins")

                x, auto_title, xum = self.get_titles()

                self.plot_histo(x, title=self.title, xtitle=auto_title, ytitle="Number of Rays", xum=xum)

                plotted = True

            time.sleep(0.1)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        except Exception as exception:
            self.prompt_exception(exception)

    def get_titles(self):
        self.title = xum = auto_title = self.x_column.currentText()
        x = self.x_column_index + 1

        if x in [1, 2, 3] and self.is_conversion_active():
            xum        += " [\u03BCm]"
            auto_title += " [$\mu$m]"
        elif x in [4, 5, 6] and self.is_conversion_active():
            xum        += " [\u03BCrad]"
            auto_title += " [$\mu$rad]"
        else:
            xum        += " " + S4Beam.column_units()[self.x_column_index]
            auto_title += " " + S4Beam.column_units()[self.x_column_index]

        return x, auto_title, xum

    def set_shadow_data(self, shadow_data : ShadowData):
        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_empty_beam(shadow_data.beam):
                self.input_data = shadow_data
                if self.is_automatic_run: self.plot_results()
            else:
                MessageDialog.message(self, "Data not displayable: bad content", "Error", "critical")

    def write_stdout(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def retrace_beam(self, new_shadow_beam : S4Beam, dist):
        new_shadow_beam.retrace(dist)

    def is_conversion_active(self):
        return self.conversion_active == 1
