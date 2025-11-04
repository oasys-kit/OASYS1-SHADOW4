import sys
O2 = True if sys.version_info.minor >= 10 else False

from orangewidget import gui
from orangewidget.settings import Setting

if O2:
    from orangewidget.widget import Output

    from oasys2.widget import gui as oasysgui
    from oasys2.widget.widget import OWAction
    from oasys2.widget.util import congruence
    from oasys2.widget.util.widget_util import EmittingStream
    from oasys2.widget.gui import Styles
    from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module
    from oasys2.widget.util.widget_objects import TriggerIn

    WidgetDecorator = object # TODO: remove? For O1-compatibility

else:
    from PyQt5.QtGui import QPalette, QColor, QFont

    from syned.widget.widget_decorator import WidgetDecorator


    from orangewidget import widget

    from oasys.widgets import gui as oasysgui
    from oasys.widgets import congruence
    from oasys.util.oasys_util import EmittingStream

    from oasys.util.oasys_util import TriggerIn

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement

from shadow4.beamline.s4_beamline import S4Beamline
from shadow4.tools.logger import set_verbose
from shadow4.sources.s4_light_source_from_file import S4LightSourceFromFile

from orangecontrib.shadow4.util.shadow4_util import TriggerToolsDecorator

class BeamFileReader(GenericElement, TriggerToolsDecorator, WidgetDecorator):
    name = "Shadow4 File Reader"
    description = "Tools: Shadow File Reader"
    icon = "icons/beam_file_reader.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 6
    category = "Tools"
    keywords = ["data", "file", "load", "read"]

    want_main_area = 1

    file_name = Setting("")
    simulation_name = Setting("run001")
    beam_name = Setting("begin")

    if O2:
        class Outputs:
            shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)
            trigger = TriggerToolsDecorator.get_trigger_output()
    else:
        inputs = []
        WidgetDecorator.append_syned_input_data(inputs)

        outputs = [{"name":"Shadow Data",
                    "type":ShadowData,
                    "doc":"",}]

        TriggerToolsDecorator.append_trigger_input_for_sources(inputs)
        TriggerToolsDecorator.append_trigger_output(outputs)


    def __init__(self):
        super().__init__(show_automatic_box=False, has_footprint=False)

        if O2:
            self.runaction = OWAction("Read Shadow4 File", self)
        else:
            self.runaction = widget.OWAction("Read Shadow4 File", self)
        self.runaction.triggered.connect(self.read_file)
        self.addAction(self.runaction)


        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Read Shadow4 File", callback=self.read_file)
        if O2:
            button.setStyleSheet(Styles.button_blue)
        else:
            font = QFont(button.font())
            font.setBold(True)
            button.setFont(font)
            palette = QPalette(button.palette()) # make a copy of the palette
            palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
            button.setPalette(palette) # assign new palette
            button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        if O2:
            button.setStyleSheet(Styles.button_red)
        else:
            font = QFont(button.font())
            font.setItalic(True)
            button.setFont(font)
            palette = QPalette(button.palette()) # make a copy of the palette
            palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
            button.setPalette(palette) # assign new palette
            button.setFixedHeight(45)
            button.setFixedWidth(150)

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT + 60)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH - 5)

        tab_basic = oasysgui.createTabPage(tabs_setting, "General")

        left_box_1 = oasysgui.widgetBox(tab_basic, "Shadow4 File Selection", addSpace=True, orientation="vertical")

        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal")

        self.le_file_name = oasysgui.lineEdit(figure_box, self, "file_name", "Shadow4 h5 File Name",
                                                    labelWidth=170, valueType=str, orientation="horizontal")

        gui.button(figure_box, self, "...", callback=self.select_file)

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def select_file(self):
        self.le_file_name.setText(oasysgui.selectFileFromDialog(self, self.file_name, "Open Shadow4 File", file_extension_filter="hdf5 Files (*.h5 *.hdf5 *.hdf)"))

    def read_file(self, scanning_data: ShadowData.ScanningData = None):
        self.setStatusMessage("")

        try:
            set_verbose()
            self.shadow_output.setText("")
            sys.stdout = EmittingStream(textWritten=self._write_stdout)

            self._set_plot_quality()

            self.progressBarInit()

            light_source = self.get_lightsource()

            # script
            script = light_source.to_python_code()
            script += "\n\n# test plot\nfrom srxraylib.plot.gol import plot_scatter"
            script += "\nrays = beam.get_rays()"
            script += "\nplot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 2], title='(X,Z) in microns')"
            self.shadow4_script.set_code(script)


            print(light_source.info())

            print(light_source.get_info())

            self.progressBarSet(5)

            # run shadow4
            output_beam = light_source.get_beam()

            # beam plots
            self._plot_results(output_beam, None, progressBarValue=80)
            self.progressBarFinished()

            # send beam and trigger
            output_data = ShadowData(beam=output_beam,
                                     number_of_rays=output_beam.N,
                                     beamline=S4Beamline(light_source=light_source))


            if O2:
                output_data.scanning_data = scanning_data
                self.Outputs.shadow_data.send(output_data)
                self.Outputs.trigger.send(TriggerIn(new_object=True))
            else:
                self.send("Shadow Data", output_data)
                self.send("Trigger", TriggerIn(new_object=True))
        except Exception as exception:
            try:    self._initialize_tabs()
            except: pass
            self.prompt_exception(exception)

    def get_lightsource(self):
        return S4LightSourceFromFile(
            name=self.name,
            file_name=self.file_name,
            simulation_name=self.simulation_name,
            beam_name=self.beam_name)

if O2: add_widget_parameters_to_module(__name__)

if __name__ == "__main__":
    if O2:
        from AnyQt.QtWidgets import QApplication
    else:
        from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = BeamFileReader()
    ow.file_name = "/nobackup/gurb1/srio/Oasys/tmp4.h5"
    ow.show()
    a.exec_()
    ow.saveSettings()