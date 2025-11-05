import os

from orangewidget import gui
from orangewidget.settings import Setting

from PyQt5.QtWidgets import QMessageBox

from oasys.widgets import gui as oasysgui, congruence
from oasys.widgets.widget import OWWidget

from orangewidget import widget

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence


class BeamFileWriter(OWWidget):
    name = "Shadow4 File Writer"
    description = "Tools: Shadow4 File Writer"
    icon = "icons/beam_file_writer.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 7
    category = "Tools"
    keywords = ["data", "file", "load", "read"]

    want_main_area = 0

    shadow_data_file_name = Setting("")
    is_automatic_run = Setting(1)

    inputs = [("Shadow Data", ShadowData, "set_shadow_data")]

    outputs = [{"name": "Shadow Data",
                "type": ShadowData,
                "doc": "", }]

    input_data = None

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Write Shadow File", self)

        self.runaction.triggered.connect(self.write_file)
        self.addAction(self.runaction)

        self.setFixedWidth(590)
        self.setFixedHeight(210)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Shadow4 File Selection", addSpace=True,
                                        orientation="vertical",
                                        width=570, height=110)

        gui.checkBox(left_box_1, self, 'is_automatic_run', 'Automatic Execution')

        gui.separator(left_box_1, height=10)

        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", width=550, height=35)

        self.le_shadow_data_file_name = oasysgui.lineEdit(figure_box, self, "shadow_data_file_name",
                                                          "Shadow4 File Name",
                                                          labelWidth=120, valueType=str, orientation="horizontal")
        self.le_shadow_data_file_name.setFixedWidth(330)

        gui.button(figure_box, self, "...", callback=self.selectFile)

        button = gui.button(self.controlArea, self, "Write Shadow4 File", callback=self.write_file)
        button.setFixedHeight(45)
        button.setFixedWidth(570)

        gui.rubber(self.controlArea)

    def selectFile(self):
        self.le_shadow_data_file_name.setText(
            oasysgui.selectSaveFileFromDialog(self, self.shadow_data_file_name, default_file_name="s4_data.h5",
                                              file_extension_filter="HDF5 Files (*.h5 *.hdf5 *.hdf)"))

    def set_shadow_data(self, input_data: ShadowData):
        if ShadowCongruence.check_empty_data(input_data):
            if ShadowCongruence.check_good_beam(input_data.beam):
                self.input_data = input_data
            else:
                QMessageBox.critical(self, "Error", "No good rays or bad content", QMessageBox.Ok)
                return
        else:
            QMessageBox.critical(self, "Error", "Empty input data or empty beam", QMessageBox.Ok)

        if self.is_automatic_run: self.write_file()


    def write_file(self):
        self.setStatusMessage("")

        try:
            if ShadowCongruence.check_empty_data(self.input_data):
                if congruence.checkFileName(self.shadow_data_file_name):
                    _ = self.input_data.beam.write_h5(self.shadow_data_file_name,
                                                      overwrite=True,
                                                      simulation_name='run001',
                                                      beam_name='begin')

                    _, file_name = os.path.split(self.shadow_data_file_name)

                    self.setStatusMessage("Current: " + file_name)

                    self.send("Shadow Data", self.input_data)
            else:
                QMessageBox.critical(self, "Error", "Empty input data or empty beam", QMessageBox.Ok)
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    a = QApplication(sys.argv)
    ow = BeamFileWriter()
    ow.show()
    a.exec_()
    ow.saveSettings()