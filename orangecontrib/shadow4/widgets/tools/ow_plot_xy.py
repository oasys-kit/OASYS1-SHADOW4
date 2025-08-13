import sys
import time
import numpy
import copy

from PyQt5.QtGui import QTextCursor
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog, MessageDialog, selectSaveFileFromDialog

from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow4.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow4.util.python_script import PythonScript

from shadow4.beam.s4_beam import S4Beam

class _PlotXY(AutomaticElement):

    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Shadow Data", ShadowData, "set_shadow_data")]

    IMAGE_WIDTH  = 878
    IMAGE_HEIGHT = 635

    want_main_area = 1
    
    plot_canvas = None
    input_beam  = None

    x_range        = Setting(0)
    x_range_min    = Setting(0.0)
    x_range_max    = Setting(0.0)

    y_range        = Setting(0)
    y_range_min    = Setting(0.0)
    y_range_max    = Setting(0.0)

    weight_column_index = Setting(23)
    rays                = Setting(1)
    cartesian_axis      = Setting(0)

    number_of_bins_h = Setting(100)
    number_of_bins_v = Setting(100)

    flip_h = Setting(0)
    flip_v = Setting(0)

    title = Setting("")

    autosave           = Setting(0)
    autosave_file_name = Setting("autosave_xy_plot.hdf5")

    keep_result              = Setting(0)
    autosave_partial_results = Setting(0)

    cumulated_ticket = None
    plotted_ticket   = None
    autosave_file    = None
    autosave_prog_id = 0

    def __init__(self, allow_retrace=True):
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

        if allow_retrace:
            screen_box = oasysgui.widgetBox(tab_set, "Screen Position Settings", addSpace=True, orientation="vertical", height=120)

            self.image_plane_combo = gui.comboBox(screen_box, self, "image_plane", label="Position of the Image",
                                                  items=["On Image Plane", "Retraced"], labelWidth=260,
                                                  callback=self.set_image_plane, sendSelectedValue=False, orientation="horizontal")

            self.image_plane_box = oasysgui.widgetBox(screen_box, "", addSpace=False, orientation="vertical", height=50)
            self.image_plane_box_empty = oasysgui.widgetBox(screen_box, "", addSpace=False, orientation="vertical", height=50)

            oasysgui.lineEdit(self.image_plane_box, self, "image_plane_new_position", "New (relative) position [m]", labelWidth=220, valueType=float, orientation="horizontal")

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

        gui.comboBox(general_box, self, "cartesian_axis", label="Same aspect ratio (Cartesian Axes)",labelWidth=300,
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

        histograms_box = oasysgui.widgetBox(tab_gen, "Histograms settings", addSpace=True, orientation="vertical", height=200)

        oasysgui.lineEdit(histograms_box, self, "number_of_bins_h", "Number of Bins H", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(histograms_box, self, "number_of_bins_v", "Number of Bins V", labelWidth=250, valueType=int, orientation="horizontal")
        gui.comboBox(histograms_box, self, "conversion_active", label="Is U.M. conversion active", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal", callback=self.set_is_conversion_active)

        gui.comboBox(histograms_box, self, "flip_h", label="Flip H Axis", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal")
        gui.comboBox(histograms_box, self, "flip_v", label="Flip V Axis", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal")

        self.set_autosave()

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")
        script_tab = oasysgui.createTabPage(self.main_tabs, "Script")

        self.image_box = gui.widgetBox(plot_tab, "Plot Result", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.shadow4_script = PythonScript()
        self.shadow4_script.code_area.setFixedHeight(400)
        script_box = gui.widgetBox(script_tab, "Python script", addSpace=True, orientation="horizontal")
        script_box.layout().addWidget(self.shadow4_script)

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
                                                     flux=flux,
                                                     flip_h=self.flip_h==1,
                                                     flip_v=self.flip_v==1)

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
    def set_script(self, x_range, y_range):

        # script
        try:
            beamline = self.input_data.beamline.duplicate()
            script = beamline.to_python_code()

            indented_script = '\n'.join('    ' + line for line in script.splitlines())

            final_script = "def run_beamline():\n"
            final_script += indented_script
            final_script += "\n    return beam, footprint"
            final_script += "\n\n"

            if self.image_plane > 0:
                retrace = "%s.retrace(%f)" % (self.get_beam_to_plot(return_str=True), self.image_plane_new_position)
            else:
                retrace = ""

            dict = {"beam_str": self.get_beam_to_plot(return_str=True),
                    "var_x": 1 + self.x_column_index,
                    "var_y": 1 + self.y_column_index,
                    "nbins_h": self.number_of_bins_h,
                    "nbins_v": self.number_of_bins_v,
                    "xrange": x_range,
                    "yrange": y_range,
                    "nolost": self.rays,
                    "ref": self.weight_column_index,
                    "retrace": retrace,
                    }

            script_template = """#
# main 
#
from srxraylib.plot.gol import plot, plot_image, plot_image_with_histograms, plot_show

# WARNING: NO incremental result allowed!!"
beam, footprint = run_beamline()
{retrace}

ticket = {beam_str}.histo2({var_x}, {var_y}, nbins_h={nbins_h}, nbins_v={nbins_v}, xrange={xrange}, yrange={yrange}, nolost={nolost}, ref={ref})

title = "I: %.1f " % ticket['intensity']
if ticket['fwhm_h'] is not None: title += "FWHM H: %f " % ticket['fwhm_h']
if ticket['fwhm_v'] is not None: title += "FWHM V: %f " % ticket['fwhm_v']

plot_image_with_histograms(ticket['histogram'], ticket['bin_h_center'], ticket['bin_v_center'],
    title=title, xtitle="column {var_x}", ytitle="column {var_y}",
    cmap='jet', add_colorbar=True, figsize=(8, 8), histo_path_flag=1, show=1)
"""

            final_script += script_template.format_map(dict)

            self.shadow4_script.set_code(final_script)
        except:
            final_script += "\n\n\n# cannot retrieve beamline data from shadow_data"

        self.shadow4_script.set_code(final_script)


    def plot_xy(self, var_x, var_y, title, xtitle, ytitle, xum, yum):
        beam_to_plot = self.get_beam_to_plot()
        flux         = self.input_data.get_flux(nolost=self.rays)


        if self.image_plane == 1:
            new_shadow_beam = beam_to_plot.duplicate()
            dist = self.image_plane_new_position
            self.retrace_beam(new_shadow_beam, dist)
            beam_to_plot = new_shadow_beam

        x_range, y_range = self.get_ranges(beam_to_plot, var_x, var_y)

        self.set_script(x_range, y_range)

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
        factor1 = ShadowPlot.get_factor(var_x)
        factor2 = ShadowPlot.get_factor(var_y)

        if self.x_range == 1:
            congruence.checkLessThan(self.x_range_min, self.x_range_max, "X range min", "X range max")
            x_range = [self.x_range_min / factor1, self.x_range_max / factor1]
        else:
            x, y = beam_to_plot.get_columns((var_x, var_y), nolost=self.rays)
            x_max = x.max()
            x_min = x.min()
            if numpy.abs(x_max - x_min) < 1e-10:
                x_min -= 1e-10
                x_max -= 1e-10
            x_range = [x_min, x_max]

        if self.y_range == 1:
            congruence.checkLessThan(self.y_range_min, self.y_range_max, "Y range min", "Y range max")
            y_range = [self.y_range_min / factor2, self.y_range_max / factor2]
        else:
            x, y = beam_to_plot.get_columns((var_x, var_y), nolost=self.rays)
            y_max = y.max()
            y_min = y.min()
            if numpy.abs(y_max - y_min) < 1e-10:
                y_min -= 1e-10
                y_max -= 1e-10
            y_range = [y_min, y_max]

        if self.cartesian_axis == 1:
            x_range[0] = numpy.min((x_range[0], y_range[0]))
            x_range[1] = numpy.max((x_range[1], y_range[1]))
            y_range[0] = x_range[0]
            y_range[1] = x_range[1]

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

class PlotXY(_PlotXY):
    name = "Plot XY"
    description = "Display Data Tools: Plot XY"
    icon = "icons/plot_xy.png"
    priority = 1.1
    inputs = copy.deepcopy(_PlotXY.inputs)

    x_column_index = Setting(0)
    y_column_index = Setting(2)
    conversion_active = Setting(1)
    image_plane              = Setting(0)
    image_plane_new_position = Setting(10.0)

    def __init__(self):
        super().__init__(allow_retrace=True)

    def set_shadow_data(self, shadow_data : ShadowData):
        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_empty_beam(shadow_data.beam):
                self.input_data = shadow_data
                if self.is_automatic_run: self.plot_results()
            else:
                MessageDialog.message(self, "Data not displayable: bad content", "Error", "critical")

    def get_beam_to_plot(self, return_str=False):
        if return_str:
            return "beam"
        else:
            return self.input_data.beam


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMessageBox


    def get_beamline():
        from shadow4.beamline.s4_beamline import S4Beamline

        beamline = S4Beamline()

        # electron beam
        from shadow4.sources.s4_electron_beam import S4ElectronBeam
        electron_beam = S4ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
        electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=4.36821e-06, sigma_xp=3.63641e-06,
                                     sigma_yp=1.37498e-06)

        # magnetic structure
        from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian
        source = S4UndulatorGaussian(
            period_length=0.042,  # syned Undulator parameter (length in m)
            number_of_periods=38.571,  # syned Undulator parameter
            photon_energy=5000.0,  # Photon energy (in eV)
            delta_e=4.0,  # Photon energy width (in eV)
            ng_e=100,  # Photon energy scan number of points
            flag_emittance=1,  # when sampling rays: Use emittance (0=No, 1=Yes)
            flag_energy_spread=0,  # when sampling rays: Use e- energy spread (0=No, 1=Yes)
            harmonic_number=1,  # harmonic number
            flag_autoset_flux_central_cone=1,  # value to set the flux peak
            flux_central_cone=681709040139326.4,  # value to set the flux peak
        )

        # light source
        from shadow4.sources.undulator.s4_undulator_gaussian_light_source import S4UndulatorGaussianLightSource
        light_source = S4UndulatorGaussianLightSource(name='GaussianUndulator', electron_beam=electron_beam,
                                                      magnetic_structure=source, nrays=15000, seed=5676561)
        beam = light_source.get_beam()

        beamline.set_light_source(light_source)

        # optical element number XX
        from syned.beamline.shape import Rectangle
        boundary_shape = Rectangle(x_left=-0.001, x_right=0.001, y_bottom=-0.001, y_top=0.001)

        from shadow4.beamline.optical_elements.absorbers.s4_screen import S4Screen
        optical_element = S4Screen(name='Generic Beam Screen/Slit/Stopper/Attenuator', boundary_shape=boundary_shape,
                                   i_abs=0,  # 0=No, 1=prerefl file_abs, 2=xraylib, 3=dabax
                                   i_stop=0, thick=0, file_abs='<specify file name>', material='Au', density=19.3)

        from syned.beamline.element_coordinates import ElementCoordinates
        coordinates = ElementCoordinates(p=27.2, q=0, angle_radial=0, angle_azimuthal=0, angle_radial_out=3.141592654)
        from shadow4.beamline.optical_elements.absorbers.s4_screen import S4ScreenElement
        beamline_element = S4ScreenElement(optical_element=optical_element, coordinates=coordinates, input_beam=beam)

        beam, footprint = beamline_element.trace_beam()

        beamline.append_beamline_element(beamline_element)

        # optical element number XX
        boundary_shape = None

        from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror
        optical_element = S4PlaneMirror(name='Plane Mirror', boundary_shape=boundary_shape,
                                        f_reflec=1, f_refl=5, file_refl='<none>', refraction_index=0.99999 + 0.001j,
                                        coating_material='Ni', coating_density=8.902, coating_roughness=0)

        from syned.beamline.element_coordinates import ElementCoordinates
        coordinates = ElementCoordinates(p=2.7, q=0, angle_radial=1.563796327, angle_azimuthal=1.570796327,
                                         angle_radial_out=1.563796327)
        movements = None
        from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirrorElement
        beamline_element = S4PlaneMirrorElement(optical_element=optical_element, coordinates=coordinates,
                                                movements=movements, input_beam=beam)

        beam, mirr = beamline_element.trace_beam()

        beamline.append_beamline_element(beamline_element)

        # test plot
        if 0:
            from srxraylib.plot.gol import plot_scatter
            plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1),
                         title='(Intensity,Photon Energy)', plot_histograms=0)
            plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1),
                         title='(X,Z) in microns')
        return beam, footprint, beamline
        ###############################


    beam, footprint, beamline = get_beamline()

    app = QApplication(sys.argv)
    w = PlotXY()
    w.set_shadow_data(ShadowData(beam=beam, footprint=footprint, number_of_rays=0, beamline=beamline))
    w.show()
    app.exec()

