import sys
import time
import numpy

from orangecontrib.shadow4.widgets.gui.ow_electron_beam import OWElectronBeam
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D, plot_data2D, plot_data3D
from orangecontrib.shadow4.util.shadow4_objects import ShadowData

from oasys.widgets import gui as oasysgui

from oasys.util.oasys_util import EmittingStream

from syned.beamline.beamline import Beamline
from syned.storage_ring.magnetic_structures.insertion_device import InsertionDevice
from syned.widget.widget_decorator import WidgetDecorator

from orangewidget import gui as orangegui
from orangewidget.settings import Setting


from shadow4.sources.undulator.s4_undulator import S4Undulator
from shadow4.sources.undulator.s4_undulator_light_source import S4UndulatorLightSource

from shadow4.beamline.s4_beamline import S4Beamline

class OWUndulator(OWElectronBeam, WidgetDecorator):

    name = "Undulator Light Source"
    description = "Undulator Light Source"
    icon = "icons/undulator.png"
    priority = 50

    inputs = []
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Shadow Data",
                "type":ShadowData,
                "doc":"",}]

    # undulator parameters
    K_vertical = Setting(0.25)  # syned Undulator parameter
    period_length = Setting(0.032)  # syned Undulator parameter
    number_of_periods = Setting(50)  # syned Undulator parameter

    # photon energy
    set_at_resonance = Setting(0)
    is_monochromatic = Setting(1)
    emin = Setting(10490.0)  # Photon energy scan from energy (in eV)
    emax = Setting(10510.0)  # Photon energy scan to energy (in eV)
    photon_energy = Setting(10500.0)
    harmonic = Setting(1.0)
    delta_e = Setting(1000.0)

    maxangle = Setting(0.015)  # Maximum radiation semiaperture in RADIANS


    # other parameters
    ng_e = Setting(3)  # Photon energy scan number of points
    ng_t = Setting(100)  # Number of points in angle theta
    ng_p = Setting(11)  # Number of points in angle phi
    ng_j = Setting(20)  # Number of points in electron trajectory (per period) for internal calculation only
    code_undul_phot = Setting(0) # "internal",  # internal, pysru, srw
    flag_emittance = Setting(0)  # when sampling rays: Use emittance (0=No, 1=Yes)
    flag_size = Setting(2)  # when sampling rays: 0=point,1=Gaussian,2=FT(Divergences)

    # sampling rays
    number_of_rays = Setting(500)
    seed = Setting(5676561)


    plot_undulator_graph = 1

    beam_out = None
    lightsource = None # store lightsource after calculation


    def __init__(self):
        super().__init__()

        tab_undulator = oasysgui.createTabPage(self.tabs_control_area, "Undulator Setting")

        # undulator parameters box
        left_box_3 = oasysgui.widgetBox(tab_undulator, "Undulator Parameters", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_3, self, "K_vertical", "K value", labelWidth=260, tooltip="K_vertical", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "period_length", "ID period [m] [m]", labelWidth=260, tooltip="period_length", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "number_of_periods", "Number of Periods", labelWidth=260, tooltip="number_of_periods", valueType=int, orientation="horizontal")



        # # photon energy Box
        # left_box_10 = oasysgui.widgetBox(tab_undulator, "Sampling intervals", addSpace=False, orientation="vertical")
        # oasysgui.lineEdit(left_box_10, self, "emin", "Min photon energy [eV]", labelWidth=260, tooltip="emin", valueType=float, orientation="horizontal")
        # oasysgui.lineEdit(left_box_10, self, "emax", "Max photon energy [eV]", labelWidth=260, tooltip="emax", valueType=float, orientation="horizontal")
        # oasysgui.lineEdit(left_box_10, self, "maxangle", "Max elevation angle for radiation theta [rad]", labelWidth=300, tooltip="maxangle", valueType=float, orientation="horizontal")

        # NEW photon energy box
        left_box_10 = oasysgui.widgetBox(tab_undulator, "Photon energy, angle acceptance", addSpace=False, orientation="vertical")
        orangegui.comboBox(left_box_10, self, "set_at_resonance",
                     label="Set photon energy", addSpace=False, tooltip="emin",
                    items=['User defined', 'Set to resonance'],
                    valueType=int, orientation="horizontal", labelWidth=250, callback=self.set_visibility)

        orangegui.comboBox(left_box_10, self, "is_monochromatic",
                     label="Mono/polychromatic", addSpace=False, tooltip="emin",
                    items=['Polychromatic', 'Monochromatic',],
                    valueType=int, orientation="horizontal", labelWidth=250, callback=self.set_visibility)

        self.box_photon_energy_min_max = oasysgui.widgetBox(left_box_10)
        oasysgui.lineEdit(self.box_photon_energy_min_max, self, "emin", "Min photon energy [eV]", labelWidth=260, tooltip="emin", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_photon_energy_min_max, self, "emax", "Max photon energy [eV]", labelWidth=260, tooltip="emax", valueType=float, orientation="horizontal")

        self.box_photon_energy_center = oasysgui.widgetBox(left_box_10)
        oasysgui.lineEdit(self.box_photon_energy_center, self, "photon_energy", "Photon energy [eV]",
                        tooltip="Photon energy [eV]", labelWidth=250, valueType=float, orientation="horizontal")

        self.box_photon_energy_harmonic = oasysgui.widgetBox(left_box_10)
        oasysgui.lineEdit(self.box_photon_energy_harmonic, self, "harmonic", "Photon energy [N x Resonance]; N: ",
                        tooltip="harmonic", labelWidth=250, valueType=float, orientation="horizontal")

        self.box_photon_energy_width = oasysgui.widgetBox(left_box_10)
        oasysgui.lineEdit(self.box_photon_energy_width, self, "delta_e", "Photon energy width [eV] (0=monochr.)",
                          tooltip="delta_e", labelWidth=250, valueType=float, orientation="horizontal")

        self.box_maxangle = oasysgui.widgetBox(left_box_10)
        oasysgui.lineEdit(self.box_maxangle, self, "maxangle", "Max elevation angle for radiation theta [rad]", labelWidth=300, tooltip="maxangle", valueType=float, orientation="horizontal")




        #
        # self.set_UseResonance()


        #self.box_photon_energy.setEnabled(False)
        #
        # oasysgui.lineEdit(left_box_4, self, "delta_e", "Photon energy width [eV] (0=monochr.)", tooltip="Photon energy interval [eV] (0=monochromatic)", labelWidth=250, valueType=float, orientation="horizontal")




        # sampling
        left_box_12 = oasysgui.widgetBox(tab_undulator, "Sampling rays", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_12, self, "number_of_rays", "Number of rays", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_12, self, "seed", "Seed", tooltip="Seed (0=clock)", labelWidth=250, valueType=int, orientation="horizontal")

        # advanced settings
        tab_advanced = oasysgui.createTabPage(self.tabs_control_area, "Advanced Setting")
        left_box_11 = oasysgui.widgetBox(tab_advanced, "Advanced Setting", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_11, self, "ng_e", "Points in Photon energy (if polychromatic)", tooltip="ng_e", labelWidth=300, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "ng_t", "Points in theta [elevation]", tooltip="ng_t", labelWidth=300, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "ng_p", "Points in phi [azimuthal]", tooltip="ng_p", labelWidth=300, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "ng_j", "Points in electron trajectory (per period)", tooltip="ng_j", labelWidth=300, valueType=int, orientation="horizontal")
        orangegui.comboBox(left_box_11, self, "code_undul_phot", label="Use code for ",
                           items=["internal", "pysru", "srw"], labelWidth=260, orientation="horizontal")
        orangegui.comboBox(left_box_11, self, "flag_size", label="Size sampling in real space",
                           items=["point", "Gaussian", "FT(Divergences)"], labelWidth=260, orientation="horizontal")



        # undulator plots
        self.add_specific_undulator_plots()

        self.set_visibility()

        orangegui.rubber(self.controlArea)


    def add_specific_undulator_plots(self):

        undulator_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

        self.main_tabs.insertTab(1, undulator_plot_tab, "Undulator Plots")

        view_box = oasysgui.widgetBox(undulator_plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.undulator_view_type_combo = orangegui.comboBox(view_box_1, self,
                                            "plot_undulator_graph",
                                                          label="Plot Graphs?",
                                                          labelWidth=220,
                                                          items=["No", "Yes"],
                                                          callback=self.refresh_specific_undulator_plots,
                                                          sendSelectedValue=False,
                                                          orientation="horizontal")

        self.undulator_tab = []
        self.undulator_tabs = oasysgui.tabWidget(undulator_plot_tab)

        current_tab = self.undulator_tabs.currentIndex()

        size = len(self.undulator_tab)
        indexes = range(0, size)
        for index in indexes:
            self.undulator_tabs.removeTab(size-1-index)

        self.undulator_tab = [
            orangegui.createTabPage(self.undulator_tabs, "Radiation (polar)"),
            orangegui.createTabPage(self.undulator_tabs, "Polarization (polar)"),
            orangegui.createTabPage(self.undulator_tabs, "Radiation (interpolated)"),
            orangegui.createTabPage(self.undulator_tabs, "Photon source size"),
            orangegui.createTabPage(self.undulator_tabs, "Power Density (interpolated)"),
            orangegui.createTabPage(self.undulator_tabs, "Flux spectrum"),
            orangegui.createTabPage(self.undulator_tabs, "Spectral Power"),
            orangegui.createTabPage(self.undulator_tabs, "e trajectory"),
            orangegui.createTabPage(self.undulator_tabs, "e velocity"),
        ]

        self.undulator_plot_canvas = [None, None, None, None, None, None, None, None, None,]

        for tab in self.undulator_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)
        # self.undulator_plot_canvas = [None, None, None, None, None, None]

        self.undulator_tabs.setCurrentIndex(current_tab)



    def set_visibility(self):
        self.box_photon_energy_min_max.setVisible( self.set_at_resonance == 0 and self.is_monochromatic == 0)
        self.box_photon_energy_center.setVisible(  self.set_at_resonance == 0 and self.is_monochromatic == 1)
        self.box_photon_energy_width.setVisible(   self.set_at_resonance == 1 and self.is_monochromatic == 0)
        self.box_photon_energy_harmonic.setVisible(self.set_at_resonance == 1)
        self.box_maxangle.setVisible(              self.set_at_resonance == 0)

        # self.box_harmonic.setVisible(self.set_at_resonance == 1)
        #
        # orangegui.comboBox(left_box_10, self, "set_at_resonance",
        #                    label="Set photon energy", addSpace=False, tooltip="emin",
        #                    items=['User defined', 'Set to resonance'],
        #                    valueType=int, orientation="horizontal", labelWidth=250, callback=self.set_visibility)
        #
        # orangegui.comboBox(left_box_10, self, "is_monochromatic",
        #                    label="Mono/polychromatic", addSpace=False, tooltip="emin",
        #                    items=['Monochromatic', 'Polychromatic'],
        #                    valueType=int, orientation="horizontal", labelWidth=250, callback=self.set_visibility)
        #
        # self.box_photon_energy_min_max = oasysgui.widgetBox(left_box_10)
        # oasysgui.lineEdit(self.box_photon_energy_min_max, self, "emin", "Min photon energy [eV]", labelWidth=260,
        #                   tooltip="emin", valueType=float, orientation="horizontal")
        # oasysgui.lineEdit(self.box_photon_energy_min_max, self, "emax", "Max photon energy [eV]", labelWidth=260,
        #                   tooltip="emax", valueType=float, orientation="horizontal")
        #
        # self.box_photon_energy_center = oasysgui.widgetBox(left_box_10)
        # oasysgui.lineEdit(self.box_photon_energy_center, self, "photon_energy", "Photon energy [eV]",
        #                   tooltip="Photon energy [eV]", labelWidth=250, valueType=float, orientation="horizontal")
        #
        # self.box_photon_energy_width = oasysgui.widgetBox(left_box_10)
        # oasysgui.lineEdit(self.box_photon_energy_width, self, "delta_e", "Photon energy width [eV] (0=monochr.)",
        #                   tooltip="delta_e", labelWidth=250, valueType=float, orientation="horizontal")
        #
        # self.box_photon_energy_harmonic = oasysgui.widgetBox(left_box_10)
        # oasysgui.lineEdit(self.box_harmonic, self, "harmonic", "Photon energy [N x Resonance]; N: ",
        #                   tooltip="harmonic", labelWidth=250, valueType=float, orientation="horizontal")
        #
        # self.box_maxangle = oasysgui.widgetBox(left_box_10)
        # oasysgui.lineEdit(self.box_photon_energy, self, "maxangle", "Max elevation angle for radiation theta [rad]",
        #                   labelWidth=300, tooltip="maxangle", valueType=float, orientation="horizontal")


        # self.box_maxangle = oasysgui.widgetBox(left_box_10)
        # self.conventional_sinusoidal_box.setVisible(self.magnetic_field_source == 0)
        # self.b_from_file_box.setVisible(self.magnetic_field_source == 1)
        # self.b_from_harmonics_box.setVisible(self.magnetic_field_source == 2)

    # def select_file_with_B_vs_Y(self):
    #     self.le_file_with_b_vs_y.setText(oasysgui.selectFileFromDialog(self, self.file_with_b_vs_y, "Open File With B vs Y"))
    #
    # def select_file_with_harmonics(self):
    #     self.le_file_with_harmonics.setText(oasysgui.selectFileFromDialog(self, self.file_with_harmonics, "Open File With Harmonics"))
    #
    # def set_shift_X_flag(self):
    #     self.shift_x_value_box.setVisible(self.shift_x_flag==5)
    #     self.shift_x_value_box_hidden.setVisible(self.shift_x_flag!=5)
    #
    # def set_shift_beta_X_flag(self):
    #     self.shift_betax_value_box.setVisible(self.shift_betax_flag==5)
    #     self.shift_betax_value_box_hidden.setVisible(self.shift_betax_flag!=5)

    def get_lightsource(self):
        # syned
        electron_beam = self.get_electron_beam()
        print("\n\n>>>>>> ElectronBeam info: ", electron_beam.info(), type(electron_beam))

        if self.type_of_properties == 3:
            flag_emittance = 0
        else:
            flag_emittance = 1

        # S4undulator
        code_undul_phot = ["internal", "pysru", "srw"][self.code_undul_phot]

        sourceundulator = S4Undulator(
            K_vertical=self.K_vertical,                # syned Undulator parameter
            period_length=self.period_length,          # syned Undulator parameter
            number_of_periods=self.number_of_periods,  # syned Undulator parameter
            emin=self.photon_energy if self.is_monochromatic else self.emin ,  # Photon energy scan from energy (in eV)
            emax=self.photon_energy if self.is_monochromatic else self.emax,  # Photon energy scan to energy (in eV)
            ng_e=self.ng_e,  # Photon energy scan number of points
            maxangle=self.maxangle,  # Maximum radiation semiaperture in RADIANS
            ng_t=self.ng_t,  # Number of points in angle theta
            ng_p=self.ng_p,  # Number of points in angle phi
            ng_j=self.ng_j,  # Number of points in electron trajectory (per period) for internal calculation only
            code_undul_phot=code_undul_phot,  # internal, pysru, srw
            flag_emittance=flag_emittance,  # when sampling rays: Use emittance (0=No, 1=Yes)
            flag_size=self.flag_size,  # when sampling rays: 0=point,1=Gaussian,2=FT(Divergences)
            )


        # S4undulatorLightSource
        lightsource = S4UndulatorLightSource(name='undulator',
                                           electron_beam=electron_beam,
                                           magnetic_structure=sourceundulator,
                                           nrays=self.number_of_rays,
                                           seed=self.seed)

        # reset energy after user choice
        if self.set_at_resonance:
            if self.is_monochromatic: lightsource.set_energy_monochromatic_at_resonance(harmonic_number=self.harmonic)
            else:                     lightsource.set_energy_at_resonance(harmonic_number=self.harmonic, delta_e=self.delta_e)


        print("\n\n>>>>>> S4undulatorLightSource info: ", lightsource.info())

        return lightsource


    def run_shadow4(self):

        self.lightsource = None # clean

        sys.stdout = EmittingStream(textWritten=self._write_stdout)

        self._set_plot_quality()

        self.progressBarInit()

        light_source = self.get_lightsource()

        #
        # script
        #
        script = light_source.to_python_code()
        script += "\n\n# test plot\nfrom srxraylib.plot.gol import plot_scatter"
        script += "\nrays = beam.get_rays()"
        script += "\nplot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 2], title='(X,Z) in microns')"


        self.shadow4_script.set_code(script)

        self.progressBarSet(5)
        #
        # run shadow4
        #
        t00 = time.time()
        print(">>>> starting calculation...")
        output_beam = light_source.get_beam()
        t11 = time.time() - t00
        print(">>>> time for %d rays: %f s, %f min, " % (self.number_of_rays, t11, t11 / 60))

        self.lightsource = light_source


        #
        # plots
        #
        self._plot_results(output_beam, None, progressBarValue=80)
        self.refresh_specific_undulator_plots()


        self.progressBarFinished()

        #
        # send beam
        #
        self.send("Shadow Data", ShadowData(beam=output_beam,
                                           number_of_rays=self.number_of_rays,
                                           beamline=S4Beamline(light_source=light_source)))

    # def plot_undulator_item(self, x, y, undulator_plot_slot_index, title="", xtitle="", ytitle=""):
    #     self.undulator_tab[undulator_plot_slot_index].layout().removeItem(self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0))
    #     plot_widget_id = plot_data1D(x.copy(), y.copy(), title=title, xtitle=xtitle, ytitle=ytitle, symbol='.')
    #     self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)

    def get_title_for_stack_view_flux(self, idx):
        # todo: improve
        # return "Units: Photons/s/eV/rad2; Photon energy index: %d"%(idx)
        # photon_energy = self.sourceundulator.get_result_photon_energy()
        photon_energy = self.lightsource.get_result_photon_energy()
        return "Units: Photons/s/eV/rad2; Photon energy: %8.3f eV"%(photon_energy[idx])

    def refresh_specific_undulator_plots(self):
        if self.lightsource is None: return

        if self.plot_undulator_graph == 0:
            for undulator_plot_slot_index in range(7):
                current_item = self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0)
                self.undulator_tab[undulator_plot_slot_index].layout().removeItem(current_item)
                plot_widget_id = oasysgui.QLabel() # TODO: is there a better way to clean this??????????????????????
                self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)
        else:
            is_monochromatic = self.lightsource.get_magnetic_structure().is_monochromatic()

            # radiation
            radiation, photon_energy, theta, phi = self.lightsource.get_radiation_polar()
            if is_monochromatic:
                self.plot_undulator_item2D(0, radiation[0], 1e6 * theta, phi,
                                           title="radiation (photons/s/eV/rad2)", xtitle="theta [urad]",
                                           ytitle="phi [rad]")
            else:
                self.plot_undulator_item3D(0, radiation, photon_energy, 1e6 * theta, phi,
                                           title="radiation (photons/s/eV/rad2)", xtitle="theta [urad]",
                                           ytitle="phi [rad]")
            # polarization
            polarization = self.lightsource.get_result_polarisation()
            if is_monochromatic:
                self.plot_undulator_item2D(1, polarization[0], 1e6 * theta, phi,
                                 title="polarization |Es|/(|Es|+|Ep|)", xtitle="theta [urad]", ytitle="phi [rad]")
            else:
                self.plot_undulator_item3D(1, polarization, photon_energy, 1e6 * theta, phi,
                                 title="polarization |Es|/(|Es|+|Ep|)", xtitle="theta [urad]", ytitle="phi [rad]")

            # radiation interpolated
            radiation_interpolated, photon_energy, vx, vz = self.lightsource.get_radiation_interpolated_cartesian(
                npointsx=100, npointsz=100, thetamax=None)
            if is_monochromatic:
                self.plot_undulator_item2D(2, radiation_interpolated[0], 1e6 * vx, 1e6 * vz,
                                 title="radiation", xtitle="vx [urad]", ytitle="vz [rad]")
            else:
                self.plot_undulator_item3D(2, radiation_interpolated, photon_energy, 1e6 * vx, 1e6 * vz,
                                 title="radiation", xtitle="vx [urad]", ytitle="vz [rad]")

            # backpropagated far field
            x, y = self.lightsource.get_photon_size_distribution()
            self.plot_undulator_item1D(3, x * 1e6, y,
                                       title="Photon emission size distribution", xtitle="Distance [um]",
                                       ytitle="Intensity [arbitrary units]")

            # power density
            intens_xy, vx, vz = self.lightsource.get_power_density_interpolated_cartesian()
            if is_monochromatic:
                title="power density W/mrad2/eV"
            else:
                title="power density W/mrad2"
            self.plot_undulator_item2D(4, intens_xy, 1e6 * vx, 1e6 * vz,
                             title=title, xtitle="vx [urad]", ytitle="vz [rad]")

            # spectra
            e, f, w = self.lightsource.calculate_spectrum()
            self.plot_undulator_item1D(5, e, f,
                                  title="Undulator spectrum", xtitle="Photon energy [eV]", ytitle=r"Photons/s/0.1%bw")

            self.plot_undulator_item1D(6, e, w,
                                  title="Undulator spectral power",
                                  xtitle="Photon energy [eV]", ytitle="Spectral power [W/eV]")

            # trajectory
            try:
                yy, xx, beta_x = self.lightsource.get_result_trajectory()
                self.plot_undulator_item1D(7, yy, xx,
                                      title="electron trajectory", xtitle="Y [m]", ytitle="X [m]", symbol='')

                self.plot_undulator_item1D(8, yy, beta_x,
                                      title="electron velocity", xtitle="Y [m]", ytitle="X [m]", symbol='')
            except:
                pass

            print("\n\n")
            # print("Total power (integral [sum] of spectral power) [W]: ",spectral_power.sum()*(photon_energy[1]-photon_energy[0]))
            print("Total power (integral [trapz] of spectral power) [W]: ",
                  numpy.trapz(w, photon_energy))
            print("Total number of photons (integral [trapz] of flux): ",
                  numpy.trapz(f / (1e-3 * photon_energy), photon_energy))
            print("\n\n")


            #
            # tabs_canvas_index += 1
            # self.plot_data2D(1e-6 * intens_xy, 1e6 * vx, 1e6 * vz,
            #                  tabs_canvas_index, plot_canvas_index,
            #                  title="power density W/mrad2", xtitle="vx [urad]", ytitle="vz [rad]")

            #     plot_data2D(radiation[0], 1e6 * theta, phi,
            #                      0, 0, title="radiation (photons/s/eV/rad2)",
            #                      xtitle="theta [urad]", ytitle="phi [rad]")
            #
            #     # tabs_canvas_index += 1
            #     # self.plot_data2D(polarization[0], 1e6 * theta, phi,
            #     #                  tabs_canvas_index, plot_canvas_index, title="polarization |Es|/(|Es|+|Ep|)",
            #     #                  xtitle="theta [urad]", ytitle="phi [rad]")
            #     #
            #     # tabs_canvas_index += 1
            #     # radiation_interpolated, photon_energy, vx, vz = self.sourceundulator.get_radiation_interpolated_cartesian()
            #     # self.plot_data2D(radiation_interpolated[0], 1e6 * vx, 1e6 * vz,
            #     #                  tabs_canvas_index, plot_canvas_index, title="radiation", xtitle="vx [urad]",
            #     #                  ytitle="vz [rad]")
            #     #
            #     # tabs_canvas_index += 1
            #     # x, y = self.sourceundulator.get_photon_size_distribution()
            #     # self.plot_data1D(x * 1e6, y,
            #     #                  tabs_canvas_index, plot_canvas_index,
            #     #                  title="Photon emission size distribution", xtitle="Distance [um]",
            #     #                  ytitle="Intensity [arbitrary units]")
            #

            # tabs_canvas_index += 1
            # self.plot_data3D(polarization, photon_energy, 1e6 * theta, phi,
            #                  tabs_canvas_index, plot_canvas_index,
            #                  title="polarization |Es|/(|Es|+|Ep|)", xtitle="theta [urad]", ytitle="phi [rad]",
            #                  callback_for_title=self.get_title_for_stack_view_polarization)
            #
            # tabs_canvas_index += 1
            # radiation_interpolated, photon_energy, vx, vz = self.sourceundulator.get_radiation_interpolated_cartesian()
            # self.plot_data3D(radiation_interpolated, photon_energy, 1e6 * vx, 1e6 * vz,
            #                  tabs_canvas_index, plot_canvas_index,
            #                  title="radiation", xtitle="vx [urad]", ytitle="vz [rad]",
            #                  callback_for_title=self.get_title_for_stack_view_flux)
            #
            # tabs_canvas_index += 1
            # x, y = self.sourceundulator.get_photon_size_distribution()
            # self.plot_data1D(x * 1e6, y,
            #                  tabs_canvas_index, plot_canvas_index,
            #                  title="Photon emission size distribution", xtitle="Distance [um]",
            #                  ytitle="Intensity [arbitrary units]")
            #
            # if polychromatic, plot power density
            #

            # intens_xy, vx, vz = self.sourceundulator.get_power_density_interpolated_cartesian()
            #
            # tabs_canvas_index += 1
            # self.plot_data2D(1e-6 * intens_xy, 1e6 * vx, 1e6 * vz,
            #                  tabs_canvas_index, plot_canvas_index,
            #                  title="power density W/mrad2", xtitle="vx [urad]", ytitle="vz [rad]")
            #
            # #
            # # if polychromatic, plot flux(energy)
            # #
            #
            # flux, spectral_power, photon_energy = self.sourceundulator.get_flux_and_spectral_power()
            #
            # tabs_canvas_index += 1
            # self.plot_data1D(photon_energy, flux,
            #                  tabs_canvas_index, plot_canvas_index,
            #                  title="Flux", xtitle="Photon Energy [eV]", ytitle="Flux [photons/s/0.1%bw]")
            #
            # tabs_canvas_index += 1
            # self.plot_data1D(photon_energy, spectral_power,
            #                  tabs_canvas_index, plot_canvas_index,
            #                  title="Spectral Power", xtitle="Photon Energy [eV]", ytitle="Spectral Power [W/eV]")
            #
            # print("\n\n")
            # # print("Total power (integral [sum] of spectral power) [W]: ",spectral_power.sum()*(photon_energy[1]-photon_energy[0]))
            # print("Total power (integral [trapz] of spectral power) [W]: ",
            #       numpy.trapz(spectral_power, photon_energy))
            # print("Total number of photons (integral [trapz] of flux): ",
            #       numpy.trapz(flux / (1e-3 * photon_energy), photon_energy))
            # print("\n\n")

    # def XXXXXXXXXplot_undulator_results(self):
    #     if self.plot_aux_graph == 1:
    #         try:
    #
    #             radiation,photon_energy,theta,phi = self.sourceundulator.get_radiation_polar()
    #
    #             tabs_canvas_index = 0
    #             plot_canvas_index = 0
    #             polarization = self.sourceundulator.get_result_polarization()
    #
    #
    #             if self.delta_e == 0.0:
    #                 self.plot_data2D(radiation[0], 1e6*theta, phi,
    #                                  tabs_canvas_index, plot_canvas_index, title="radiation (photons/s/eV/rad2)", xtitle="theta [urad]", ytitle="phi [rad]")
    #
    #                 tabs_canvas_index += 1
    #                 self.plot_data2D(polarization[0], 1e6*theta, phi,
    #                                  tabs_canvas_index, plot_canvas_index, title="polarization |Es|/(|Es|+|Ep|)", xtitle="theta [urad]", ytitle="phi [rad]")
    #
    #                 tabs_canvas_index += 1
    #                 radiation_interpolated,photon_energy,vx,vz = self.sourceundulator.get_radiation_interpolated_cartesian()
    #                 self.plot_data2D(radiation_interpolated[0], 1e6*vx, 1e6*vz,
    #                                  tabs_canvas_index, plot_canvas_index, title="radiation", xtitle="vx [urad]", ytitle="vz [rad]")
    #
    #                 tabs_canvas_index += 1
    #                 x,y = self.sourceundulator.get_photon_size_distribution()
    #                 self.plot_data1D(x*1e6,y,
    #                                  tabs_canvas_index, plot_canvas_index,
    #                                  title="Photon emission size distribution", xtitle="Distance [um]", ytitle="Intensity [arbitrary units]")
    #
    #             else:
    #                 self.plot_data3D(radiation, photon_energy, 1e6*theta, phi,
    #                                  tabs_canvas_index, plot_canvas_index,
    #                                  title="radiation (photons/s/eV/rad2)", xtitle="theta [urad]", ytitle="phi [rad]",
    #                                  callback_for_title=self.get_title_for_stack_view_flux)
    #
    #                 tabs_canvas_index += 1
    #                 self.plot_data3D(polarization, photon_energy, 1e6*theta, phi,
    #                                  tabs_canvas_index, plot_canvas_index,
    #                                  title="polarization |Es|/(|Es|+|Ep|)", xtitle="theta [urad]", ytitle="phi [rad]",
    #                                  callback_for_title=self.get_title_for_stack_view_polarization)
    #
    #                 tabs_canvas_index += 1
    #                 radiation_interpolated,photon_energy,vx,vz = self.sourceundulator.get_radiation_interpolated_cartesian()
    #                 self.plot_data3D(radiation_interpolated, photon_energy, 1e6*vx, 1e6*vz,
    #                                  tabs_canvas_index, plot_canvas_index,
    #                                  title="radiation", xtitle="vx [urad]", ytitle="vz [rad]",
    #                                  callback_for_title=self.get_title_for_stack_view_flux)
    #
    #                 tabs_canvas_index += 1
    #                 x,y = self.sourceundulator.get_photon_size_distribution()
    #                 self.plot_data1D(x*1e6,y,
    #                                  tabs_canvas_index, plot_canvas_index,
    #                                  title="Photon emission size distribution", xtitle="Distance [um]", ytitle="Intensity [arbitrary units]")
    #                 #
    #                 # if polychromatic, plot power density
    #                 #
    #
    #                 intens_xy,vx,vz = self.sourceundulator.get_power_density_interpolated_cartesian()
    #
    #                 tabs_canvas_index += 1
    #                 self.plot_data2D(1e-6*intens_xy,1e6*vx,1e6*vz,
    #                                  tabs_canvas_index, plot_canvas_index,
    #                                  title="power density W/mrad2", xtitle="vx [urad]", ytitle="vz [rad]")
    #
    #
    #                 #
    #                 # if polychromatic, plot flux(energy)
    #                 #
    #
    #
    #                 flux,spectral_power,photon_energy = self.sourceundulator.get_flux_and_spectral_power()
    #
    #                 tabs_canvas_index += 1
    #                 self.plot_data1D(photon_energy,flux,
    #                                  tabs_canvas_index, plot_canvas_index,
    #                                  title="Flux", xtitle="Photon Energy [eV]", ytitle="Flux [photons/s/0.1%bw]")
    #
    #
    #                 tabs_canvas_index += 1
    #                 self.plot_data1D(photon_energy,spectral_power,
    #                                  tabs_canvas_index, plot_canvas_index,
    #                                  title="Spectral Power", xtitle="Photon Energy [eV]", ytitle="Spectral Power [W/eV]")
    #
    #                 print("\n\n")
    #                 # print("Total power (integral [sum] of spectral power) [W]: ",spectral_power.sum()*(photon_energy[1]-photon_energy[0]))
    #                 print("Total power (integral [trapz] of spectral power) [W]: ",numpy.trapz(spectral_power,photon_energy))
    #                 print("Total number of photons (integral [trapz] of flux): ",numpy.trapz(flux/(1e-3*photon_energy),photon_energy))
    #                 print("\n\n")
    #
    #
    #
    #
    #         except Exception as exception:
    #             QtWidgets.QMessageBox.critical(self, "Error",
    #                                        str(exception),
    #                 QtWidgets.QMessageBox.Ok)


    def plot_undulator_item1D(self, undulator_plot_slot_index, x, y, title="", xtitle="", ytitle="", symbol='.'):
        self.undulator_tab[undulator_plot_slot_index].layout().removeItem(self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_data1D(x.copy(), y.copy(), title=title, xtitle=xtitle, ytitle=ytitle, symbol=symbol)
        self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)

    def plot_undulator_item2D(self, undulator_plot_slot_index, data2D, dataX, dataY, title="", xtitle ="", ytitle=""):
        self.undulator_tab[undulator_plot_slot_index].layout().removeItem(self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_data2D(data2D, dataX, dataY, title=title, xtitle=xtitle, ytitle=ytitle)
        self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)

    def plot_undulator_item3D(self, undulator_plot_slot_index, data3D, dataE, dataX, dataY,
                            title ="", xtitle ="", ytitle = ""):
        self.undulator_tab[undulator_plot_slot_index].layout().removeItem(self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_data3D(data3D, dataE, dataX, dataY,
                                     title=title, xtitle=xtitle, ytitle=ytitle,
                                     callback_for_title=self.get_title_for_stack_view_flux)
        self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)

    def receive_syned_data(self, data):
        sys.stdout = EmittingStream(textWritten=self._write_stdout)
        if data is not None:
            if isinstance(data, Beamline):
                if not data.get_light_source() is None:
                    if isinstance(data.get_light_source().get_magnetic_structure(), InsertionDevice):
                        print(data.get_light_source().get_magnetic_structure(), InsertionDevice)
                        light_source = data.get_light_source()

                        self.set_visibility()

                        self.populate_fields_from_electron_beam(light_source.get_electron_beam())
                        w = light_source.get_magnetic_structure()
                        self.k_value = w.K_vertical()
                        self.id_period = w.period_length()
                        self.number_of_periods = w.number_of_periods()

                    else:
                        raise ValueError("Syned light source not congruent")
                else:
                    raise ValueError("Syned data not correct: light source not present")
            else:
                raise ValueError("Syned data not correct")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWUndulator()
    ow.show()
    a.exec_()

