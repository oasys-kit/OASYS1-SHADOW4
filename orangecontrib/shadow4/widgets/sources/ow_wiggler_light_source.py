import sys

from syned.storage_ring.magnetic_structures.wiggler import Wiggler

from orangecontrib.shadow4.widgets.gui import ow_insertion_device

class OWWigglerLightSource(ow_insertion_device.OWInsertionDevice):

    name = "Wiggler Light Source"
    description = "Syned: Wiggler Light Source"
    icon = "icons/wiggler.png"
    priority = 3

    def __init__(self):
        super().__init__()

    def get_magnetic_structure(self):
        return Wiggler(K_horizontal=self.K_horizontal,
                       K_vertical=self.K_vertical,
                       period_length=self.period_length,
                       number_of_periods=self.number_of_periods)

    def check_magnetic_structure_instance(self, magnetic_structure):
        if not isinstance(magnetic_structure, Wiggler):
            raise ValueError("Magnetic Structure is not a Wiggler")

    def populate_magnetic_structure(self, magnetic_structure):
        if not isinstance(magnetic_structure, Wiggler):
            raise ValueError("Magnetic Structure is not a Wiggler")

        self.K_horizontal = magnetic_structure._K_horizontal
        self.K_vertical = magnetic_structure._K_vertical
        self.period_length = magnetic_structure._period_length
        self.number_of_periods = magnetic_structure._number_of_periods


from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = OWWigglerLightSource()
    ow.show()
    a.exec_()
    #ow.saveSettings()
