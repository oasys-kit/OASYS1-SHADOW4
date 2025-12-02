import sys
import numpy

from orangewidget import gui
from orangewidget.settings import Setting

O2 = True if sys.version_info.minor >= 10 else False
if O2:
    from orangewidget.widget import Input

    from AnyQt import QtGui
    from AnyQt.QtWidgets import QApplication

    from oasys2.widget import gui as oasysgui
    from oasys2.widget.util.widget_util import EmittingStream
    from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module
    from oasys2.widget.gui import ConfirmDialog, MessageDialog
else:
    from PyQt5 import QtGui, QtWidgets
    from PyQt5.QtWidgets import QApplication

    from oasys.widgets import gui as oasysgui
    from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence
from orangecontrib.shadow4.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D, plot_data2D, plot_data3D
from orangecontrib.shadow4.util.python_script import PythonScript

from srxraylib.util.h5_simple_writer import H5SimpleWriter

class OWCaustic(AutomaticElement):

    name = "Caustic Generator"
    description = "Shadow4: Caustic Generator"
    icon = "icons/caustic.png"
    maintainer = "M. Sanchez del Rio"
    maintainer_email = "srio@esrf.eu"
    priority = 5.5
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    if O2:
        class Inputs:
            shadow_data = Input("Shadow Data", ShadowData, default=True, auto_summary=False)
    else:
        inputs = [("Input Beam", ShadowData, "set_shadow_data")]

    want_main_area=1
    want_control_area = 1

    input_data = None

    npoints_x = Setting(1000) # in X and Z
    npoints_z = Setting(101)  # in X and Z
    npositions = Setting(300) # in Y

    y_min = Setting(-5.0)
    y_max = Setting(5.0)

    no_lost  = Setting(1)
    use_reflectivity = Setting(1)
    shadow_column = Setting(0)

    x_min = Setting(-0.2)
    x_max = Setting( 0.2)

    save_h5_file_flag = Setting(0)
    save_h5_file_name = Setting("caustic.h5")

    def __init__(self, show_automatic_box=True):
        super().__init__(show_automatic_box=show_automatic_box)

        gui.button(self.controlArea, self, "Calculate", callback=self.calculate, height=45)

        general_box = oasysgui.widgetBox(self.controlArea, "General Settings", orientation="vertical",)

        gui.comboBox(general_box, self, "no_lost", label="Rays",labelWidth=220,
                                     items=["All rays","Good only","Lost only"],
                                     sendSelectedValue=False, orientation="horizontal")


        gui.comboBox(general_box, self, "use_reflectivity", label="Include reflectivity",labelWidth=220,
                                     items=["No","Yes"],
                                     sendSelectedValue=False, orientation="horizontal")

        box_y = oasysgui.widgetBox(general_box, "Propagation along Y (col 2)", orientation="vertical", height=100)
        oasysgui.lineEdit(box_y, self, "npositions", "Y Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box_y, self, "y_min", "Y min"+ " [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_y, self, "y_max", "Y max"+ " [m]", labelWidth=260, valueType=float, orientation="horizontal")


        gui.comboBox(general_box, self, "shadow_column", label="Scan direction",labelWidth=220,
                                     items=["X (col 1)","Z (col 3)", "R (col 20)"],
                                     sendSelectedValue=False, orientation="horizontal")

        box_x = oasysgui.widgetBox(general_box, "Scan direction", orientation="vertical", height=100)
        oasysgui.lineEdit(box_x, self, "npoints_x", "Points", labelWidth=260, valueType=int,orientation="horizontal")
        oasysgui.lineEdit(box_x, self, "x_min", "min"+ " [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_x, self, "x_max", "max"+ " [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(self.controlArea, height=200)

        box_file = oasysgui.widgetBox(general_box, "File", orientation="vertical", height=100)
        gui.comboBox(box_file, self, "save_h5_file_flag", label="Save plots into h5 file", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal", callback=self.set_visible)

        self.box_file_1 = oasysgui.widgetBox(box_file, "", orientation="horizontal", height=25)
        oasysgui.lineEdit(self.box_file_1, self, "save_h5_file_name", "File Name", labelWidth=100,  valueType=str, orientation="horizontal")

        #
        #
        #
        tabs_setting = oasysgui.tabWidget(self.mainArea)

        tmp = oasysgui.createTabPage(tabs_setting, "Intensity vs y")
        self.image_box = gui.widgetBox(tmp, "", orientation="vertical")

        tmp = oasysgui.createTabPage(tabs_setting, "FWHM(y)")
        self.box_fwhm = gui.widgetBox(tmp, "", orientation="vertical")

        tmp = oasysgui.createTabPage(tabs_setting, "Center(y)")
        self.box_center = gui.widgetBox(tmp, "", orientation="vertical")

        tmp = oasysgui.createTabPage(tabs_setting, "I0(y)")
        self.box_I0 = gui.widgetBox(tmp, "", orientation="vertical")

        tab_out = oasysgui.createTabPage(tabs_setting, "Output")
        self.output_text = oasysgui.textArea()
        info_box = oasysgui.widgetBox(tab_out, "", orientation="horizontal")
        info_box.layout().addWidget(self.output_text)

        script_tab = oasysgui.createTabPage(tabs_setting, "Script")
        self.shadow4_script = PythonScript()
        self.shadow4_script.code_area.setFixedHeight(400)
        script_box = gui.widgetBox(script_tab, "Python script", orientation="horizontal")
        script_box.layout().addWidget(self.shadow4_script)

        self.set_visible()

    def set_visible(self):
        self.box_file_1.setVisible(self.save_h5_file_flag != 0)

    def writeStdOut(self, text="", initialize=False):
        cursor = self.output_text.textCursor()
        if initialize:
            self.output_text.setText(text)
        else:
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertText(text)

    if O2:
        @Inputs.shadow_data
        def set_shadow_data(self, shadow_data: ShadowData):
            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_empty_beam(shadow_data.beam):
                    self.input_data = shadow_data
                    if self.is_automatic_run: self.calculate()
                else:
                    MessageDialog.message(self, "Data not displayable: bad content", "Error", "critical")

    else:
        def set_shadow_data(self, shadow_data):
            if ShadowCongruence.check_empty_beam(shadow_data.beam):
                self.input_data = shadow_data
                if self.is_automatic_run: self.calculate()
            else:
                MessageDialog.message(self, "Data not displayable: bad content", "Error", "critical")

    def calculate(self):

        self.progressBarInit()

        # capture stout
        self.writeStdOut(initialize=True)
        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        if ShadowCongruence.check_empty_data(self.input_data):
            beam_to_analyze = self.input_data.beam
        else:
            beam_to_analyze = None

        if beam_to_analyze is None:
            print("No SHADOW Beam")
            self.progressBarFinished()
            return

        positions = numpy.linspace(self.y_min, self.y_max, self.npositions)

        out_x = numpy.zeros((self.npoints_x, self.npositions))
        fwhm = numpy.zeros(self.npositions)
        center = numpy.zeros(self.npositions)

        if self.shadow_column == 0:
            col = 1
        elif self.shadow_column == 1:
            col = 3
        elif self.shadow_column == 2:
            col = 20

        if self.use_reflectivity:
            ref = 23
        else:
            ref = 0

        self.set_script()

        self.progressBarSet(10)
        self.setStatusMessage("Retracing...")
        print(f"{'position index':<20} {'distance [m]':<20} {'peak center at [m]':<20} {'peak value I0':<20} {'fwhm [m]':<20}")
        print("-" * 20 * 6)

        for i in range(self.npositions):
            beami = beam_to_analyze.duplicate()
            beami.retrace(positions[i], resetY=True)
            tkt_x = beami.histo1(col, xrange=[self.x_min, self.x_max], nbins=self.npoints_x, nolost=self.no_lost, ref=ref)
            out_x[:, i] = tkt_x["histogram"]
            fwhm[i] = tkt_x["fwhm"]

            if ref == 23:
                center[i] = numpy.average(beami.get_column(col, nolost=self.no_lost),
                                          weights=beami.get_column(23, nolost=self.no_lost))
            else:
                center[i] = numpy.average(beami.get_column(col,nolost=self.no_lost))

            if numpy.mod(i, 10) == 0:
                self.progressBarSet(10 + 85 * i / self.npositions)
                I0 = out_x.T[i, self.npoints_x // 2]
                print(f"{i           :<30d} "
                      f"{positions[i]:<30.4g} "
                      f"{center[i]   :<30.4g} "
                      f"{I0          :<30.4g} "
                      f"{fwhm[i]     :<30.4g}")

        #
        # plots
        #
        print("\nResult arrays X,Y (shapes): ", out_x.shape, tkt_x["bin_center"].shape, positions.shape )
        x = tkt_x["bin_center"]
        y = positions

        if self.shadow_column == 0:
            col_title="X (col 1)"
        elif self.shadow_column == 1:
            col_title = "Z (col 3)"
        elif self.shadow_column == 2:
            col_title = "R (col 20)"

        plot_canvas = plot_data2D(
                             out_x.T, y, 1e6 * x,
                             title="",ytitle="%s [um] (%d pixels)"%(col_title,x.size),xtitle="Y [m] (%d pixels)"%(y.size),)
        self.image_box.layout().removeItem(self.image_box.layout().itemAt(0))
        self.image_box.layout().addWidget(plot_canvas)


        #FWHM
        fwhm[fwhm == 0] = 'nan'
        self.box_fwhm.layout().removeItem(self.box_fwhm.layout().itemAt(0))
        plot_widget_id = plot_data1D(y,1e6 * fwhm,title="FWHM",xtitle="y [m]", ytitle="FHWH [um]",symbol='.')
        self.box_fwhm.layout().addWidget(plot_widget_id)

        #I0
        nx, ny = out_x.shape
        I0 = out_x.T[:,nx//2]
        self.box_I0.layout().removeItem(self.box_I0.layout().itemAt(0))
        plot_widget_id = plot_data1D(y,I0,title="I at central profile",xtitle="y [m]", ytitle="I0",symbol='.')
        self.box_I0.layout().addWidget(plot_widget_id)

        #center
        self.box_center.layout().removeItem(self.box_center.layout().itemAt(0))
        plot_widget_id = plot_data1D(y, 1e6 * center,title="CENTER",xtitle="y [m]", ytitle="CENTER [um]",symbol='.',
                                     yrange=[1e6 * self.x_min, 1e6 * self.x_max])
        self.box_center.layout().addWidget(plot_widget_id)

        if self.save_h5_file_flag:

            h5w = H5SimpleWriter.initialize_file(self.save_h5_file_name, creator="h5_basic_writer.py")

            h5w.create_entry("caustic", nx_default="image")

            h5w.add_image(out_x.T, y, 1e6 * x,
                          entry_name="caustic", image_name="image",
                          title_y="%s [um] (%d pixels)"%(col_title,x.size),
                          title_x="Y [m] (%d pixels)"%(y.size))

            h5w.add_dataset(y, 1e6 * fwhm,
                            entry_name="caustic", dataset_name="fwhm",
                            title_x="Y [m]", title_y="FWHM [um]")

            h5w.add_dataset(y, 1e6 * center,
                            entry_name="caustic", dataset_name="center",
                            title_x="Y [m]", title_y="center [um]")

            h5w.add_dataset(y, I0,
                            entry_name="caustic", dataset_name="I0",
                            title_x="Y [m]", title_y="I at central profile")

        self.setStatusMessage("")
        self.progressBarFinished()

    def set_script(self):
        # script
        try:
            beamline = self.input_data.beamline.duplicate()

            script_bl = beamline.to_python_code()
            script_bl_indented = '\n'.join('    ' + line for line in script_bl.splitlines())

            script_bl = "def run_beamline():\n"
            script_bl += script_bl_indented
            script_bl += "\n    return beam"
            script_bl += "\n\n"

            script_loop = ""
            script_loop += "\ny_min, y_max, npositions = %g, %g, %d" % (self.y_min, self.y_max, self.npositions)
            script_loop += "\nx_min, x_max, npoints_x = %g, %g, %d" % (self.x_min, self.x_max, self.npoints_x)
            script_loop += "\nnolost = %d" % (self.no_lost)

            script_loop += "\n\npositions = numpy.linspace(y_min, y_max, npositions)"
            script_loop += "\nout_x = numpy.zeros((npoints_x, npositions))"
            script_loop += "\nfwhm = numpy.zeros(npositions)"
            script_loop += "\ncenter = numpy.zeros(npositions)"

            if self.shadow_column == 0:
                col = 1
            elif self.shadow_column == 1:
                col = 3
            elif self.shadow_column == 2:
                col = 20

            if self.use_reflectivity:
                ref = 23
            else:
                ref = 0

            if self.shadow_column == 0:
                col_title = "X (col 1)"
            elif self.shadow_column == 1:
                col_title = "Z (col 3)"
            elif self.shadow_column == 2:
                col_title = "R (col 20)"

            script_loop += "\ncol = %d" % col
            script_loop += "\nref = %d" % ref
            script_loop += '\ncol_title = "%s"' % col_title

            script_loop += "\n\nfor i in range(npositions):"
            script_loop += "\n    beami = beam_to_analyze.duplicate()"
            script_loop += "\n    beami.retrace(positions[i], resetY=True)"
            script_loop += "\n    tkt_x = beami.histo1(col, xrange=[x_min, x_max], nbins=npoints_x, nolost=nolost, ref=ref)"
            script_loop += "\n    out_x[:, i] = tkt_x['histogram']"
            script_loop += "\n    fwhm[i] = tkt_x['fwhm']"
            script_loop += "\n    if ref == 23:"
            script_loop += "\n        center[i] = numpy.average(beami.get_column(col, nolost=nolost), weights=beami.get_column(23, nolost=nolost))"
            script_loop += "\n    else:"
            script_loop += "\n        center[i] = numpy.average(beami.get_column(col, nolost=nolost))"

            script_loop += "\n#"
            script_loop += "\n# plots"
            script_loop += "\n#"
            script_loop += "\nprint('Result arrays X,Y (shapes): ', out_x.shape, tkt_x['bin_center'].shape, positions.shape)"
            script_loop += "\nx = tkt_x['bin_center']"
            script_loop += "\ny = positions"

            script_loop += '\n\n# 2D'
            script_loop += '\nplot_image(out_x.T, y, 1e6 * x,'
            script_loop += '\n           title="", ytitle="%s [um] (%d pixels)" % (col_title, x.size),'
            script_loop += '\n           xtitle="Y [m] (%d pixels)" % (y.size), aspect="auto" )'
            script_loop += '\n# FWHM'
            script_loop += '\nfwhm[fwhm == 0] = "nan"'
            script_loop += '\nplot(y, 1e6 * fwhm, title="FWHM",'
            script_loop += '\n     xtitle="y [m]", ytitle="FHWH [um]", marker=".")'
            script_loop += '\n# I0'
            script_loop += '\nnx, ny = out_x.shape'
            script_loop += '\nI0 = out_x.T[:, nx // 2]'
            script_loop += '\nplot(y, I0, title="I at central profile", xtitle="y [m]", ytitle="I0", marker=".")'
            script_loop += '\n# center'
            script_loop += '\nplot(y, 1e6 * center, title="CENTER",'
            script_loop += '\n     xtitle="y [m]", ytitle="CENTER [um]", marker=".", yrange=[1e6 * x_min, 1e6 * x_max])'

            script_h5 = ""
            if self.save_h5_file_flag:
                script_h5 += "\n# write h5 file"
                script_h5 += "\nfrom srxraylib.util.h5_simple_writer import H5SimpleWriter"
                script_h5 += '\nh5w = H5SimpleWriter.initialize_file("%s", creator="h5_basic_writer.py")' % self.save_h5_file_name
                script_h5 += '\nh5w.create_entry("caustic", nx_default="image")'
                script_h5 += '\nh5w.add_image(out_x.T, y, 1e6 * x, entry_name="caustic", image_name="image",'
                script_h5 += '\n              title_y="%s [um] (%d pixels)" % (col_title, x.size), title_x="Y [m] (%d pixels)" % (y.size), )'
                script_h5 += '\nh5w.add_dataset(y, 1e6 * fwhm, entry_name="caustic", dataset_name="fwhm",'
                script_h5 += '\n                title_x="Y [m]", title_y="FWHM [um]")'
                script_h5 += '\nh5w.add_dataset(y, 1e6 * center, entry_name="caustic", dataset_name="center",'
                script_h5 += '\n                title_x="Y [m]", title_y="center [um]")'
                script_h5 += '\nh5w.add_dataset(y, I0, entry_name="caustic", dataset_name="I0",'
                script_h5 += '\n                title_x="Y [m]", title_y="I at central profile")'

            dict = {
                "script_bl" : script_bl,
                "script_loop": script_loop,
                "script_h5": script_h5,
            }

            script_template = """

{script_bl}

#
# main 
#
import numpy
from srxraylib.plot.gol import plot, plot_image, plot_show

beam_to_analyze = run_beamline()

{script_loop}

{script_h5}

"""

            final_script = script_template.format_map(dict)
        except:
            final_script += "\n\n\n# cannot retrieve beamline data from shadow_data"

        self.shadow4_script.set_code(final_script)

if O2: add_widget_parameters_to_module(__name__)

if __name__ == "__main__":
    def get_shadow_data():
        from shadow4.sources.s4_light_source_from_file import S4LightSourceFromFile
        from shadow4.beamline.s4_beamline import S4Beamline
        light_source = S4LightSourceFromFile(name='Shadow4 File Reader', file_name='/home/srio/Oasys/lens01.h5',
                                             simulation_name='run001', beam_name='begin')
        return ShadowData(beam=light_source.get_beam(),
                                 number_of_rays=light_source.get_beam().N,
                                 beamline=S4Beamline(light_source=light_source))

    a = QApplication(sys.argv)
    ow = OWCaustic()
    ow.show()
    ow.npoints_x = 300
    ow.npoints_z = 300
    ow.npositions = 200
    ow.y_min = -50
    ow.y_max = 50
    ow.shadow_column = 1
    ow.x_min = -0.005
    ow.x_max = 0.005
    ow.save_h5_file_flag = 1
    ow.input_data = get_shadow_data()
    if O2:
        a.exec()
    else:
        a.exec_()
    ow.saveSettings()
