import copy
import sys
import time
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

class PlotXY(AutomaticElement):

    name = "Plot XY"
    description = "Display Data Tools: Plot XY"
    icon = "icons/plot_xy.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1.1
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Shadow Data", ShadowData, "set_shadow_data")]

    IMAGE_WIDTH  = 878
    IMAGE_HEIGHT = 635

    want_main_area = 1
    
    plot_canvas = None
    input_beam  = None

    image_plane                  = Setting(0)
    image_plane_new_position     = Setting(10.0)
    image_plane_rel_abs_position = Setting(0)

    x_column_index = Setting(0)
    x_range        = Setting(0)
    x_range_min    = Setting(0.0)
    x_range_max    = Setting(0.0)

    y_column_index = Setting(2)
    y_range        = Setting(0)
    y_range_min    = Setting(0.0)
    y_range_max    = Setting(0.0)

    weight_column_index = Setting(22)
    rays                = Setting(1)
    cartesian_axis      = Setting(1)

    number_of_bins_h = Setting(100)
    number_of_bins_v = Setting(100)

    title = Setting("X,Z")

    autosave           = Setting(0)
    autosave_file_name = Setting("autosave_xy_plot.hdf5")

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

        general_box = oasysgui.widgetBox(tab_set, "Variables Settings", addSpace=True, orientation="vertical", height=350)

        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="H Column",labelWidth=70,
                                     items=S4Beam.column_names_with_column_number(),
                                     sendSelectedValue=False, orientation="horizontal", callback=self.set_x_column_index)

        gui.comboBox(general_box, self, "x_range", label="H Range", labelWidth=250,
                     items=["<Default>", "Set.."],
                     callback=self.set_x_range, sendSelectedValue=False, orientation="horizontal")

        self.x_range_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.x_range_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        self.le_x_range_min = oasysgui.lineEdit(self.x_range_box, self, "x_range_min", "H min", labelWidth=220, valueType=float, orientation="horizontal")
        self.le_x_range_max = oasysgui.lineEdit(self.x_range_box, self, "x_range_max", "H max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_x_range()

        self.y_column = gui.comboBox(general_box, self, "y_column_index", label="V Column",labelWidth=70,
                                     items=S4Beam.column_names_with_column_number(),
                                     sendSelectedValue=False, orientation="horizontal", callback=self.set_y_column_index)

        gui.comboBox(general_box, self, "y_range", label="V Range", labelWidth=250,
                     items=["<Default>", "Set.."],
                     callback=self.set_y_range, sendSelectedValue=False, orientation="horizontal")

        self.y_range_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.y_range_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        self.le_y_range_min = oasysgui.lineEdit(self.y_range_box, self, "y_range_min", "V min", labelWidth=220, valueType=float, orientation="horizontal")
        self.le_y_range_max = oasysgui.lineEdit(self.y_range_box, self, "y_range_max", "V max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_y_range()

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

        gui.comboBox(general_box, self, "cartesian_axis", label="Cartesian Axis",labelWidth=300,
                                     items=["No",
                                            "Yes"],
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

        histograms_box = oasysgui.widgetBox(tab_gen, "Histograms settings", addSpace=True, orientation="vertical", height=120)

        oasysgui.lineEdit(histograms_box, self, "number_of_bins_h", "Number of Bins H", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(histograms_box, self, "number_of_bins_v", "Number of Bins V", labelWidth=250, valueType=int, orientation="horizontal")
        gui.comboBox(histograms_box, self, "conversion_active", label="Is U.M. conversion active", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal", callback=self.set_is_conversion_active)

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
            self.input_beam = None
            self.cumulated_ticket = None
            self.plotted_ticket = None
            self.autosave_prog_id = 0
            if not self.autosave_file is None:
                self.autosave_file.close()
                self.autosave_file = None

            if not self.plot_canvas is None:
                self.plot_canvas.clear()

    def set_autosave(self):
        self.autosave_box_1.setVisible(self.autosave==1)
        self.autosave_box_2.setVisible(self.autosave==0)

        self.cb_autosave_partial_results.setEnabled(self.autosave==1 and self.keep_result==1)

    def set_x_column_index(self):
        self.__change_labels(dir='x')

    def set_y_column_index(self):
        self.__change_labels(dir='y')

    def set_is_conversion_active(self):
        self.__change_labels(dir='b')

    def set_x_range(self):
        self.x_range_box.setVisible(self.x_range == 1)
        self.x_range_box_empty.setVisible(self.x_range == 0)
        self.__change_labels(dir='x')

    def set_y_range(self):
        self.y_range_box.setVisible(self.y_range == 1)
        self.y_range_box_empty.setVisible(self.y_range == 0)
        self.__change_labels(dir='y')

    def __change_labels(self, dir='b'):
        def change_label(line_edit, index):
            label      = line_edit.parent().layout().itemAt(0).widget()
            label_text = label.text()
            if label_text[-1] == "]": label_text = label_text.split(sep="[")[0]
            else: label_text += " "
            if    index in [0, 1, 2] and self.is_conversion_active(): label_text += "[\u03BCm]"
            elif  index in [3, 4, 5] and self.is_conversion_active(): label_text += "[\u03BCrad]"
            else:                                                      label_text += S4Beam.column_units()[index]
            label.setText(label_text)

        if self.x_range == 1 and dir in ['x', 'b']:
            change_label(self.le_x_range_min, self.x_column_index)
            change_label(self.le_x_range_max, self.x_column_index)
        if self.y_range == 1 and dir in ['y', 'b']:
            change_label(self.le_y_range_min, self.y_column_index)
            change_label(self.le_y_range_max, self.y_column_index)

    def set_image_plane(self):
        self.image_plane_box.setVisible(self.image_plane==1)
        self.image_plane_box_empty.setVisible(self.image_plane==0)

    def select_autosave_file(self):
        self.le_autosave_file_name.setText(oasysgui.selectFileFromDialog(self, self.autosave_file_name, "Select File", file_extension_filter="HDF5 Files (*.hdf5 *.h5 *.hdf)"))

    def replace_plot(self, beam, var_x, var_y, title, xtitle, ytitle, x_range, y_range, nbins=100, nbins_h=None, nbins_v=None, nolost=0, xum="", yum="", flux=None):
        if self.plot_canvas is None:
            self.plot_canvas = ShadowPlot.DetailedPlotWidget(y_scale_factor=1.14)
            self.image_box.layout().addWidget(self.plot_canvas)

        try:
            if self.autosave == 1:
                if self.autosave_file is None:
                    self.autosave_file = ShadowPlot.PlotXYHdf5File(congruence.checkDir(self.autosave_file_name))
                elif self.autosave_file.filename != congruence.checkFileName(self.autosave_file_name):
                    self.autosave_file.close()
                    self.autosave_file = ShadowPlot.PlotXYHdf5File(congruence.checkDir(self.autosave_file_name))

            if nbins_h is None: nbins_h=nbins
            if nbins_v is None: nbins_v=nbins

            if self.keep_result == 1:
                self.cumulated_ticket, last_ticket = self.plot_canvas.plot_xy(beam, var_x, var_y, title, xtitle, ytitle,
                                                                              xrange=x_range,
                                                                              yrange=y_range,
                                                                              nbins_h=nbins_h,
                                                                              nbins_v=nbins_v,
                                                                              nolost=nolost,
                                                                              xum=xum,
                                                                              yum=yum,
                                                                              ref=self.weight_column_index,
                                                                              ticket_to_add=self.cumulated_ticket,
                                                                              flux=flux)

                self.plotted_ticket = self.cumulated_ticket

                if self.autosave == 1:
                    self.autosave_prog_id += 1
                    self.autosave_file.write_coordinates(self.cumulated_ticket)
                    dataset_name = self.weight_column.itemText(self.weight_column_index)

                    self.autosave_file.add_plot_xy(self.cumulated_ticket, dataset_name=dataset_name)

                    if self.autosave_partial_results == 1:
                        if last_ticket is None: self.autosave_file.add_plot_xy(self.cumulated_ticket, plot_name="Plot XY #" + str(self.autosave_prog_id), dataset_name=dataset_name)
                        else:                   self.autosave_file.add_plot_xy(last_ticket, plot_name="Plot X #" + str(self.autosave_prog_id), dataset_name=dataset_name)

                    self.autosave_file.flush()
            else:
                ticket, _ = self.plot_canvas.plot_xy(beam, var_x, var_y, title, xtitle, ytitle,
                                                     xrange=x_range,
                                                     yrange=y_range,
                                                     nbins_h=nbins_h,
                                                     nbins_v=nbins_v,
                                                     nolost=nolost,
                                                     xum=xum,
                                                     yum=yum,
                                                     ref=self.weight_column_index,
                                                     flux=flux)

                self.cumulated_ticket = None
                self.plotted_ticket = ticket

                if self.autosave == 1:
                    self.autosave_prog_id += 1
                    self.autosave_file.write_coordinates(ticket)
                    self.autosave_file.add_plot_xy(ticket, dataset_name=self.weight_column.itemText(self.weight_column_index))
                    self.autosave_file.flush()

        except Exception as e:
            if not self.IS_DEVELOP:
                raise Exception("Data not plottable: Bad content")
            else:
                raise e

    def plot_xy(self, var_x, var_y, title, xtitle, ytitle, xum, yum):
        beam_to_plot = self.input_data.beam
        flux         = self.input_data.get_flux(nolost=self.rays)

        if self.image_plane == 1:
            new_shadow_beam = self.input_data.beam.duplicate()
            dist = 0.0

            if self.image_plane_rel_abs_position == 1:  # relative
                dist = self.image_plane_new_position
            else:  # absolute
                if self.input_beam.historySize() == 0:
                    historyItem = None
                else:
                    historyItem = self.input_beam.getOEHistory(oe_number=self.input_beam._oe_number)

                if historyItem is None: image_plane = 0.0
                elif self.input_beam._oe_number == 0: image_plane = 0.0
                else:
                    if self.input_data.beamline is None == 0: beamline_element = None
                    else:                                     beamline_element = self.input_data.beamline.get_beamline_element_at(-1)

                    if beamline_element is None: image_plane = 0.0
                    else:                        image_plane = beamline_element.get_coordinates().q()

                dist = self.image_plane_new_position - image_plane

            self.retrace_beam(new_shadow_beam, dist)

            beam_to_plot = new_shadow_beam

        x_range, y_range = self.get_ranges(beam_to_plot, var_x, var_y)

        self.replace_plot(beam_to_plot, var_x, var_y, title, xtitle, ytitle,
                          x_range=x_range,
                          y_range=y_range,
                          nbins_h=int(self.number_of_bins_h),
                          nbins_v=int(self.number_of_bins_v),
                          nolost=self.rays,
                          xum=xum,
                          yum=yum,
                          flux=flux)

    def get_ranges(self, beam_to_plot, var_x, var_y):
        x_range = None
        y_range = None
        factor1 = ShadowPlot.get_factor(var_x)
        factor2 = ShadowPlot.get_factor(var_y)

        if self.x_range == 0 and self.y_range == 0:
            if self.cartesian_axis == 1:
                x_max = 0
                y_max = 0
                x_min = 0
                y_min = 0

                x, y, good_only = beam_to_plot.get_columns((var_x, var_y, 10))

                x_to_plot = copy.deepcopy(x)
                y_to_plot = copy.deepcopy(y)

                go = numpy.where(good_only == 1)
                lo = numpy.where(good_only != 1)

                if self.rays == 0:
                    x_max = numpy.array(x_to_plot[0:], float).max()
                    y_max = numpy.array(y_to_plot[0:], float).max()
                    x_min = numpy.array(x_to_plot[0:], float).min()
                    y_min = numpy.array(y_to_plot[0:], float).min()
                elif self.rays == 1:
                    x_max = numpy.array(x_to_plot[go], float).max()
                    y_max = numpy.array(y_to_plot[go], float).max()
                    x_min = numpy.array(x_to_plot[go], float).min()
                    y_min = numpy.array(y_to_plot[go], float).min()
                elif self.rays == 2:
                    x_max = numpy.array(x_to_plot[lo], float).max()
                    y_max = numpy.array(y_to_plot[lo], float).max()
                    x_min = numpy.array(x_to_plot[lo], float).min()
                    y_min = numpy.array(y_to_plot[lo], float).min()

                x_range = [x_min, x_max]
                y_range = [y_min, y_max]
        else:
            if self.x_range == 1:
                congruence.checkLessThan(self.x_range_min, self.x_range_max, "X range min", "X range max")
                x_range = [self.x_range_min / factor1, self.x_range_max / factor1]

            if self.y_range == 1:
                congruence.checkLessThan(self.y_range_min, self.y_range_max, "Y range min", "Y range max")
                y_range = [self.y_range_min / factor2, self.y_range_max / factor2]

        return x_range, y_range

    def save_results(self):
        if not self.plotted_ticket is None:
            try:
                file_name = oasysgui.selectSaveFileFromDialog(self, message="Save Current Plot", file_extension_filter="HDF5 Files (*.hdf5 *.h5 *.hdf)")

                if not file_name is None and not file_name.strip()=="":
                    if not (file_name.endswith("hd5") or file_name.endswith("hdf5") or file_name.endswith("hdf")): file_name += ".hdf5"

                    save_file = ShadowPlot.PlotXYHdf5File(congruence.checkDir(file_name))
                    save_file.write_coordinates(self.plotted_ticket)
                    save_file.add_plot_xy(self.plotted_ticket, dataset_name=self.weight_column.itemText(self.weight_column_index))

                    save_file.close()
            except Exception as exception:
                self.prompt_exception(exception)

    def plot_results(self):
        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if ShadowCongruence.check_empty_data(self.input_data):
                ShadowPlot.set_conversion_active(self.is_conversion_active())

                self.number_of_bins_h = congruence.checkStrictlyPositiveNumber(self.number_of_bins_h, "Number of Bins (H)")
                self.number_of_bins_v = congruence.checkStrictlyPositiveNumber(self.number_of_bins_v, "Number of Bins (V)")

                x, y, auto_x_title, auto_y_title, xum, yum = self.get_titles()

                self.plot_xy(x, y, title=self.title, xtitle=auto_x_title, ytitle=auto_y_title, xum=xum, yum=yum)

                plotted = True

            time.sleep(0.1)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        except Exception as exception:
            self.prompt_exception(exception)

    def get_titles(self):
        xum = auto_x_title = self.x_column.currentText()
        yum = auto_y_title = self.y_column.currentText()

        self.title = S4Beam.column_short_names()[self.x_column_index] + "," + S4Beam.column_short_names()[self.y_column_index]

        def get_strings(um, auto_title, col, index):
            if col in [1, 2, 3] and self.is_conversion_active():
                um         += " [\u03BCm]"
                auto_title += " [$\mu$m]"
            elif col in [4, 5, 6] and self.is_conversion_active():
                um         += " [\u03BCrad]"
                auto_title += " [$\mu$rad]"
            else:
                um         += " " + S4Beam.column_units()[index]
                auto_title += " " + S4Beam.column_units()[index]

            return um, auto_title

        x = self.x_column_index + 1
        y = self.y_column_index + 1
        xum, auto_x_title = get_strings(xum, auto_x_title, x, self.x_column_index)
        yum, auto_y_title = get_strings(yum, auto_y_title, y, self.y_column_index)

        return x, y, auto_x_title, auto_y_title, xum, yum

    def set_shadow_data(self, shadow_data : ShadowData):
        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_empty_beam(shadow_data.beam):
                self.input_data = shadow_data
                if self.is_automatic_run: self.plot_results()
            else:
                MessageDialog.message(self, "Data not displayable: bad content", "Error", "critical")

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def retrace_beam(self, new_shadow_beam: S4Beam, dist):
        new_shadow_beam.retrace(dist)

    def is_conversion_active(self):
        return self.conversion_active == 1
