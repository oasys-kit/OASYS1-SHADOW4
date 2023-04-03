import sys

from oasys.widgets.widget import OWWidget
from oasys.widgets.gui import MessageDialog
from orangewidget import gui
from orangewidget.settings import Setting

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

from oasys.widgets.gui import ConfirmDialog, MessageDialog

class AutomaticElement(OWWidget):
    want_main_area = 1
    is_automatic_run = Setting(True)

    MAX_WIDTH          = 1320
    MAX_HEIGHT         = 700
    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT   = 560

    def __init__(self, show_automatic_box=True):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))
        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())
        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        if show_automatic_box:
            self.general_options_box = gui.widgetBox(self.controlArea, "General Options", addSpace=True, orientation="horizontal")
            gui.checkBox(self.general_options_box, self, 'is_automatic_run', 'Automatic Execution')

    def call_reset_settings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:    self.resetSettings()
            except: pass

    def prompt_exception(self, exception: Exception):
        MessageDialog.message(self, str(exception), "Exception occured in OASYS", "critical")
        if self.IS_DEVELOP: raise exception


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = AutomaticElement()
    ow.show()
    a.exec_()
    ow.saveSettings()
