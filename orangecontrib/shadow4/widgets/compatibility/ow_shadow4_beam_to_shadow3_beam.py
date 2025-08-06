from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

from orangewidget import gui
from oasys.widgets import gui as oasysgui

from oasys.widgets.widget import AutomaticWidget
from orangewidget.settings import Setting

from orangecontrib.shadow4.util.shadow4_objects import ShadowData

try:
    import Shadow
    from orangecontrib.shadow.util.shadow_objects import ShadowBeam as ShadowBeam3
except:
    pass

class OW_beam_converter_4_to_3(AutomaticWidget):
    name = "shadow4->3 beam converter"
    id = "toShadowOUIbeam"
    description = "shadow4->3 beam converter"
    icon = "icons/beam4to3.png"
    priority = 20
    category = ""
    keywords = ["shadow3", "shadow4"]

    inputs = [("Shadow Data", ShadowData, "set_input")]

    outputs = [{"name":"Shadow3 Beam",
                "type":ShadowBeam3,
                "doc":"",
                "id":"Beam"}]

    MAX_WIDTH = 420
    MAX_HEIGHT = 230
    CONTROL_AREA_WIDTH = 410

    want_main_area = 0

    pixels_h = Setting(100)
    pixels_v = Setting(100)

    shadow_data = None

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMinimumHeight(self.geometry().height())
        self.setMinimumWidth(self.geometry().width())
        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.MAX_WIDTH-10)
        self.controlArea.setFixedHeight(self.MAX_HEIGHT-10)

        main_box = oasysgui.widgetBox(self.controlArea, "From Shadow4 Beam To Shadow3 (ShadowOUI) Beam", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=140)

        # oasysgui.lineEdit(main_box, self, "pixels_h", "Number of Pixels (H)", labelWidth=280, valueType=int, orientation="horizontal")
        # oasysgui.lineEdit(main_box, self, "pixels_v", "Number of Pixels (V)", labelWidth=280, valueType=int, orientation="horizontal")

        gui.button(main_box, self, "Compute", callback=self.convert_beam, height=45)

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.shadow_data = input_data

            if self.is_automatic_execution:
                self.convert_beam()

    def convert_beam(self):
        if self.shadow_data is None:
            self.prompt_exception(ValueError("No Shadow4 input beam"))
            return

        try:
            beam4 = self.shadow_data.beam
            print(">>beam4: ", beam4)
            beam3 = Shadow.Beam(N=self.shadow_data.get_number_of_rays())
            beam3.rays = beam4.rays.copy()
            beam3.rays[:, 0:3] /= self.workspace_units_to_m
            beam3.rays[:, 12] /= self.workspace_units_to_m
            print(">>beam3: ", beam3)
            print(beam4.get_number_of_rays(), beam3.nrays())
            output_beam3 = ShadowBeam3(beam=beam3, number_of_rays=self.shadow_data.get_number_of_rays())
            print(output_beam3)
            self.send("Shadow3 Beam", output_beam3)
        except Exception as exception:
            self.prompt_exception(exception)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    a = QApplication(sys.argv)
    ow = OW_beam_converter_4_to_3()
    ow.set_input(ShadowData())
    ow.show()
    a.exec_()
    #ow.saveSettings()

