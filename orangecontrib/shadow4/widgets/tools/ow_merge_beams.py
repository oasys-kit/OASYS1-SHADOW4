import sys, numpy
O2 = True if sys.version_info.minor >= 10 else False

from orangewidget.settings import Setting

if O2:
    from AnyQt.QtWidgets import QMessageBox

    from orangewidget import gui

    from orangewidget.widget import Input, Output

    from oasys2.widget.gui import Styles
    from oasys2.widget import gui as oasysgui
    from oasys2.widget.util import congruence
    from oasys2.widget.widget import OWWidget, OWAction
    from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module
    from oasys2.widget.util.widget_util import EmittingStream
else:
    from PyQt5.QtGui import QPalette, QColor, QFont
    from PyQt5.QtWidgets import QMessageBox

    from oasys.widgets import gui as oasysgui, congruence
    from oasys.widgets.widget import OWWidget
    from oasys.util.oasys_util import EmittingStream

    from orangewidget import widget
    from orangewidget import gui



from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence
from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
from orangecontrib.shadow4.util.shadow4_util import TriggerToolsDecorator

from shadow4.tools.logger import set_verbose
from shadow4.sources.s4_light_source_from_beamlines import S4LightSourceFromBeamlines
from shadow4.beamline.s4_beamline import S4Beamline

