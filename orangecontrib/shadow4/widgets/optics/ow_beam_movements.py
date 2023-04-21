import numpy
import sys

from PyQt5.QtGui import QPalette, QColor, QFont


from orangewidget import widget
from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement

from syned.widget.widget_decorator import WidgetDecorator

from shadow4.beamline.optical_elements.ideal_elements.s4_beam_movement import S4BeamMovement, S4BeamMovementElement

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence


class OWBeamMovement(GenericElement, WidgetDecorator):

    name = "Beam movements"
    description = "Shadow Beam Movement"
    icon = "icons/beam_movement.png"
    priority = 10.1

    inputs = [("Shadow Data", ShadowData, "set_shadow_data")]
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Shadow Data",
                "type":ShadowData,
                "doc":"",}]

    #########################################################
    # Position
    #########################################################
    apply_flag = Setting(1)
    translation_x  = Setting(0.0)
    translation_y  = Setting(0.0)
    translation_z  = Setting(0.0)
    rotation_x     = Setting(0.0)
    rotation_y     = Setting(0.0)
    rotation_z     = Setting(0.0)

    input_data = None
    beamline = None


    def __init__(self):
        super().__init__(show_automatic_box=True, has_footprint=False)

        #
        # main buttons
        #
        self.runaction = widget.OWAction("Run Shadow4/Trace", self)
        self.runaction.triggered.connect(self.run_shadow4)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run shadow4/trace", callback=self.run_shadow4)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        #
        # tabs
        #
        self.tabs_control_area = oasysgui.tabWidget(self.controlArea)
        self.tabs_control_area.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_control_area.setFixedWidth(self.CONTROL_AREA_WIDTH-5)


        self.tab_movement = oasysgui.createTabPage(self.tabs_control_area, "Movement")           # to be populated

        #
        # populate tabs with widgets
        #

        #########################################################
        # Position
        #########################################################
        self.populate_tab_movement()

        self.update_panels()
        #
        #
        #

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def resetSettings(self):
        self.translation_x = 0.0
        self.translation_y = 0.0
        self.translation_z = 0.0
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0


    def populate_tab_movement(self):

        gui.comboBox(self.tab_movement, self, "apply_flag", label="Apply movements",
                     labelWidth=250, items=["Off", "On"], callback=self.update_panels,
                     sendSelectedValue=False, orientation="horizontal", tooltip="angles_respect_to")


        self.translation_box = oasysgui.widgetBox(self.tab_movement, "Translation", addSpace=True, orientation="vertical")
        self.rotation_box = oasysgui.widgetBox(self.tab_movement, "Rotation", addSpace=True, orientation="vertical")


        oasysgui.lineEdit(self.translation_box, self, "translation_x", "Translation along X [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="translation_x")
        oasysgui.lineEdit(self.translation_box, self, "translation_y", "Translation along Y [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="translation_y")
        oasysgui.lineEdit(self.translation_box, self, "translation_z", "Translation along Z [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="translation_z")

        oasysgui.lineEdit(self.rotation_box, self, "rotation_x", "1) Rotation along X [rad]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="rotation_x")
        oasysgui.lineEdit(self.rotation_box, self, "rotation_y", "2) Rotation along Y [rad]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="rotation_y")
        oasysgui.lineEdit(self.rotation_box, self, "rotation_z", "3) Rotation along Z [rad]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="rotation_z")


    def update_panels(self):

        if self.apply_flag:
            self.translation_box.setVisible(True)
            self.rotation_box.setVisible(True)
        else:
            self.translation_box.setVisible(False)
            self.rotation_box.setVisible(False)


    def get_oe_instance(self):
        return S4BeamMovement(
            apply_flag = self.apply_flag,
            translation_x = self.translation_x,
            translation_y = self.translation_y,
            translation_z = self.translation_z,
            rotation_x = self.rotation_x,
            rotation_y = self.rotation_y,
            rotation_z = self.rotation_z,
        )

    def get_element_instance(self):
        optical_element = S4BeamMovementElement()
        optical_element.set_optical_element(self.get_oe_instance())
        # optical_element.set_coordinates()
        optical_element.set_input_beam(self.input_data.beam)
        return optical_element

    def set_shadow_data(self, input_data):
        self.not_interactive = self._check_not_interactive_conditions(input_data)

        self._on_receiving_input()

        if ShadowCongruence.check_empty_data(input_data):
            self.input_data = input_data.duplicate()
            if self.is_automatic_run: self.run_shadow4()


    def run_shadow4(self):
        self.shadow_output.setText("")

        sys.stdout = EmittingStream(textWritten=self._write_stdout)

        element = self.get_element_instance()
        print(element.info())

        self.progressBarInit()

        output_beam, _ = element.trace_beam()

        beamline = self.input_data.beamline.duplicate()
        beamline.append_beamline_element(element)

        self._set_plot_quality()

        self._plot_results(output_beam, None, progressBarValue=80)

        self.progressBarFinished()

        #
        # script
        #
        script = beamline.to_python_code()
        script += "\n\n\n# test plot"
        script += "\nif True:"
        script += "\n   from srxraylib.plot.gol import plot_scatter"
        script += "\n   # plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)', plot_histograms=0)"
        script += "\n   plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')"
        self.shadow4_script.set_code(script)

        #
        # send beam
        #
        self.send("Shadow Data", ShadowData(beam=output_beam, beamline=beamline))


if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline
    def get_test_beam():
        # electron beam
        from syned.storage_ring.light_source import ElectronBeam
        electron_beam = ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
        electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=3.63641e-06, sigma_xp=4.36821e-06,
                                     sigma_yp=1.37498e-06)

        # Gaussian undulator
        from shadow4.sources.undulator.s4_undulator import S4Undulator
        undulator_source = S4Undulator(
            period_length=0.0159999,
            number_of_periods=100,
            emin=2700.136,
            emax=2700.136,
            flag_emittance=1,  # Use emittance (0=No, 1=Yes)
        )
        undulator_source.set_energy_monochromatic(2700.14)

        from shadow4.sources.undulator.s4_undulator_light_source import S4UndulatorLightSource
        light_source = S4UndulatorLightSource(name='GaussianUndulator', electron_beam=electron_beam,
                                             magnetic_structure=undulator_source)

        beam = light_source.get_beam_in_gaussian_approximation()

        return ShadowData(beam=beam, beamline=S4Beamline(light_source=light_source))

    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWBeamMovement()
    ow.set_shadow_data(get_test_beam())
    ow.show()
    a.exec_()
    ow.saveSettings()
