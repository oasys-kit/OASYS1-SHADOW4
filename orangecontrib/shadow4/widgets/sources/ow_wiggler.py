import sys

# from syned.storage_ring.magnetic_structures.wiggler import Wiggler
#
# from orangecontrib.shadow4.widgets.gui.ow_light_source import OWLightSource
# # from orangecontrib.syned.widgets.gui.ow_light_source import OWLightSource
# # from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
# from orangecontrib.shadow4.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow4.widgets.gui.ow_electron_beam import OWElectronBeam
from oasys.widgets import gui as oasysgui
from orangewidget import gui as orangegui
from orangewidget.settings import Setting

class OWWiggler(OWElectronBeam):

    name = "Wiggler Light Source"
    description = "Wiggler Light Source"
    icon = "icons/wiggler.png"
    priority = 3

    type_combo = Setting(0)
    number_of_periods = Setting(1)
    k_value = Setting(10.0)
    id_period = Setting(0.010)
    file_with_b_vs_y = Setting("tmp.b")
    file_with_harmonics = Setting("tmp.h")

    use_emittances_combo = Setting(0)
    shift_x_flag = Setting(0)
    shift_x_value =Setting(0.0)

    shift_betax_flag = Setting(0)
    shift_betax_value = Setting(0.0)


    def __init__(self):
        super().__init__()

        tab_wiggler = oasysgui.createTabPage(self.tabs_control_area, "Wiggler Setting")


        left_box_3 = oasysgui.widgetBox(tab_wiggler, "Wiggler Parameters", addSpace=False, orientation="vertical", height=200)

        orangegui.comboBox(left_box_3, self, "type_combo", label="Type", items=["conventional/sinusoidal", "B from file (y [m], Bz [T])", "B from harmonics"], callback=self.set_visibility, labelWidth=220, orientation="horizontal")

        oasysgui.lineEdit(left_box_3, self, "number_of_periods", "Number of Periods", labelWidth=260, tooltip="Number of Periods", valueType=int, orientation="horizontal")

        self.conventional_sinusoidal_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.conventional_sinusoidal_box, self, "k_value", "K value", labelWidth=260, tooltip="K value", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.conventional_sinusoidal_box, self, "id_period", "ID period [m]", labelWidth=260, tooltip="ID period [m]", valueType=float, orientation="horizontal")

        self.b_from_file_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.b_from_file_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_b_vs_y = oasysgui.lineEdit(file_box, self, "file_with_b_vs_y", "File/Url with B vs Y", labelWidth=150, tooltip="File/Url with B vs Y", valueType=str, orientation="horizontal")

        orangegui.button(file_box, self, "...", callback=self.selectFileWithBvsY)

        self.b_from_harmonics_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.b_from_harmonics_box, self, "id_period", "ID period [m]", labelWidth=260, tooltip="ID period [m]", valueType=float, orientation="horizontal")

        file_box = oasysgui.widgetBox(self.b_from_harmonics_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_harmonics = oasysgui.lineEdit(file_box, self, "file_with_harmonics", "File/Url with harmonics", labelWidth=150, tooltip="File/Url with harmonics", valueType=str, orientation="horizontal")

        orangegui.button(file_box, self, "...", callback=self.selectFileWithHarmonics)





        left_box_10 = oasysgui.widgetBox(tab_wiggler, "Electron Beam Parameters", addSpace=False, orientation="vertical", height=200)

        orangegui.comboBox(left_box_10, self, "use_emittances_combo", label="Use Emittances?", items=["No", "Yes"],
                           callback=self.set_visibility, labelWidth=260, orientation="horizontal")

        orangegui.comboBox(left_box_10, self, "shift_betax_flag", label="Shift Transversal Velocity", items=["No shift", "Half excursion", "Minimum", "Maximum", "Value at zero", "User value"], callback=self.set_ShiftBetaXFlag, labelWidth=260, orientation="horizontal")
        self.shift_betax_value_box = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        self.shift_betax_value_box_hidden = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        oasysgui.lineEdit(self.shift_betax_value_box, self, "shift_betax_value", "Value", labelWidth=260, valueType=float, orientation="horizontal")

        orangegui.comboBox(left_box_10, self, "shift_x_flag", label="Shift Transversal Coordinate", items=["No shift", "Half excursion", "Minimum", "Maximum", "Value at zero", "User value"], callback=self.set_ShiftXFlag, labelWidth=260, orientation="horizontal")
        self.shift_x_value_box = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        self.shift_x_value_box_hidden = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        oasysgui.lineEdit(self.shift_x_value_box, self, "shift_x_value", "Value [m]", labelWidth=260, valueType=float, orientation="horizontal")


        self.set_ShiftXFlag()
        self.set_ShiftBetaXFlag()







        self.set_visibility()

        orangegui.rubber(self.controlArea)

    def set_visibility(self):
        self.conventional_sinusoidal_box.setVisible(self.type_combo == 0)
        self.b_from_file_box.setVisible(self.type_combo == 1)
        self.b_from_harmonics_box.setVisible(self.type_combo == 2)


    def selectFileWithBvsY(self):
        self.le_file_with_b_vs_y.setText(oasysgui.selectFileFromDialog(self, self.file_with_b_vs_y, "Open File With B vs Y"))

    def selectFileWithHarmonics(self):
        self.le_file_with_harmonics.setText(oasysgui.selectFileFromDialog(self, self.file_with_harmonics, "Open File With Harmonics"))


    def set_ShiftXFlag(self):
        self.shift_x_value_box.setVisible(self.shift_x_flag==5)
        self.shift_x_value_box_hidden.setVisible(self.shift_x_flag!=5)

    def set_ShiftBetaXFlag(self):
        self.shift_betax_value_box.setVisible(self.shift_betax_flag==5)
        self.shift_betax_value_box_hidden.setVisible(self.shift_betax_flag!=5)


    # def get_magnetic_structure(self):
    #     return Wiggler(K_horizontal=self.K_horizontal,
    #                    K_vertical=self.K_vertical,
    #                    period_length=self.period_length,
    #                    number_of_periods=self.number_of_periods)
    #
    # def check_magnetic_structure_instance(self, magnetic_structure):
    #     if not isinstance(magnetic_structure, Wiggler):
    #         raise ValueError("Magnetic Structure is not a Wiggler")
    #
    # def populate_magnetic_structure(self, magnetic_structure):
    #     if not isinstance(magnetic_structure, Wiggler):
    #         raise ValueError("Magnetic Structure is not a Wiggler")
    #
    #     self.K_horizontal = magnetic_structure._K_horizontal
    #     self.K_vertical = magnetic_structure._K_vertical
    #     self.period_length = magnetic_structure._period_length
    #     self.number_of_periods = magnetic_structure._number_of_periods




if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWWiggler()
    ow.show()
    a.exec_()
    #ow.saveSettings()
