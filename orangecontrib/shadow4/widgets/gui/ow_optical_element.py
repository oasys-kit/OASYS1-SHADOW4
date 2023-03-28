#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------- #
# Copyright (c) 2022, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2022. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# ----------------------------------------------------------------------- #

import numpy
import sys, os

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5 import QtWidgets

from orangewidget import widget
from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import EmittingStream, read_surface_file

from syned.widget.widget_decorator import WidgetDecorator

from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.shape import Rectangle
from syned.beamline.shape import Ellipse

from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
from orangecontrib.shadow4.util.shadow_objects import ShadowData
from orangecontrib.shadow4.util.shadow_util import ShadowCongruence

from orangecanvas.resources import icon_loader
from orangecanvas.scheme.node import SchemeNode


class OWOpticalElement(GenericElement, WidgetDecorator):
    inputs = [("Shadow Data", ShadowData, "set_shadow_data")]
    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Shadow Data",
                "type":ShadowData,
                "doc":"",}]

    #########################################################
    # Position
    #########################################################
    source_plane_distance           = Setting(1.0)
    image_plane_distance            = Setting(1.0)
    angles_respect_to               = Setting(0)
    incidence_angle_deg             = Setting(88.8)
    incidence_angle_mrad            = Setting(0.0)
    reflection_angle_deg            = Setting(85.0)
    reflection_angle_mrad           = Setting(0.0)
    oe_orientation_angle            = Setting(1)
    oe_orientation_angle_user_value = Setting(0.0)


    def __init__(self):
        super().__init__()

        #
        # main buttons
        #
        self.runaction = widget.OWAction("Run Shadow4/Trace", self)
        self.runaction.triggered.connect(self.run_shadow4)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run shadow4/trace", callback=self.run_shadow4)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        #
        # tabs
        #
        self.tabs_control_area = oasysgui.tabWidget(self.controlArea)
        self.tabs_control_area.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_control_area.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_position          = oasysgui.createTabPage(self.tabs_control_area, "Position")           # to be populated
        self.tab_basic_settings    = oasysgui.createTabPage(self.tabs_control_area, "Basic Settings")
        self.tab_advanced_settings = oasysgui.createTabPage(self.tabs_control_area, "Advanced Settings")

        self.tabs_basic_settings   = oasysgui.tabWidget(self.tab_basic_settings)
        basic_setting_subtabs      = self.create_basic_settings_subtabs(self.tabs_basic_settings)

        self.tabs_advanced_settings   = oasysgui.tabWidget(self.tab_advanced_settings)

        advanced_setting_subtabs = self.create_advanced_settings_subtabs(self.tabs_advanced_settings)
        subtab_oe_movement       = oasysgui.createTabPage(self.tabs_advanced_settings, "O.E. Movement")  # to be populated

        #########################################################
        # Position
        #########################################################
        self.populate_tab_position(self.tab_position)

        #########################################################
        # Basic Settings
        #########################################################

        self.populate_basic_setting_subtabs(basic_setting_subtabs)

        #########################################################
        # Advanced Settings
        #########################################################
        self.populate_advanced_setting_subtabs(advanced_setting_subtabs)

        self.populate_tab_oe_movement(subtab_oe_movement)

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def create_basic_settings_subtabs(self, tabs_basic_settings): return None
    def create_advanced_settings_subtabs(self, tabs_advanced_settings): return None
    def populate_basic_setting_subtabs(self, basic_setting_subtabs): pass
    def populate_advanced_setting_subtabs(self, advanced_setting_subtabs): pass

    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="image_plane_distance")

        gui.comboBox(self.orientation_box, self, "angles_respect_to", label="Angles in [deg] with respect to the",
                     labelWidth=250, items=["Normal", "Surface"], callback=self.set_angles_respect_to,
                     sendSelectedValue=False, orientation="horizontal", tooltip="angles_respect_to")

        self.incidence_angle_deg_le = oasysgui.lineEdit(self.orientation_box, self, "incidence_angle_deg",
                                                        "Incident Angle\nwith respect to the Normal [deg]",
                                                        labelWidth=220, callback=self.calculate_incidence_angle_mrad,
                                                        valueType=float, orientation="horizontal", tooltip="incidence_angle_deg")
        self.incidence_angle_rad_le = oasysgui.lineEdit(self.orientation_box, self, "incidence_angle_mrad",
                                                        "Incident Angle\nwith respect to the surface [mrad]",
                                                        labelWidth=220, callback=self.calculate_incidence_angle_deg,
                                                        valueType=float, orientation="horizontal", tooltip="incidence_angle_mrad")
        self.reflection_angle_deg_le = oasysgui.lineEdit(self.orientation_box, self, "reflection_angle_deg",
                                                         "Reflection Angle\nwith respect to the Normal [deg]",
                                                         labelWidth=220, callback=self.calculate_reflection_angle_mrad,
                                                         valueType=float, orientation="horizontal", tooltip="reflection_angle_deg")
        self.reflection_angle_rad_le = oasysgui.lineEdit(self.orientation_box, self, "reflection_angle_mrad",
                                                         "Reflection Angle\nwith respect to the surface [mrad]",
                                                         labelWidth=220, callback=self.calculate_reflection_angle_deg,
                                                         valueType=float, orientation="horizontal", tooltip="reflection_angle_mrad")

        self.set_angles_respect_to()

        self.calculate_incidence_angle_mrad()
        self.calculate_reflection_angle_mrad()

        if True: # self.graphical_options.is_mirror:
            self.reflection_angle_deg_le.setEnabled(False)
            self.reflection_angle_rad_le.setEnabled(False)

        gui.comboBox(self.orientation_box, self, "oe_orientation_angle", label="O.E. Orientation Angle [deg]",
                     labelWidth=390,
                     items=[0, 90, 180, 270, "Other value..."],
                     valueType=float,
                     sendSelectedValue=False, orientation="horizontal", callback=self.oe_orientation_angle_user,
                     tooltip="oe_orientation_angle" )
        self.oe_orientation_angle_user_value_le = oasysgui.widgetBox(self.orientation_box, "", addSpace=False,
                                                                         orientation="vertical")
        oasysgui.lineEdit(self.oe_orientation_angle_user_value_le, self, "oe_orientation_angle_user_value",
                          "O.E. Orientation Angle [deg]",
                          labelWidth=220,
                          valueType=float, orientation="horizontal", tooltip="oe_orientation_angle_user_value")

        self.oe_orientation_angle_user()

    def populate_tab_oe_movement(self, subtab_oe_movement):
        box = oasysgui.widgetBox(subtab_oe_movement, "Not yet implemented", addSpace=True, orientation="vertical")

    #########################################################
    # Position Methods
    #########################################################
    def set_angles_respect_to(self):
        label_1 = self.incidence_angle_deg_le.parent().layout().itemAt(0).widget()
        label_2 = self.reflection_angle_deg_le.parent().layout().itemAt(0).widget()

        if self.angles_respect_to == 0:
            label_1.setText("Incident Angle\nwith respect to the normal [deg]")
            label_2.setText("Reflection Angle\nwith respect to the normal [deg]")
        else:
            label_1.setText("Incident Angle\nwith respect to the surface [deg]")
            label_2.setText("Reflection Angle\nwith respect to the surface [deg]")

        self.calculate_incidence_angle_mrad()
        self.calculate_reflection_angle_mrad()

    def calculate_incidence_angle_mrad(self):
        digits = 7

        if self.angles_respect_to == 0: self.incidence_angle_mrad = round(numpy.radians(90-self.incidence_angle_deg)*1000, digits)
        else:                           self.incidence_angle_mrad = round(numpy.radians(self.incidence_angle_deg)*1000, digits)

    def calculate_reflection_angle_mrad(self):
        digits = 7
        if self.angles_respect_to == 0: self.reflection_angle_mrad = round(numpy.radians(90 - self.reflection_angle_deg)*1000, digits)
        else:                           self.reflection_angle_mrad = round(numpy.radians(self.reflection_angle_deg)*1000, digits)

    def calculate_incidence_angle_deg(self):
        digits = 10
        if self.angles_respect_to == 0: self.incidence_angle_deg = round(numpy.degrees(0.5 * numpy.pi - (self.incidence_angle_mrad / 1000)), digits)
        else:                           self.incidence_angle_deg = round(numpy.degrees(self.incidence_angle_mrad / 1000), digits)

    def calculate_reflection_angle_deg(self):
        digits = 10

        if self.angles_respect_to == 0: self.reflection_angle_deg = round(numpy.degrees(0.5*numpy.pi-(self.reflection_angle_mrad/1000)), digits)
        else:                           self.reflection_angle_deg = round(numpy.degrees(self.reflection_angle_mrad/1000), digits)

    def oe_orientation_angle_user(self):
        if self.oe_orientation_angle < 4: self.oe_orientation_angle_user_value_le.setVisible(False)
        else:                             self.oe_orientation_angle_user_value_le.setVisible(True)

    def get_oe_orientation_angle(self):
        if self.oe_orientation_angle == 0:   return 0.0
        elif self.oe_orientation_angle == 1: return 90.0
        elif self.oe_orientation_angle == 2: return 180.0
        elif self.oe_orientation_angle == 3: return 270.0
        elif self.oe_orientation_angle == 4: return self.oe_orientation_angle_user_value