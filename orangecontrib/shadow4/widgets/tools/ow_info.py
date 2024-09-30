import sys

from PyQt5 import QtGui
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from oasys.widgets import gui as oasysgui, widget
from oasys.widgets.gui import MessageDialog

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence
from orangecontrib.shadow4.util.python_script import PythonScript, PythonConsole

from shadow4.tools.beamline_tools import flux_summary

class OWInfo(widget.OWWidget):

    name = "Info"
    description = "Display Data: Info"
    icon = "icons/info.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "srio(@at@)esrf.eu, lrebuffi(@at@)anl.gov"
    priority = 4
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Shadow Data", ShadowData, "set_shadow_data")]

    WIDGET_WIDTH = 950
    WIDGET_HEIGHT = 650

    want_main_area=1
    want_control_area = 0

    input_data = None
    is_automatic_run = 1

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()

        window_width  = round(min(geom.width()*0.98, self.WIDGET_WIDTH))
        window_height = round(min(geom.height() * 0.95, self.WIDGET_HEIGHT))

        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               window_width,
                               window_height))

        gen_box = gui.widgetBox(self.mainArea, "Beamline Info", addSpace=True, orientation="horizontal")

        tabs_setting1 = oasysgui.tabWidget(gen_box)
        tabs_setting1.setFixedHeight(self.WIDGET_HEIGHT-60)
        tabs_setting1.setFixedWidth(self.WIDGET_WIDTH-60)

        tab_flux = oasysgui.createTabPage(tabs_setting1, "Flux-Power")
        tab_sys = oasysgui.createTabPage(tabs_setting1, "Sys Info")
        tab_sys_plot_side = oasysgui.createTabPage(tabs_setting1, "Sys Plot (Side View)")
        tab_sys_plot_top = oasysgui.createTabPage(tabs_setting1, "Sys Plot (Bottom View)")
        tab_sys_plot_front = oasysgui.createTabPage(tabs_setting1, "Sys Plot (Front View)")
        tab_mir = oasysgui.createTabPage(tabs_setting1, "OE Info")
        tab_sou = oasysgui.createTabPage(tabs_setting1, "Source Info")
        tab_dis = oasysgui.createTabPage(tabs_setting1, "Distances Summary")
        tab_syned = oasysgui.createTabPage(tabs_setting1, "BL (syned info)")
        tab_syned_json = oasysgui.createTabPage(tabs_setting1, "BL (json)")
        # tab_scr = oasysgui.createTabPage(tabs_setting1, "Python Script")
        tab_out = oasysgui.createTabPage(tabs_setting1, "System Output")

        # flux
        self.fluxPower = oasysgui.textArea()
        self.fluxPower.setMaximumHeight(self.WIDGET_HEIGHT-100)

        # sysinfo and plots
        self.sysInfo = oasysgui.textArea()
        self.sysInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)

        self.sysPlotSide = oasysgui.plotWindow(tab_sys_plot_side)
        self.sysPlotSide.setMaximumHeight(self.WIDGET_HEIGHT-100)

        self.sysPlotTop = oasysgui.plotWindow(tab_sys_plot_top)
        self.sysPlotTop.setMaximumHeight(self.WIDGET_HEIGHT-100)

        self.sysPlotFront = oasysgui.plotWindow(tab_sys_plot_front)
        self.sysPlotFront.setMaximumHeight(self.WIDGET_HEIGHT-100)

        # mirinfo
        self.mirInfo = oasysgui.textArea()
        self.mirInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)

        # sourcinfo
        self.sourceInfo = oasysgui.textArea()
        self.sourceInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)

        # syned doc
        self.synedInfo = oasysgui.textArea()
        self.synedInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)

        # syned json
        self.synedJson = oasysgui.textArea()
        self.synedJson.setMaximumHeight(self.WIDGET_HEIGHT-100)

        # distances
        self.distancesSummary = oasysgui.textArea()
        self.distancesSummary.setMaximumHeight(self.WIDGET_HEIGHT-100)

        # sysinfo plots
        flux_power_box = oasysgui.widgetBox(tab_flux, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        flux_power_box.layout().addWidget(self.fluxPower)

        sys_box = oasysgui.widgetBox(tab_sys, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        sys_box.layout().addWidget(self.sysInfo)

        sys_plot_side_box = oasysgui.widgetBox(tab_sys_plot_side, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        sys_plot_side_box.layout().addWidget(self.sysPlotSide)

        sys_plot_top_box = oasysgui.widgetBox(tab_sys_plot_top, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        sys_plot_top_box.layout().addWidget(self.sysPlotTop)

        sys_plot_front_box = oasysgui.widgetBox(tab_sys_plot_front, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        sys_plot_front_box.layout().addWidget(self.sysPlotFront)

        mir_box = oasysgui.widgetBox(tab_mir, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        mir_box.layout().addWidget(self.mirInfo)

        source_box = oasysgui.widgetBox(tab_sou, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        source_box.layout().addWidget(self.sourceInfo)

        syned_box = oasysgui.widgetBox(tab_syned, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        syned_box.layout().addWidget(self.synedInfo)

        syned_json_box = oasysgui.widgetBox(tab_syned_json, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        syned_json_box.layout().addWidget(self.synedJson)

        dist_box = oasysgui.widgetBox(tab_dis, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        dist_box.layout().addWidget(self.distancesSummary)

        # # script
        # self.shadow4_script = PythonScript()
        # script_box = gui.widgetBox(tab_scr, "Python script", addSpace=True, orientation="horizontal")
        # script_box.layout().addWidget(self.shadow4_script)
        # # self.shadow4_script.code_area.setFixedHeight(400)
        #
        #
        # console
        # console_box = oasysgui.widgetBox(script_box, "", addSpace=True, orientation="vertical",
        #                                   height=150, width=self.WIDGET_WIDTH - 80)
        # self.console = PythonConsole(self.__dict__, self)
        # console_box.layout().addWidget(self.console)
        #
        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.WIDGET_HEIGHT - 80)
        out_box.layout().addWidget(self.shadow_output)

        self.refresh()

    def set_shadow_data(self, shadow_data : ShadowData):
        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_empty_beam(shadow_data.beam):
                self.input_data = shadow_data
                self.refresh()
            else:
                MessageDialog.message(self, "Data not displayable: bad content", "Error", "critical")

    def refresh(self):

        self.fluxPower.setText("")
        self.sysInfo.setText("")
        self.mirInfo.setText("")
        self.sourceInfo.setText("")
        self.distancesSummary.setText("")
        self.synedJson.setText("")
        self.synedInfo.setText("")

        # self.shadow4_script.set_code("#")

        if self.input_data is None: return

        try:
            self.fluxPower.append(flux_summary(self.input_data.beamline))
        except:
            self.fluxPower.append("error in creating fluxPower")

        try:
            self.sysInfo.append(self.input_data.beamline.sysinfo())
        except:
            self.sysInfo.append("error in creating sysInfo")

        try:
            self.mirInfo.append(self.input_data.beamline.oeinfo())
        except:
            self.mirInfo.append("error in creating mirInfo")

        try:
            self.sourceInfo.append( self.input_data.beamline.sourcinfo())
        except:
            self.sourceInfo.append("error in creating xsourceInfoxx")

        try:
            self.synedInfo.append(self.input_data.beamline.info())
        except:
            self.synedInfo.append("error in creating synedInfo")

        try:
            self.synedJson.append(self.input_data.beamline.to_json())
        except:
            self.synedJson.append("error in creating json dump")

        try:
            self.distancesSummary.append(self.input_data.beamline.distances_summary())
        except:
            self.distancesSummary.append("error in creating xxdistancesSummaryx")

        try:
            self.sysplots()
        except:
            self.outputs.append("error in creating sysplots")

    def sysplots(self):
        try:
            status = 0
            dic = self.input_data.beamline.syspositions()

            status = 1
            self.sysPlotSide.addCurve(dic["optical_axis_y"], dic["optical_axis_z"], symbol='o', replace=True)
            self.sysPlotSide.setGraphXLabel("Y [m]")
            self.sysPlotSide.setGraphYLabel("Z [m]")
            self.sysPlotSide.setGraphTitle("Side View of optical axis")
            self.sysPlotSide.replot()

            status = 2
            self.sysPlotTop.addCurve(dic["optical_axis_y"], dic["optical_axis_x"], symbol='o', replace=True)
            self.sysPlotTop.setGraphXLabel("Y [m]")
            self.sysPlotTop.setGraphYLabel("X [m]")
            self.sysPlotTop.setGraphTitle("Bottom View of optical axis")
            self.sysPlotTop.replot()

            status = 3
            self.sysPlotFront.addCurve(dic["optical_axis_x"], dic["optical_axis_z"], symbol='o', replace=True)
            self.sysPlotFront.setGraphXLabel("X [m]")
            self.sysPlotFront.setGraphYLabel("Z [m]")
            self.sysPlotFront.setGraphTitle("Front View of optical axis")
            self.sysPlotFront.replot()

            status = 4
        except:
            self.shadow_output.setText(
                "Problem in plotting SysPlot. status: %d\n" % status)


    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()


if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline

    beamline = S4Beamline()

    # electron beam
    from shadow4.sources.s4_electron_beam import S4ElectronBeam

    electron_beam = S4ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
    electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=4.36821e-06, sigma_xp=3.63641e-06, sigma_yp=1.37498e-06)

    # magnetic structure
    from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian

    source = S4UndulatorGaussian(
        period_length=0.042,  # syned Undulator parameter (length in m)
        number_of_periods=38.571,  # syned Undulator parameter
        photon_energy=15000.0,  # Photon energy (in eV)
        delta_e=2.0,  # Photon energy width (in eV)
        ng_e=100,  # Photon energy scan number of points
        flag_emittance=1,  # when sampling rays: Use emittance (0=No, 1=Yes)
        flag_energy_spread=0,  # when sampling rays: Use e- energy spread (0=No, 1=Yes)
        harmonic_number=1,  # harmonic number
        flag_autoset_flux_central_cone=0,  # value to set the flux peak
        flux_central_cone=10000000000.0,  # value to set the flux peak
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

    coordinates = ElementCoordinates(p=27.2, q=0, angle_radial=0, angle_azimuthal=0, angle_radial_out=3.14159)
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

    coordinates = ElementCoordinates(p=2.7, q=0, angle_radial=1.5638, angle_azimuthal=1.5708, angle_radial_out=1.5638)
    movements = None
    from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirrorElement

    beamline_element = S4PlaneMirrorElement(optical_element=optical_element, coordinates=coordinates,
                                            movements=movements, input_beam=beam)

    beam, mirr = beamline_element.trace_beam()

    beamline.append_beamline_element(beamline_element)

    # optical element number XX
    boundary_shape = None

    from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror

    optical_element = S4PlaneMirror(name='Plane Mirror', boundary_shape=boundary_shape,
                                    f_reflec=1, f_refl=5, file_refl='<none>', refraction_index=0.99999 + 0.001j,
                                    coating_material='Ni', coating_density=8.902, coating_roughness=0)

    from syned.beamline.element_coordinates import ElementCoordinates

    coordinates = ElementCoordinates(p=0.825, q=0, angle_radial=1.5638, angle_azimuthal=3.14159,
                                     angle_radial_out=1.5638)
    movements = None
    from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirrorElement

    beamline_element = S4PlaneMirrorElement(optical_element=optical_element, coordinates=coordinates,
                                            movements=movements, input_beam=beam)

    beam, mirr = beamline_element.trace_beam()

    beamline.append_beamline_element(beamline_element)

    # optical element number XX

    from shadow4.beamline.optical_elements.ideal_elements.s4_empty import S4Empty

    optical_element = S4Empty(name='Empty Element')

    from syned.beamline.element_coordinates import ElementCoordinates

    coordinates = ElementCoordinates(p=0, q=0, angle_radial=0, angle_azimuthal=4.71239, angle_radial_out=3.14159)
    from shadow4.beamline.optical_elements.ideal_elements.s4_empty import S4EmptyElement

    beamline_element = S4EmptyElement(optical_element=optical_element, coordinates=coordinates, input_beam=beam)

    beam, mirr = beamline_element.trace_beam()

    beamline.append_beamline_element(beamline_element)

    # optical element number XX
    from syned.beamline.shape import Rectangle

    boundary_shape = Rectangle(x_left=-0.0015, x_right=0.0015, y_bottom=-0.0015, y_top=0.0015)

    from shadow4.beamline.optical_elements.absorbers.s4_screen import S4Screen

    optical_element = S4Screen(name='Generic Beam Screen/Slit/Stopper/Attenuator', boundary_shape=boundary_shape,
                               i_abs=0,  # 0=No, 1=prerefl file_abs, 2=xraylib, 3=dabax
                               i_stop=0, thick=0, file_abs='<specify file name>', material='Au', density=19.3)

    from syned.beamline.element_coordinates import ElementCoordinates

    coordinates = ElementCoordinates(p=5.475, q=0, angle_radial=0, angle_azimuthal=0, angle_radial_out=3.14159)
    from shadow4.beamline.optical_elements.absorbers.s4_screen import S4ScreenElement

    beamline_element = S4ScreenElement(optical_element=optical_element, coordinates=coordinates, input_beam=beam)

    beam, footprint = beamline_element.trace_beam()

    beamline.append_beamline_element(beamline_element)


###################################



    # test plot
    if False:
        from srxraylib.plot.gol import plot_scatter

        # plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1),
        #              title='(Intensity,Photon Energy)', plot_histograms=0)
        plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')

    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWInfo()
    ow.set_shadow_data(ShadowData(beam=beam, footprint=footprint, number_of_rays=0, beamline=beamline))
    ow.show()
    a.exec_()