class MergeBeams(GenericElement, TriggerToolsDecorator):
    name = "Merge Shadow4 Beam"
    description = "Tools: Merge Shadow4 Beam"
    icon = "icons/merge.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 8.1
    category = "Tools"
    keywords = ["data", "file", "load", "read"]

    want_main_area = 1
    want_control_area = 1

    if O2:
        class Inputs:
            shadow_data_1 = Input("Input Shadow Data # 1", ShadowData, default=True, auto_summary=False)
            shadow_data_2 = Input("Input Shadow Data # 2", ShadowData, default=True, auto_summary=False)
            shadow_data_3 = Input("Input Shadow Data # 3", ShadowData, default=True, auto_summary=False)
            shadow_data_4 = Input("Input Shadow Data # 4", ShadowData, default=True, auto_summary=False)
            shadow_data_5 = Input("Input Shadow Data # 5", ShadowData, default=True, auto_summary=False)
            shadow_data_6 = Input("Input Shadow Data # 6", ShadowData, default=True, auto_summary=False)
            shadow_data_7 = Input("Input Shadow Data # 7", ShadowData, default=True, auto_summary=False)
            shadow_data_8 = Input("Input Shadow Data # 8", ShadowData, default=True, auto_summary=False)
            shadow_data_9 = Input("Input Shadow Data # 9", ShadowData, default=True, auto_summary=False)
            shadow_data_10 = Input("Input Shadow Data # 10", ShadowData, default=True, auto_summary=False)

        class Outputs:
            shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)
    else:
        inputs = [("Input Beam # 1", ShadowData,  "set_shadow_data1"),
                  ("Input Beam # 2", ShadowData,  "set_shadow_data2"),
                  ("Input Beam # 3", ShadowData,  "set_shadow_data3"),
                  ("Input Beam # 4", ShadowData,  "set_shadow_data4"),
                  ("Input Beam # 5", ShadowData,  "set_shadow_data5"),
                  ("Input Beam # 6", ShadowData,  "set_shadow_data6"),
                  ("Input Beam # 7", ShadowData,  "set_shadow_data7"),
                  ("Input Beam # 8", ShadowData,  "set_shadow_data8"),
                  ("Input Beam # 9", ShadowData,  "set_shadow_data9"),
                  ("Input Beam # 10", ShadowData, "set_shadow_data10"), ]

        outputs = [{"name": "Beam",
                    "type": ShadowData,
                    "doc": "Shadow Data",
                    "id": "beam"}]

    want_main_area = 1

    input_data_1 = None
    input_data_2 = None
    input_data_3 = None
    input_data_4 = None
    input_data_5 = None
    input_data_6 = None
    input_data_7 = None
    input_data_8 = None
    input_data_9 = None
    input_data_10 = None

    use_weights = Setting(0)

    weight_input_data_1 = Setting(0.0)
    weight_input_data_2 = Setting(0.0)
    weight_input_data_3 = Setting(0.0)
    weight_input_data_4 = Setting(0.0)
    weight_input_data_5 = Setting(0.0)
    weight_input_data_6 = Setting(0.0)
    weight_input_data_7 = Setting(0.0)
    weight_input_data_8 = Setting(0.0)
    weight_input_data_9 = Setting(0.0)
    weight_input_data_10 = Setting(0.0)

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box, has_footprint=False)

        if O2:
            self.runaction = OWAction("Merge Shadow4 Data", self)
            self.runaction.triggered.connect(self.merge_data)
        else:
            self.runaction = widget.OWAction("Merge Shadow4 Data", self)
        self.addAction(self.runaction)

        gen_box = gui.widgetBox(self.controlArea, "Merge Shadow4 Data", orientation="vertical")
        gui.separator(gen_box)

        button_box = oasysgui.widgetBox(gen_box, "", orientation="horizontal")
        button = gui.button(button_box, self, "Merge Data and Send", callback=self.merge_data)
        if O2: button.setStyleSheet(Styles.button_blue)

        weight_box = oasysgui.widgetBox(gen_box, "Relative Weights", orientation="vertical")

        gui.comboBox(weight_box, self, "use_weights", label="Use Relative Weights?",
                     labelWidth=350, items=["No", "Yes"], callback=self.set_UseWeights,
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(weight_box, height=10)

        self.le_weight_input_data_1 = oasysgui.lineEdit(weight_box, self, "weight_input_data_1", "Input Beam 1 weight",
                                                        labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_2 = oasysgui.lineEdit(weight_box, self, "weight_input_data_2", "Input Beam 2 weight",
                                                        labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_3 = oasysgui.lineEdit(weight_box, self, "weight_input_data_3", "Input Beam 3 weight",
                                                        labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_4 = oasysgui.lineEdit(weight_box, self, "weight_input_data_4", "Input Beam 4 weight",
                                                        labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_5 = oasysgui.lineEdit(weight_box, self, "weight_input_data_5", "Input Beam 5 weight",
                                                        labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_6 = oasysgui.lineEdit(weight_box, self, "weight_input_data_6", "Input Beam 6 weight",
                                                        labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_7 = oasysgui.lineEdit(weight_box, self, "weight_input_data_7", "Input Beam 7 weight",
                                                        labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_8 = oasysgui.lineEdit(weight_box, self, "weight_input_data_8", "Input Beam 8 weight",
                                                        labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_9 = oasysgui.lineEdit(weight_box, self, "weight_input_data_9", "Input Beam 9 weight",
                                                        labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_10 = oasysgui.lineEdit(weight_box, self, "weight_input_data_10",
                                                         "Input Beam 10 weight",
                                                         labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_1.setEnabled(False)
        self.le_weight_input_data_2.setEnabled(False)
        self.le_weight_input_data_3.setEnabled(False)
        self.le_weight_input_data_4.setEnabled(False)
        self.le_weight_input_data_5.setEnabled(False)
        self.le_weight_input_data_6.setEnabled(False)
        self.le_weight_input_data_7.setEnabled(False)
        self.le_weight_input_data_8.setEnabled(False)
        self.le_weight_input_data_9.setEnabled(False)
        self.le_weight_input_data_10.setEnabled(False)

    if O2:
        @Inputs.shadow_data_1
        def set_shadow_data1(self, shadow_data: ShadowData):
            self.le_weight_input_data_1.setEnabled(False)
            self.input_data_1 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_1 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_1.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #1 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        @Inputs.shadow_data_2
        def set_shadow_data2(self, shadow_data: ShadowData):
            self.le_weight_input_data_2.setEnabled(False)
            self.input_data_2 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_2 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_2.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #2 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        @Inputs.shadow_data_3
        def set_shadow_data3(self, shadow_data: ShadowData):
            self.le_weight_input_data_3.setEnabled(False)
            self.input_data_3 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_3 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_3.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #3 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        @Inputs.shadow_data_4
        def set_shadow_data4(self, shadow_data: ShadowData):
            self.le_weight_input_data_4.setEnabled(False)
            self.input_data_4 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_4 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_4.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #4 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        @Inputs.shadow_data_5
        def set_shadow_data5(self, shadow_data: ShadowData):
            self.le_weight_input_data_5.setEnabled(False)
            self.input_data_5 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_5 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_5.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #5 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        @Inputs.shadow_data_6
        def set_shadow_data6(self, shadow_data: ShadowData):
            self.le_weight_input_data_6.setEnabled(False)
            self.input_data_6 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_6 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_6.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #6 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        @Inputs.shadow_data_7
        def set_shadow_data7(self, shadow_data: ShadowData):
            self.le_weight_input_data_7.setEnabled(False)
            self.input_data_7 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_7 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_7.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #7 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        @Inputs.shadow_data_8
        def set_shadow_data8(self, shadow_data: ShadowData):
            self.le_weight_input_data_8.setEnabled(False)
            self.input_data_8 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_8 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_8.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #8 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        @Inputs.shadow_data_9
        def set_shadow_data9(self, shadow_data: ShadowData):
            self.le_weight_input_data_9.setEnabled(False)
            self.input_data_9 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_9 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_9.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #9 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        @Inputs.shadow_data_10
        def set_shadow_data10(self, shadow_data: ShadowData):
            self.le_weight_input_data_10.setEnabled(False)
            self.input_data_10 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_10 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_10.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #10 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)
    else:
        def set_shadow_data1(self, shadow_data: ShadowData):
            self.le_weight_input_data_1.setEnabled(False)
            self.input_data_1 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_1 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_1.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #1 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        def set_shadow_data2(self, shadow_data: ShadowData):
            self.le_weight_input_data_2.setEnabled(False)
            self.input_data_2 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_2 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_2.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #2 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        def set_shadow_data3(self, shadow_data: ShadowData):
            self.le_weight_input_data_3.setEnabled(False)
            self.input_data_3 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_3 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_3.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #3 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        def set_shadow_data4(self, shadow_data: ShadowData):
            self.le_weight_input_data_4.setEnabled(False)
            self.input_data_4 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_4 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_4.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #4 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        def set_shadow_data5(self, shadow_data: ShadowData):
            self.le_weight_input_data_5.setEnabled(False)
            self.input_data_5 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_5 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_5.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #5 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        def set_shadow_data6(self, shadow_data: ShadowData):
            self.le_weight_input_data_6.setEnabled(False)
            self.input_data_6 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_6 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_6.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #6 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        def set_shadow_data7(self, shadow_data: ShadowData):
            self.le_weight_input_data_7.setEnabled(False)
            self.input_data_7 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_7 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_7.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #7 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        def set_shadow_data8(self, shadow_data: ShadowData):
            self.le_weight_input_data_8.setEnabled(False)
            self.input_data_8 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_8 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_8.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #8 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        def set_shadow_data9(self, shadow_data: ShadowData):
            self.le_weight_input_data_9.setEnabled(False)
            self.input_data_9 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_9 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_9.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #9 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)

        def set_shadow_data10(self, shadow_data: ShadowData):
            self.le_weight_input_data_10.setEnabled(False)
            self.input_data_10 = None

            if ShadowCongruence.check_empty_data(shadow_data):
                if ShadowCongruence.check_good_beam(shadow_data.beam):
                    self.input_data_10 = shadow_data
                    if self.use_weights == 1: self.le_weight_input_data_10.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Error", "Data #10 not displayable: No good rays or bad content",
                                         QMessageBox.Ok)


    def get_lightsource(self):

        try:    name = self.getNode().title
        except: name = "Merged beamlines"

        light_source = S4LightSourceFromBeamlines(name=name)

        try:
            for index in range(1, 11):
                current_data: ShadowData = getattr(self, "input_data_" + str(index))

                if not current_data is None:
                    if self.use_weights == 1:
                        weight = getattr(self, "weight_input_data_" + str(index))
                    else:
                        weight = 1.0
                    light_source.append_beamline(current_data.beamline, id="beamline channel %d" % (index + 1), weight=weight)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)

            if self.IS_DEVELOP: raise e

        return light_source

    def merge_data(self):

        self.setStatusMessage("")
        set_verbose()
        self.shadow_output.setText("")
        sys.stdout = EmittingStream(textWritten=self._write_stdout)

        self.progressBarInit()

        light_source = self.get_lightsource()

        # script
        script = light_source.to_python_code()
        script += "\n\n# test plot\nfrom srxraylib.plot.gol import plot_scatter"
        script += "\nrays = beam.get_rays()"
        script += "\nplot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 2], title='(X,Z) in microns')"
        self.shadow4_script.set_code(script)

        self.progressBarSet(5)


        try:
            merged_beam = None

            for index in range(1, 11):
                current_data: ShadowData = getattr(self, "input_data_" + str(index))
                if not current_data is None:
                    current_data_beam = current_data.beam.duplicate()

                    if self.use_weights == 1:
                        weight = getattr(self, "weight_input_data_" + str(index))
                        if weight < 0: raise ValueError(f"Weight #{index} is must be > 0]")

                        current_data_beam.apply_attenuation(numpy.sqrt(weight)) # weights are intensities!

                    if merged_beam is None:
                        merged_beam = current_data_beam
                    else:
                        merged_beam.append_beam(current_data_beam, update_column_index=True)

            if O2:
                self.Outputs.shadow_data.send(ShadowData(
                    beamline=S4Beamline(light_source=light_source),
                    beam=merged_beam,
                    number_of_rays=merged_beam.N))
            else:
                pass # TODO
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)

            if self.IS_DEVELOP: raise e


        # beam plots
        self._plot_results(merged_beam, None, progressBarValue=80)
        self.progressBarFinished()

    def set_UseWeights(self):
        self.le_weight_input_data_1.setEnabled(self.use_weights == 1 and not self.input_data_1 is None)
        self.le_weight_input_data_2.setEnabled(self.use_weights == 1 and not self.input_data_2 is None)
        self.le_weight_input_data_3.setEnabled(self.use_weights == 1 and not self.input_data_3 is None)
        self.le_weight_input_data_4.setEnabled(self.use_weights == 1 and not self.input_data_4 is None)
        self.le_weight_input_data_5.setEnabled(self.use_weights == 1 and not self.input_data_5 is None)
        self.le_weight_input_data_6.setEnabled(self.use_weights == 1 and not self.input_data_6 is None)
        self.le_weight_input_data_7.setEnabled(self.use_weights == 1 and not self.input_data_7 is None)
        self.le_weight_input_data_8.setEnabled(self.use_weights == 1 and not self.input_data_8 is None)
        self.le_weight_input_data_9.setEnabled(self.use_weights == 1 and not self.input_data_9 is None)
        self.le_weight_input_data_10.setEnabled(self.use_weights == 1 and not self.input_data_10 is None)


if O2: add_widget_parameters_to_module(__name__)

if __name__ == "__main__":
    def get_shadow_data():
        from shadow4.beamline.s4_beamline import S4Beamline

        beamline = S4Beamline()

        #
        #
        #
        from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
        light_source = SourceGeometrical(name='Geometrical Source', nrays=100000, seed=12345)
        light_source.set_spatial_type_gaussian(sigma_h=0.000553, sigma_v=0.000029)
        light_source.set_depth_distribution_off()
        light_source.set_angular_distribution_uniform(hdiv1=-0.000000, hdiv2=0.000000, vdiv1=-0.000030, vdiv2=0.000030)
        light_source.set_energy_distribution_singleline(10850.000000, unit='eV')
        light_source.set_polarization(polarization_degree=1.000000, phase_diff=0.000000, coherent_beam=0)
        beam = light_source.get_beam()

        beamline.set_light_source(light_source)

        # optical element number XX
        boundary_shape = None

        from shadow4.beamline.optical_elements.absorbers.s4_screen import S4Screen
        optical_element = S4Screen(name='Generic Beam Screen/Slit/Stopper/Attenuator (1)',
                                   boundary_shape=boundary_shape,
                                   i_abs=0,  # 0=No, 1=prerefl file_abs, 2=xraylib, 3=dabax
                                   i_stop=0, thick=0, file_abs='<specify file name>', material='Au', density=19.3)

        from syned.beamline.element_coordinates import ElementCoordinates
        coordinates = ElementCoordinates(p=31.15, q=0, angle_radial=0, angle_azimuthal=0, angle_radial_out=3.141592654)
        from shadow4.beamline.optical_elements.absorbers.s4_screen import S4ScreenElement
        beamline_element = S4ScreenElement(optical_element=optical_element, coordinates=coordinates, input_beam=beam)

        beam, footprint = beamline_element.trace_beam()

        beamline.append_beamline_element(beamline_element)

        # test plot
        if 0:
            from srxraylib.plot.gol import plot_scatter
            plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1),
                         title='(Intensity,Photon Energy)', plot_histograms=0)
            plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1),
                         title='(X,Z) in microns')

        output_data = ShadowData(beam=beam,
                                 number_of_rays=beam.N,
                                 beamline=beamline)

        return output_data


    if O2:
        from AnyQt.QtWidgets import QApplication
    else:
        from PyQt5.QtWidgets import QApplication

    a = QApplication(sys.argv)
    ow = MergeBeams()
    ow.show()
    ow.set_shadow_data1(get_shadow_data())
    ow.set_shadow_data2(get_shadow_data())
    a.exec()
    ow.saveSettings()