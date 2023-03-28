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

from PyQt5 import QtWidgets

from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui

from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.shape import Rectangle
from syned.beamline.shape import Ellipse

from shadow4.beamline.optical_elements.absorbers.s4_screen import S4ScreenElement, S4Screen

from orangecontrib.shadow4.widgets.gui.ow_optical_element import OWOpticalElement, NO_FILE_SPECIFIED

from orangecanvas.resources import icon_loader
from orangecanvas.scheme.node import SchemeNode


class OWScreenSlits(OWOpticalElement):
    name        = "Generic Beam Stopper"
    description = "Shadow Screen/Slits"
    icon        = "icons/generic_beam_stopper.png"

    priority = 2.0

    aperturing           = Setting(0)
    open_slit_solid_stop = Setting(0)
    aperture_shape       = Setting(0)
    absorption           = Setting(0)
    slit_width_xaxis     = Setting(0.0)
    slit_height_zaxis    = Setting(0.0)
    slit_center_xaxis    = Setting(0.0)
    slit_center_zaxis    = Setting(0.0)
    thickness            = Setting(0.0)
    opt_const_file_name  = Setting(NO_FILE_SPECIFIED)


    input_data = None

    def createdFromNode(self, node):
        super(OWScreenSlits, self).createdFromNode(node)
        self.__change_icon_from_oe_type()

    def widgetNodeAdded(self, node_item : SchemeNode):
        super(OWScreenSlits, self).widgetNodeAdded(node_item)
        self.__change_icon_from_oe_type()

    def __change_icon_from_oe_type(self):
        try:
            title, icon = self.title_and_icon_for_oe

            node = self.getNode()
            node.description.icon = icon
            self.changeNodeIcon(icon_loader.from_description(node.description).get(node.description.icon))
            if node.title in self.oe_names: self.changeNodeTitle(title)
        except:
            pass

    @property
    def oe_names(self):
        return ["Generic Beam Stopper", "Screen", "Aperture", "Obstruction", "Absorber", "Aperture/Absorber", "Obstruction/Absorber"]

    @property
    def title_and_icon_for_oe(self):
        if self.absorption == 0:
            if self.aperturing == 0: return self.oe_names[1], "icons/screen.png"
            elif self.aperturing == 1:
                if self.open_slit_solid_stop == 0: return self.oe_names[2], "icons/aperture_only.png"
                else:                              return self.oe_names[3], "icons/obstruction_only.png"
        else:
            if self.aperturing == 0: return self.oe_names[4], "icons/absorber.png"
            elif self.aperturing == 1:
                if self.open_slit_solid_stop == 0: return self.oe_names[5], "icons/aperture_absorber.png"
                else:                              return self.oe_names[6], "icons/obstruction_absorber.png"

    def __init__(self):
        super().__init__()

    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="image_plane_distance")

    def create_basic_settings_subtabs(self, tabs_basic_settings):
        return oasysgui.createTabPage(tabs_basic_settings, "Beam Stopper Type")  # to be populated

    def populate_basic_setting_subtabs(self, basic_setting_subtabs):
        tab_beam_stopper_type = basic_setting_subtabs

        box_aperturing = oasysgui.widgetBox(tab_beam_stopper_type, "Screen/Slit Shape", addSpace=False, orientation="vertical", height=240)

        gui.comboBox(box_aperturing, self, "aperturing", label="Aperturing", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_aperturing, sendSelectedValue=False, orientation="horizontal")

        gui.separator(box_aperturing)

        self.box_aperturing_shape = oasysgui.widgetBox(box_aperturing, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.box_aperturing_shape, self, "open_slit_solid_stop", label="Open slit/Solid stop", labelWidth=260,
                     items=["aperture/slit", "obstruction/stop"],
                     callback=self.set_open_slit_solid_stop, sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.box_aperturing_shape, self, "aperture_shape", label="Aperture shape", labelWidth=260,
                     items=["Rectangular", "Ellipse"],
                     sendSelectedValue=False, orientation="horizontal")

        box_aperturing_shape = oasysgui.widgetBox(self.box_aperturing_shape, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(box_aperturing_shape, self, "slit_width_xaxis", "Slit width/x-axis   [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_aperturing_shape, self, "slit_height_zaxis", "Slit height/z-axis [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_aperturing_shape, self, "slit_center_xaxis", "Slit center/x-axis [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_aperturing_shape, self, "slit_center_zaxis", "Slit center/z-axis [m]", labelWidth=260, valueType=float, orientation="horizontal")

        box_absorption = oasysgui.widgetBox(tab_beam_stopper_type, "Absorption Parameters", addSpace=False, orientation="vertical", height=130)

        gui.comboBox(box_absorption, self, "absorption", label="Absorption", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_absorption, sendSelectedValue=False, orientation="horizontal")

        gui.separator(box_absorption)#, width=self.INNER_BOX_WIDTH_L0)

        self.box_absorption       = oasysgui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")
        #self.box_absorption_empty = oasysgui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.box_absorption, self, "thickness", "Thickness [m]", labelWidth=300, valueType=float, orientation="horizontal")

        file_box = oasysgui.widgetBox(self.box_absorption, "", addSpace=False, orientation="horizontal", height=25)

        self.le_opt_const_file_name = oasysgui.lineEdit(file_box, self, "opt_const_file_name", "Opt. const. file name", labelWidth=130, valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.select_opt_const_file_name)

        self.set_aperturing(is_init=True)
        self.set_absorption(is_init=True)

    def set_aperturing(self, is_init=False):
        self.box_aperturing_shape.setVisible(self.aperturing == 1)

        if not is_init: self.__change_icon_from_oe_type()

    def set_open_slit_solid_stop(self, is_init=False):
        if not is_init: self.__change_icon_from_oe_type()

    def set_absorption(self, is_init=False):
        #self.box_absorption_empty.setVisible(self.absorption == 0)
        self.box_absorption.setVisible(self.absorption == 1)

        if not is_init: self.__change_icon_from_oe_type()

    def select_opt_const_file_name(self):
        self.le_opt_const_file_name.setText(oasysgui.selectFileFromDialog(self, self.opt_const_file_name, "Open Opt. Const. File"))

    # ----------------------------------------------------
    # from OpticalElement

    def get_coordinates(self):
        return ElementCoordinates(
                p=self.source_plane_distance,
                q=self.image_plane_distance,
                angle_radial=0.0,
                angle_azimuthal=0.0,
                angle_radial_out=numpy.pi,
                )

    def get_optical_element_instance(self):
        boundary_shape = None

        if self.aperturing == 1:
            if self.aperture_shape == 0:   boundary_shape = Rectangle(x_left=self.slit_center_xaxis - self.slit_width_xaxis*0.5,
                                                                      x_right=self.slit_center_xaxis + self.slit_width_xaxis*0.5,
                                                                      y_bottom=self.slit_center_zaxis - self.slit_height_zaxis*0.5,
                                                                      y_top=self.slit_center_zaxis + self.slit_height_zaxis*0.5)
            elif self.aperture_shape == 1: boundary_shape = Ellipse(a_axis_min=self.slit_center_xaxis - self.slit_width_xaxis*0.5,
                                                                    a_axis_max=self.slit_center_xaxis + self.slit_width_xaxis*0.5,
                                                                    b_axis_min=self.slit_center_zaxis - self.slit_height_zaxis*0.5,
                                                                    b_axis_max=self.slit_center_zaxis + self.slit_height_zaxis*0.5)

        return S4Screen(name=self.getNode().title,
                        boundary_shape=boundary_shape,
                        i_abs=self.absorption==1,
                        i_stop=self.open_slit_solid_stop==1,
                        thick=self.thickness,
                        file_abs=self.opt_const_file_name)

    def get_beamline_element_instance(self): return S4ScreenElement()