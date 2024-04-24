import sys
import numpy
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow4.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D, plot_data2D, plot_data3D, plot_multi_data1D

from shadow4.tools.beamline_tools import focnew, focnew_scan, focnew_scan_full_beamline
from shadow4.tools.logger import set_verbose

class FocNew(AutomaticElement):

    name = "FocNew"
    description = "Tools: FocNew"
    icon = "icons/focnew.png"
    maintainer = "M. Sanchez del Rio and L. Rebuffi"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 5
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Shadow Data", ShadowData, "set_shadow_data")]

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 675

    want_main_area=1
    want_control_area = 1

    mode = Setting(0)
    center_x = Setting(0.0)
    center_z = Setting(0.0)

    # y_range=Setting(0)
    y_range_min=Setting(-10.0)
    y_range_max=Setting(10.0)
    y_npoints=Setting(1001)
    npoints_beamline=Setting(11)

    plot_canvas_x = None
    plot_canvas_bl = None


    input_data = None

    def __init__(self):
        super().__init__(show_automatic_box=True)

        gui.button(self.controlArea, self, "Calculate", callback=self.calculate, height=45)

        general_box = oasysgui.widgetBox(self.controlArea, "General Settings", addSpace=True, orientation="vertical") # , width=self.CONTROL_AREA_WIDTH-8, height=220)

        gui.comboBox(general_box, self, "mode", label="Mode", labelWidth=250,
                                     items=["Center at Origin",
                                            "Center at Barycenter",
                                            "External"],
                                     callback=self.set_Center, sendSelectedValue=False, orientation="horizontal")

        self.center_box = oasysgui.widgetBox(general_box, "", addSpace=False, orientation="vertical", height=50)
        self.center_box_empty = oasysgui.widgetBox(general_box, "", addSpace=False, orientation="vertical", height=50)

        self.le_center_x = oasysgui.lineEdit(self.center_box, self, "center_x", "Center X [m]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_center_z = oasysgui.lineEdit(self.center_box, self, "center_z", "Center Z [m]", labelWidth=260, valueType=float, orientation="horizontal")

        # gui.comboBox(general_box, self, "y_range", label="Y Range",labelWidth=250,
        #                              items=["<Default>",
        #                                     "Set.."],
        #                              callback=self.set_YRange, sendSelectedValue=False, orientation="horizontal")

        self.yrange_box = oasysgui.widgetBox(general_box, "", addSpace=False, orientation="vertical", height=100)
        self.yrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=False, orientation="vertical",  height=100)

        self.le_y_range_min = oasysgui.lineEdit(self.yrange_box, self, "y_range_min", "Y min [m]", labelWidth=250, valueType=float, orientation="horizontal")
        self.le_y_range_max = oasysgui.lineEdit(self.yrange_box, self, "y_range_max", "Y max [m]", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.yrange_box, self, "y_npoints", "Points (for focnew scan)", labelWidth=300, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.yrange_box, self, "npoints_beamline", "Points inter o.e. (for focnew full beamline)", labelWidth=300, valueType=int, orientation="horizontal")

        gui.separator(self.controlArea, height=200)

        tabs_setting = oasysgui.tabWidget(self.mainArea)
        tabs_setting.setFixedHeight(self.IMAGE_HEIGHT+5)
        tabs_setting.setFixedWidth(self.IMAGE_WIDTH)

        tab_info = oasysgui.createTabPage(tabs_setting, "Focnew Info")
        tab_scan = oasysgui.createTabPage(tabs_setting, "Focnew Scan")
        tab_beamline = oasysgui.createTabPage(tabs_setting, "Focnew Full Beamline")
        # tab_scan_old = oasysgui.createTabPage(tabs_setting, "Focnew Scan Old")
        tab_out = oasysgui.createTabPage(tabs_setting, "System Output")

        self.focnewInfo = oasysgui.textArea(height=self.IMAGE_HEIGHT-35)
        info_box = oasysgui.widgetBox(tab_info, "", addSpace=True, orientation="horizontal", width = self.IMAGE_WIDTH-20, ) # height = self.IMAGE_HEIGHT-20)
        info_box.layout().addWidget(self.focnewInfo)

        self.image_box = gui.widgetBox(tab_scan, "Scan", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT-30)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH-20)

        self.beamline_box = gui.widgetBox(tab_beamline, "Scan", addSpace=True, orientation="vertical")
        self.beamline_box.setFixedHeight(self.IMAGE_HEIGHT-30)
        self.beamline_box.setFixedWidth(self.IMAGE_WIDTH-20)

        self.shadow_output = oasysgui.textArea(height=self.IMAGE_HEIGHT-35)
        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", width = self.IMAGE_WIDTH-20, ) # height = self.IMAGE_HEIGHT-20)
        out_box.layout().addWidget(self.shadow_output)

        self.set_Center()
        # self.set_YRange()


    def set_Center(self):
        self.center_box.setVisible(self.mode == 2)
        self.center_box_empty.setVisible(self.mode < 2)

    # def set_YRange(self):
    #     self.yrange_box.setVisible(self.y_range == 1)
    #     self.yrange_box_empty.setVisible(self.y_range == 0)


    def setBeam(self, shadow_data):
        if ShadowCongruence.checkEmptyBeam(shadow_data):
            if ShadowCongruence.checkGoodBeam(shadow_data):
                self.input_data = shadow_data
                if self.is_automatic_run:
                    self.calculate()
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def calculate(self):
        set_verbose(0)
        sys.stdout = EmittingStream(textWritten=self.write_stdout)

        self.shadow_output.setText("")
        self.focnewInfo.setText("")
        if self.plot_canvas_x is not None: self.image_box.layout().removeItem(self.image_box.layout().itemAt(0))
        if self.plot_canvas_bl is not None: self.beamline_box.layout().removeItem(self.beamline_box.layout().itemAt(0))

        if self.input_data is None:
            print("*** Error *** Missing beam")
            return

        try:
            ticket = focnew(beam=self.input_data.beam, nolost=1, mode=self.mode, center=[self.center_x, self.center_z])
            self.focnewInfo.setText(ticket['text'])
            self.do_plot_focnew(ticket)
            self.do_plot_beamline()

            print("list of 6 coeffs: <d**2>, <x d>, <x**2>, <x>**2, <x><d>, <d>**2: ")
            print("AX coeffs: ", ticket["AX"])
            print("AZ coeffs: ", ticket["AZ"])
            print("AT coeffs: ", ticket["AT"])

            print("\n\nYou can retrieve the data in a script like this:")
            print("########################################################################")
            print("import numpy")
            print("from shadow4.tools.beamline_tools import focnew, focnew_scan, focnew_scan_full_beamline")
            print("beam = in_object_1.beam         # define your beam")
            print("beamline = in_object_1.beamline # define your beamline")
            print("ticket1 = focnew(beam=beam, nolost=1, mode=%d, center=[%g, %g])" % (self.mode, self.center_x, self.center_z))
            print("y = numpy.linspace(%f, %f, %d)" % (self.y_range_min, self.y_range_max, int(self.y_npoints)))
            print("x = focnew_scan(ticket1['AX'], y) * 1e6")
            print("z = focnew_scan(ticket1['AZ'], y) * 1e6")
            print("t = focnew_scan(ticket1['AT'], y) * 1e6")
            print("from srxraylib.plot.gol import plot")
            print("plot(y, x, y, z, xtitle='Y [m]', ytitle='<x> or <z> [um]', legend=['x','z'])")

            print("\nticket2 = focnew_scan_full_beamline(beamline, npoints=%d)" % self.npoints_beamline)
            print("plot(ticket2['y'], ticket2['x'], ticket2['y'], ticket2['z'], xtitle='Y [m]', ytitle='<H> or <V> [um]', legend=['H','V'])")
            print("########################################################################")

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)
            if self.IS_DEVELOP: raise exception


    def do_plot_focnew(self, ticket):
        # if self.y_range == 0:
        #     y = numpy.linspace(-10.0, 10.0, 1001)
        # else:
        #     y = numpy.linspace(self.y_range_min, self.y_range_max, int(self.y_npoints))

        y = numpy.linspace(self.y_range_min, self.y_range_max, int(self.y_npoints))

        ylist = [focnew_scan(ticket["AX"], y) * 1e6,
                 focnew_scan(ticket["AZ"], y) * 1e6,
                 focnew_scan(ticket["AT"], y) * 1e6]

        self.plot_canvas_x = plot_multi_data1D(y, ylist,
                                               title="title",
                                               xtitle="Y [m]",
                                               ytitle="<X> or <Z> or <X,Z> [$\mu$m]",
                                               ytitles=["X","Z","X,Z combined"],
                                               flag_common_abscissas=1)

        self.image_box.layout().addWidget(self.plot_canvas_x)

    def do_plot_beamline(self):
        ticket = focnew_scan_full_beamline(self.input_data.beamline, npoints=self.npoints_beamline)

        self.plot_canvas_bl = plot_multi_data1D(ticket['list_y'] + ticket['list_y'],
                                                ticket['list_x'] + ticket['list_z'],
                                                title="title",
                                                xtitle="Y [m]",
                                                ytitle="<H> or <V> [$\mu$m]",
                                                ytitles=ticket['list_x_label'] + ticket['list_z_label'],
                                                flag_common_abscissas=0)  # , xrange=[0, yy_multi[-1][-1]])

        self.beamline_box.layout().addWidget(self.plot_canvas_bl)


    def set_shadow_data(self, input_data):
        if ShadowCongruence.check_empty_data(input_data):
            self.input_data = input_data.duplicate()
            if self.is_automatic_run: self.calculate()

    def write_stdout(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    def get_beamline():
        from shadow4.beamline.s4_beamline import S4Beamline

        beamline = S4Beamline()

        # electron beam
        from shadow4.sources.s4_electron_beam import S4ElectronBeam
        electron_beam = S4ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
        electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=4.36821e-06, sigma_xp=3.63641e-06,
                                     sigma_yp=1.37498e-06)

        # magnetic structure
        from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian
        source = S4UndulatorGaussian(
            period_length=0.042,  # syned Undulator parameter (length in m)
            number_of_periods=38.571,  # syned Undulator parameter
            photon_energy=5000.0,  # Photon energy (in eV)
            delta_e=4.0,  # Photon energy width (in eV)
            ng_e=100,  # Photon energy scan number of points
            flag_emittance=1,  # when sampling rays: Use emittance (0=No, 1=Yes)
            flag_energy_spread=0,  # when sampling rays: Use e- energy spread (0=No, 1=Yes)
            harmonic_number=1,  # harmonic number
            flag_autoset_flux_central_cone=1,  # value to set the flux peak
            flux_central_cone=681709040139326.4,  # value to set the flux peak
        )

        # light source
        from shadow4.sources.undulator.s4_undulator_gaussian_light_source import S4UndulatorGaussianLightSource
        light_source = S4UndulatorGaussianLightSource(name='GaussianUndulator', electron_beam=electron_beam,
                                                      magnetic_structure=source, nrays=15000, seed=5676561)
        beam = light_source.get_beam()

        beamline.set_light_source(light_source)

        # optical element number XX
        from syned.beamline.shape import Rectangle
        boundary_shape = Rectangle(x_left=-0.001, x_right=0.001, y_bottom=-0.001, y_top=0.001)

        from shadow4.beamline.optical_elements.absorbers.s4_screen import S4Screen
        optical_element = S4Screen(name='Generic Beam Screen/Slit/Stopper/Attenuator', boundary_shape=boundary_shape,
                                   i_abs=0,  # 0=No, 1=prerefl file_abs, 2=xraylib, 3=dabax
                                   i_stop=0, thick=0, file_abs='<specify file name>', material='Au', density=19.3)

        from syned.beamline.element_coordinates import ElementCoordinates
        coordinates = ElementCoordinates(p=27.2, q=0, angle_radial=0, angle_azimuthal=0, angle_radial_out=3.141592654)
        from shadow4.beamline.optical_elements.absorbers.s4_screen import S4ScreenElement
        beamline_element = S4ScreenElement(optical_element=optical_element, coordinates=coordinates, input_beam=beam)

        beam, footprint = beamline_element.trace_beam()

        beamline.append_beamline_element(beamline_element)

        # optical element number XX
        boundary_shape = None

        from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror
        optical_element = S4PlaneMirror(name='Plane Mirror', boundary_shape=boundary_shape,
                                        f_reflec=1, f_refl=5, file_refl='<none>', refraction_index=0.99999 + 0.001j,
                                        coating_material='Ni', coating_density=8.902, coating_roughness=0)

        from syned.beamline.element_coordinates import ElementCoordinates
        coordinates = ElementCoordinates(p=2.7, q=0, angle_radial=1.563796327, angle_azimuthal=1.570796327,
                                         angle_radial_out=1.563796327)
        movements = None
        from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirrorElement
        beamline_element = S4PlaneMirrorElement(optical_element=optical_element, coordinates=coordinates,
                                                movements=movements, input_beam=beam)

        beam, mirr = beamline_element.trace_beam()

        beamline.append_beamline_element(beamline_element)

        # test plot
        if 0:
            from srxraylib.plot.gol import plot_scatter
            plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1),
                         title='(Intensity,Photon Energy)', plot_histograms=0)
            plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1),
                         title='(X,Z) in microns')
        return beam, footprint, beamline
    ###############################
    beam, footprint, beamline = get_beamline()

    if 1:
        app = QApplication(sys.argv)
        w = FocNew()
        w.set_shadow_data(ShadowData(beam=beam, footprint=footprint, number_of_rays=0, beamline=beamline))
        w.show()
        app.exec()
        # w.saveSettings()

    if 0:
        #############################################################
        import numpy
        from shadow4.tools.beamline_tools import focnew, focnew_scan, focnew_scan_full_beamline

        # beam = in_object_1.beam  # define your beam
        # beamline = in_object_1.beamline  # define your beamline
        ticket1 = focnew(beam=beam, nolost=1, mode=0, center=[0.000000, 0.000000])
        y = numpy.linspace(-10.000000, 10.000000, 1001)
        x = focnew_scan(ticket1['AX'], y) * 1e6
        z = focnew_scan(ticket1['AZ'], y) * 1e6
        t = focnew_scan(ticket1['AT'], y) * 1e6
        from srxraylib.plot.gol import plot

        plot(y, x, y, z, xtitle='Y [m]', ytitle='<x> or <z> [um]', legend=['x', 'z'])

        ticket2 = focnew_scan_full_beamline(beamline)
        plot(ticket2['y'], ticket2['x'], ticket2['y'], ticket2['z'], xtitle='Y [m]', ytitle='<H> or <V> [um]',
             legend=['H', 'V'])
        #############################################################