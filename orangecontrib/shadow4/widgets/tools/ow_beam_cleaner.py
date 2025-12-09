import numpy, copy, sys

from orangewidget import gui
from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence, TriggerToolsDecorator


# from oasys2.widget.util.widget_objects import TriggerIn
# from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module
# from oasys2.widget.widget import OWWidget
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox

from oasys.widgets.widget import OWWidget
from syned.widget.widget_decorator import WidgetDecorator
from orangewidget import widget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from oasys.util.oasys_util import TriggerIn


class BeamCleaner(OWWidget, TriggerToolsDecorator):
    name = "Beam Cleaner"
    description = "Tools: Beam Cleaner"
    icon = "icons/clean.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 30
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    # class Inputs:
    #     shadow_data = Input("Shadow Data", ShadowData, default=True, auto_summary=False)
    #
    # class Outputs:
    #     shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)
    #     trigger = TriggerToolsDecorator.get_trigger_output()

    inputs = [("Shadow Data", ShadowData, "set_shadow_data")]

    outputs = [{"name": "Shadow Data",
                "type": ShadowData,
                "doc": "", }]

    TriggerToolsDecorator.append_trigger_input_for_sources(inputs)
    TriggerToolsDecorator.append_trigger_output(outputs)

    want_main_area = 0
    want_control_area = 1

    def __init__(self):
         self.setFixedWidth(300)
         self.setFixedHeight(120)

         gui.separator(self.controlArea, height=20)
         gui.label(self.controlArea, self, "         LOST RAYS REMOVER", orientation="horizontal")
         gui.rubber(self.controlArea)

    def set_shadow_data(self, shadow_data: ShadowData):
        if ShadowCongruence.check_empty_data(shadow_data):
            output_data = shadow_data.duplicate()

            if ShadowCongruence.check_good_beam(input_beam=output_data.beam):
                output_data.beam.clean_lost_rays()

                self.send("Shadow Data", output_data)
                self.send("Trigger", TriggerIn(new_object=True))


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    a = QApplication(sys.argv)
    ow = BeamCleaner()
    ow.show()
    a.exec()
    ow.saveSettings()