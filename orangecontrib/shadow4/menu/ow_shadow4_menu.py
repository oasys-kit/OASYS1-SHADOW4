__author__ = 'L. Rebuffi'

import webbrowser
from oasys.menus.menu import OMenu

from orangecontrib.shadow4.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
from orangecontrib.shadow4.widgets.tools.ow_plot_xy import PlotXY
from orangecontrib.shadow4.widgets.tools.ow_histogram import Histogram

from orangecontrib.shadow4.widgets.preprocessors.ow_bragg import OWBragg
from orangecontrib.shadow4.widgets.preprocessors.ow_prerefl import OWPrerefl
from orangecontrib.shadow4.widgets.preprocessors.vls_pgm_coefficients_calculator import OWVlsPgmCoefficientsCalculator

class Shadow4Menu(OMenu):
    def __init__(self):
        super().__init__(name="Shadow4")

        self.openContainer()
        self.addContainer("Plotting")
        self.addSubMenu("Select Detailed Plots on all Source and O.E. widgets")
        self.addSubMenu("Select Preview Plots on all Source and O.E. widgets")
        self.addSubMenu("Select No Plots on all Source and O.E. widgets")
        self.addSeparator()
        self.addSubMenu("Enable all the Plotting widgets")
        self.addSubMenu("Disable all the Plotting widgets")
        self.addSeparator()
        self.addSubMenu("Clear all the cumulated plots")
        self.closeContainer()
        self.addSubMenu("Execute all the Preprocessor widgets")
        self.addSeparator()
        self.addSubMenu("Shadow4 Documentation")

    def __set_plot_visibility(self, vt, pg):
        try:
            for node in self.canvas_main_window.current_document().scheme().nodes:
                widget = self.canvas_main_window.current_document().scheme().widget_for_node(node)

                if isinstance(widget, GenericElement):
                    if hasattr(widget, "view_type") and hasattr(widget, "_set_plot_quality"):
                        widget.view_type = vt
                        widget._set_plot_quality()

                    if hasattr(widget, "plot_undulator_graph") and hasattr(widget, "refresh_specific_undulator_plots"):
                        widget.plot_undulator_graph = pg
                        widget.refresh_specific_undulator_plots()
                    elif hasattr(widget, "plot_bm_graph") and hasattr(widget, "refresh_specific_bm_plots"):
                        widget.plot_bm_graph = pg
                        widget.refresh_specific_bm_plots()
                    elif hasattr(widget, "plot_wiggler_graph") and hasattr(widget, "refresh_specific_wiggler_plots"):
                        widget.plot_wiggler_graph = pg
                        widget.refresh_specific_wiggler_plots()

        except Exception as exception:
            super(Shadow4Menu, self).showCriticalMessage(message=exception.args[0])

    def executeAction_1(self, action): self.__set_plot_visibility(0, 1)

    def executeAction_2(self, action): self.__set_plot_visibility(1, 1)

    def executeAction_3(self, action): self.__set_plot_visibility(2, 0)

    def __set_preprocessor_enabled(self, enabled):
        try:
            for link in self.canvas_main_window.current_document().scheme().links:
                if link.enabled != enabled:
                    widget = self.canvas_main_window.current_document().scheme().widget_for_node(link.sink_node)
                    if isinstance(widget, (PlotXY, Histogram)): link.set_enabled(enabled)
        except Exception as exception:
            super(Shadow4Menu, self).showCriticalMessage(message=exception.args[0])

    #ENABLE PLOTS
    def executeAction_4(self, action): self.__set_preprocessor_enabled(True)

    def executeAction_5(self, action): self.__set_preprocessor_enabled(False)

    def executeAction_6(self, action):
        try:
            for node in self.canvas_main_window.current_document().scheme().nodes:
                widget = self.canvas_main_window.current_document().scheme().widget_for_node(node)

                if isinstance(widget, AutomaticElement) and hasattr(widget, "clear_results"):
                    widget.clear_results(interactive=False)
        except Exception as exception:
            super(Shadow4Menu, self).showCriticalMessage(message=exception.args[0])

    def executeAction_7(self, action):
        try:
            for node in self.canvas_main_window.current_document().scheme().nodes:
                widget = self.canvas_main_window.current_document().scheme().widget_for_node(node)
                if isinstance(widget, (OWBragg, OWVlsPgmCoefficientsCalculator, OWPrerefl)): widget.compute()
        except Exception as exception:
            super(Shadow4Menu, self).showCriticalMessage(message=exception.args[0])

    def executeAction_8(self, action):
        try:
            webbrowser.open("https://github.com/oasys-kit/shadow4")
        except Exception as exception:
            super(Shadow4Menu, self).showCriticalMessage(message=exception.args[0])

