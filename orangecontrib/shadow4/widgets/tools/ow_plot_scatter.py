import sys, os
import time
import numpy

from PyQt5.QtGui import QTextCursor
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox

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

from silx.gui.plot.ScatterView import ScatterView
from silx.gui.colors import Colormap

from oasys.util.oasys_util import EmittingStream


try:
    import OpenGL
    has_opengl = True
except:
    has_opengl = False

class PlotScatter(AutomaticElement):
    name = "Plot Scatter"
    description = "Display Data Tools: Plot XY"
    icon = "icons/plot_scatter.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 1.3
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Shadow Data", ShadowData, "set_shadow_data"),
              ("Shadow Data (color)", ShadowData, "set_shadow_data_for_color")]

    IMAGE_WIDTH = 878
    IMAGE_HEIGHT = 635

    want_main_area = 1

    plot_canvas = None

    image_plane = Setting(0)
    image_plane_new_position = Setting(10.0)

    x_column_index = Setting(0)
    x_range = Setting(0)
    x_range_min = Setting(0.0)
    x_range_max = Setting(0.0)

    y_column_index = Setting(2)
    y_range = Setting(0)
    y_range_min = Setting(0.0)
    y_range_max = Setting(0.0)

    weight_transparency = Setting(0)

    color_source = Setting(0) # 0 = same beam , 1 = specific beam
    color_column = Setting(23)
    weight_transparency = Setting(0)

    rays = Setting(1)
    title = Setting("")

    conversion_active = Setting(1)

    if has_opengl:
        backend = 1
    else:
        backend = 0

    input_data = None
    input_data_color = None

    def __init__(self):
        super().__init__()

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        gui.button(button_box, self, "Refresh", callback=self.plot_results, height=45)

        gui.separator(self.controlArea, 10)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH - 5)

        # graph tab
        tab_set = oasysgui.createTabPage(self.tabs_setting, "Plot Settings")

        ################
        screen_box = oasysgui.widgetBox(tab_set, "Screen Position Settings", addSpace=True, orientation="vertical",)

        self.image_plane_combo = gui.comboBox(screen_box, self, "image_plane", label="Position of the Image",
                                              items=["On Image Plane", "Retraced"], labelWidth=260,
                                              callback=self.set_visibility, sendSelectedValue=False,
                                              orientation="horizontal")

        self.image_plane_box = oasysgui.widgetBox(screen_box, "", addSpace=False, orientation="vertical",) # height=50)

        oasysgui.lineEdit(self.image_plane_box, self, "image_plane_new_position", "New (relative) position [m]",
                          labelWidth=220, valueType=float, orientation="horizontal")

        ################
        general_box = oasysgui.widgetBox(tab_set, "Variables Settings", addSpace=True, orientation="vertical",)


        #######
        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="H Column", labelWidth=70,
                                     items=S4Beam.column_names_with_column_number(),
                                     sendSelectedValue=False, orientation="horizontal",
                                     callback=self.set_x_column_index)

        gui.comboBox(general_box, self, "x_range", label="H Range", labelWidth=250,
                     items=["<Default>", "Set.."],
                     callback=self.set_visibility, sendSelectedValue=False, orientation="horizontal")

        self.x_range_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical",) # height=120)

        self.le_x_range_min = oasysgui.lineEdit(self.x_range_box, self, "x_range_min", "H min", labelWidth=220,
                                                valueType=float, orientation="horizontal")
        self.le_x_range_max = oasysgui.lineEdit(self.x_range_box, self, "x_range_max", "H max", labelWidth=220,
                                                valueType=float, orientation="horizontal")

        #######
        self.y_column = gui.comboBox(general_box, self, "y_column_index", label="V Column", labelWidth=70,
                                     items=S4Beam.column_names_with_column_number(),
                                     sendSelectedValue=False, orientation="horizontal",
                                     callback=self.set_y_column_index)

        gui.comboBox(general_box, self, "y_range", label="V Range", labelWidth=250,
                     items=["<Default>", "Set.."],
                     callback=self.set_visibility, sendSelectedValue=False, orientation="horizontal")

        self.y_range_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical",) # height=100)

        self.le_y_range_min = oasysgui.lineEdit(self.y_range_box, self, "y_range_min", "V min", labelWidth=220,
                                                valueType=float, orientation="horizontal")
        self.le_y_range_max = oasysgui.lineEdit(self.y_range_box, self, "y_range_max", "V max", labelWidth=220,
                                                valueType=float, orientation="horizontal")

        #######
        gui.comboBox(general_box, self, "color_source", label="Color source", labelWidth=100,
                     items=["The same beam", "Specific beam"],sendSelectedValue=False, orientation="horizontal")

        ######
        col_names = S4Beam.column_names_with_column_number()
        col_names.insert(0, "0: No Weight")
        self.weight_column = gui.comboBox(general_box, self, "color_column", label="Color", labelWidth=70,
                                          items=col_names,
                                          sendSelectedValue=False, orientation="horizontal")


        gui.comboBox(general_box, self, "weight_transparency", label="Transparency (Weight=col23)", labelWidth=250,
                                         items=["No","Yes"],
                                         sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "rays", label="Rays", labelWidth=250,
                     items=["All rays",
                            "Good Only",
                            "Lost Only"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "conversion_active", label="Is U.M. conversion active", labelWidth=250,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_is_conversion_active)

        gui.comboBox(general_box, self, "backend", label="render backend", labelWidth=250,
                                         items=["matplotlib", "gl"],
                                         sendSelectedValue=False, orientation="horizontal")

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

        self.set_visibility()

    def set_shadow_data(self, shadow_data: ShadowData):
        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_empty_beam(shadow_data.beam):
                self.input_data = shadow_data
                if self.is_automatic_run: self.plot_results()
            else:
                MessageDialog.message(self, "Data not displayable: bad content", "Error", "critical")

    def set_shadow_data_for_color(self, shadow_data: ShadowData):
        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_empty_beam(shadow_data.beam):
                self.input_data_color = shadow_data
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

    def set_visibility(self):
        self.x_range_box.setVisible(False)
        self.y_range_box.setVisible(False)
        self.image_plane_box.setVisible(False)

        if self.x_range == 1:
            self.x_range_box.setVisible(True)

        if self.y_range == 1:
            self.y_range_box.setVisible(True)

        self.__change_labels(dir='x')
        self.__change_labels(dir='y')

        if self.image_plane == 1:
            self.image_plane_box.setVisible(True)

    def set_is_conversion_active(self):
        self.__change_labels(dir='b')

    def set_script(self, x_range, y_range):

        # script
        try:
            beamline = self.input_data.beamline.duplicate()

            script = beamline.to_python_code(partial_code=1) # onlu source
            indented_script = '\n'.join('    ' + line for line in script.splitlines())
            final_script = "def run_source():\n"
            final_script += indented_script
            final_script += "\n    return beam"
            final_script += "\n\n"

            script = beamline.to_python_code(partial_code=2) # only beamline
            indented_script = '\n'.join('    ' + line for line in script.splitlines())
            final_script += "def run_beamline(beam):\n"
            final_script += indented_script
            final_script += "\n    return beam, footprint"
            final_script += "\n\n"

            # TODO: add script for color
            if self.color_source == 1:
                beamline_color = self.input_data_color.beamline.duplicate()
                script = beamline_color.to_python_code(partial_code=2) # only beamline
                indented_script = '\n'.join('    ' + line for line in script.splitlines())
                final_script += "def run_beamline_for_color(beam):\n"
                final_script += indented_script
                final_script += "\n    return beam"
                final_script += "\n\n"

            if self.image_plane > 0:
                retrace = "beam.retrace(%f)" % self.image_plane_new_position
            else:
                retrace = ""

            if self.color_source == 0:
                color_same_beam = "(the same beam)"
                color_code = "beam_color = beam"
            else:
                color_same_beam = "(from different beam)"
                color_code = "beam_color = run_beamline_for_color(beam_source)"

            dict = {"var_x": 1 + self.x_column_index,
                    "var_y": 1 + self.y_column_index,
                    "x_range_min": x_range[0],
                    "x_range_max": x_range[1],
                    "y_range_min": y_range[0],
                    "y_range_max": y_range[1],
                    "nolost": self.rays,
                    "color_column": self.color_column,
                    "color_code": color_code,
                    "weight_transparency": self.weight_transparency,
                    "retrace": retrace,
                    "color_code": color_code,
                    "color_same_beam": color_same_beam,
                    }

            script_template = """#
#
# main
#
import matplotlib.pyplot as plt

# WARNING: No incremental or cumulated result allowed!!"
beam_source = run_source()
beam, footprint = run_beamline(beam_source)
{retrace}

{color_code}

weight_transparency = {weight_transparency} # flag to use transparency

x = beam.get_column({var_x}, nolost={nolost}) # H 
y = beam.get_column({var_y}, nolost={nolost}) # V
t = beam.get_column(23, nolost={nolost}) # for transparency
f = beam.get_column(10, nolost={nolost}) # lost ray flag
i = beam.get_column(12, nolost={nolost})  # index ray flag

colors = beam_color.get_column({color_column}, nolost=0)
colors = colors[i.astype(int) - 1]

if weight_transparency == 0: t = t * 0 + 1
alpha_vals = t / t.max()  # normalize to [0, 1]

# Create scatter plot (no border, filled with color)
sc = plt.scatter(
    x, y,
    c=colors,
    marker='o',
    cmap='viridis',
    edgecolors='none'  # removes circle border
)

# Apply individual alpha values
facecolors = sc.get_facecolors()
for i in range(len(facecolors)):
    facecolors[i][-1] = alpha_vals[i]
sc.set_facecolors(facecolors)

# Labels
plt.xlabel('column {var_x}')
plt.ylabel('column {var_y}')

# Colorbar
plt.colorbar(label='column {color_column} {color_same_beam}')

# limitx
plt.xlim({x_range_min}, {x_range_max})
plt.ylim({y_range_min}, {y_range_max})

plt.title('Scatter Plot, transparency=%d' % (weight_transparency))
plt.grid(True)
plt.show()

"""

            final_script += script_template.format_map(dict)

            self.shadow4_script.set_code(final_script)
        except:
            final_script += "\n\n\n# cannot retrieve beamline data from shadow_data"

        self.shadow4_script.set_code(final_script)


    #######################

    def plot_results(self):

        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if ShadowCongruence.check_empty_data(self.input_data):
                ShadowPlot.set_conversion_active(self.is_conversion_active())

                x, y, c, auto_x_title, auto_y_title, xum, yum = self.get_titles()

                print(">>>>", x, y, c, auto_x_title, auto_y_title, xum, yum)

                self.plot_scatter(x, y, c, title=self.title, xtitle=auto_x_title, ytitle=auto_y_title, xum=xum, yum=yum)

                plotted = True

            time.sleep(0.1)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted


            if True: # self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                                       QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

            return False

    def plot_scatter(self, var_x, var_y, var_color, title, xtitle, ytitle, xum, yum):
        beam_to_plot = self.input_data.beam

        if self.image_plane == 1:
            new_shadow_beam = beam_to_plot.duplicate()
            self.retrace_beam(new_shadow_beam, self.image_plane_new_position)
            beam_to_plot = new_shadow_beam

        xrange, yrange = self.get_ranges(beam_to_plot, var_x, var_y)

        self.set_script(x_range=xrange, y_range=yrange)

        self.replace_fig(beam_to_plot, var_x, var_y, var_color,
                         title, xtitle, ytitle,
                         xrange=xrange, yrange=yrange,
                         nolost=self.rays, xum=xum, yum=yum)



    def replace_fig(self, beam, var_x, var_y, var_color, title, xtitle, ytitle,
                    xrange=[0,0], yrange=[0,0], nolost=0, xum="", yum=""):

        if self.backend == 0:
            use_backend = 'matplotlib'
        elif self.backend == 1:
            if not has_opengl:
                QMessageBox.information(self, "Plot Scatter Information",
                        "It seems that PyOpenGL is not installed in your system." +
                        "\nInstall it to get much faster scatter plots, like:" +
                        "\n" + os.path.dirname(sys.executable) + os.sep + "pip install PyOpenGL",
                        QMessageBox.Ok)
                use_backend = 'matplotlib'
                self.backend = 0
            else:
                use_backend = 'gl'

        if self.plot_canvas is None:
            self.plot_canvas = ScatterView(backend=use_backend)
        else:
            self.image_box.layout().removeWidget(self.plot_canvas)
            self.plot_canvas = None
            self.plot_canvas = ScatterView(backend=use_backend)

        if self.color_column != 0:
            if self.color_source == 0:
                color_array = beam.get_column(var_color, nolost=nolost)
            else:
                if self.input_data_color is None:
                    raise Exception("Undefined specific beam for color")

                color_array = self.input_data_color.beam.get_column(var_color, nolost=False)
                if nolost == 0:
                    pass
                elif nolost == 1:
                    color_good_flags = beam.get_column(10, nolost=False)
                    color_array = color_array[numpy.where(color_good_flags >=0 )]
                elif nolost == 2:
                    color_good_flags = beam.get_column(10, nolost=False)
                    color_array = color_array[numpy.where(color_good_flags < 0 )]
        else:
            color_array = beam.get_column(1, nolost=nolost) * 0.0

        factor1 = ShadowPlot.get_factor(var_x)
        factor2 = ShadowPlot.get_factor(var_y)
        factorC = ShadowPlot.get_factor(var_color)


        if self.weight_transparency == 1:
            self.plot_canvas.setData(
                beam.get_column(var_x, nolost=nolost)*factor1,
                beam.get_column(var_y, nolost=nolost)*factor2,
                color_array*factorC,
                alpha = beam.get_column(23, nolost=nolost) )
        else:
            self.plot_canvas.setData(
                beam.get_column(var_x, nolost=nolost)*factor1,
                beam.get_column(var_y, nolost=nolost)*factor2,
                color_array*factorC,
                )

        self.plot_canvas.resetZoom()
        self.plot_canvas.setGraphTitle(title)
        self.plot_canvas.setColormap(Colormap('viridis'))

        ax = self.plot_canvas.getPlotWidget().getXAxis()
        if self.x_range == 1:
            ax.setLimits(self.x_range_min,self.x_range_max)
        ax.setLabel(xtitle)

        ay = self.plot_canvas.getPlotWidget().getYAxis()
        if self.y_range == 1:
            ay.setLimits(self.y_range_min,self.y_range_max)
        ay.setLabel(ytitle)

        self.image_box.layout().addWidget(self.plot_canvas)

    def set_x_column_index(self):
        self.__change_labels(dir='x')

    def set_y_column_index(self):
        self.__change_labels(dir='y')

    def __change_labels(self, dir='b'):
        def change_label(line_edit, index):
            label = line_edit.parent().layout().itemAt(0).widget()
            label_text = label.text()
            if label_text[-1] == "]":
                label_text = label_text.split(sep="[")[0]
            else:
                label_text += " "
            if index in [0, 1, 2] and self.is_conversion_active():
                label_text += "[\u03BCm]"
            elif index in [3, 4, 5] and self.is_conversion_active():
                label_text += "[\u03BCrad]"
            else:
                label_text += S4Beam.column_units()[index]
            label.setText(label_text)

        if self.x_range == 1 and dir in ['x', 'b']:
            change_label(self.le_x_range_min, self.x_column_index)
            change_label(self.le_x_range_max, self.x_column_index)
        if self.y_range == 1 and dir in ['y', 'b']:
            change_label(self.le_y_range_min, self.y_column_index)
            change_label(self.le_y_range_max, self.y_column_index)

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

        return x_range, y_range

    def get_titles(self):
        xum = auto_x_title = self.x_column.currentText()
        yum = auto_y_title = self.y_column.currentText()

        self.title = S4Beam.column_short_names()[self.x_column_index] + "," + S4Beam.column_short_names()[
            self.y_column_index]

        def get_strings(um, auto_title, col, index):
            if col in [1, 2, 3] and self.is_conversion_active():
                um += " [\u03BCm]"
                auto_title += " [\u03BCm]" # " [\mu m]"
            elif col in [4, 5, 6] and self.is_conversion_active():
                um += " [\u03BCrad]"
                auto_title += " [\u03BCrad]" # " [\mu rad]"
            else:
                um += " " + S4Beam.column_units()[index]
                auto_title += " " + S4Beam.column_units()[index]

            return um, auto_title

        x = self.x_column_index + 1
        y = self.y_column_index + 1
        c = self.color_column
        xum, auto_x_title = get_strings(xum, auto_x_title, x, self.x_column_index)
        yum, auto_y_title = get_strings(yum, auto_y_title, y, self.y_column_index)

        return x, y, c, auto_x_title, auto_y_title, xum, yum

    def is_conversion_active(self):
        return self.conversion_active == 1


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
    w = PlotScatter()
    w.set_shadow_data(ShadowData(beam=beam, footprint=footprint, number_of_rays=0, beamline=beamline))
    w.set_shadow_data_for_color(ShadowData(beam=beam, footprint=footprint, number_of_rays=0, beamline=beamline))
    w.show()
    app.exec()

