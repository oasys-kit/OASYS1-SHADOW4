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
from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui

from syned.beamline.element_coordinates import ElementCoordinates

from shadow4.beamline.optical_elements.ideal_elements.s4_ideal_lens import S4IdealLensElement, S4SuperIdealLensElement, S4IdealLens, S4SuperIdealLens

from orangecontrib.shadow4.widgets.gui.ow_optical_element import OWOpticalElement


class OWIdealLens(OWOpticalElement):
    name        = "Ideal Lens"
    description = "Shadow Ideal Lens"
    icon        = "icons/ideal_lens.png"

    priority = 2.1

    focal_x    = Setting(0.0)
    focal_z    = Setting(0.0)

    focal_p_x    = Setting(0.0)
    focal_p_z    = Setting(0.0)
    focal_q_x    = Setting(0.0)
    focal_q_z    = Setting(0.0)

    ideal_lens_type = Setting(0)

    def __init__(self):
        super().__init__(has_footprint=False)

    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="image_plane_distance")

    def create_basic_settings_subtabs(self, tabs_basic_settings):
        return oasysgui.createTabPage(tabs_basic_settings, "Ideal Lens Parameters")  # to be populated

    def populate_basic_setting_subtabs(self, basic_setting_subtabs):
        tab_ideal_lens = basic_setting_subtabs

        box_ideal_lens = oasysgui.widgetBox(tab_ideal_lens, "", addSpace=False, orientation="vertical", height=180)

        gui.comboBox(box_ideal_lens, self, "ideal_lens_type", label="Ideal Lens Type", labelWidth=350,
                     items=["Simple", "Super"],
                     callback=self.set_ideal_lens_type, sendSelectedValue=False, orientation="horizontal")

        gui.separator(box_ideal_lens)

        self.box_focal_distances = oasysgui.widgetBox(box_ideal_lens, "Focal Distances", addSpace=False, orientation="vertical", height=140)
        self.box_p_q_distances   = oasysgui.widgetBox(box_ideal_lens, "P,Q Distances",   addSpace=False, orientation="vertical", height=140)

        oasysgui.lineEdit(self.box_focal_distances, self, "focal_x", "F(x) [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_focal_distances, self, "focal_z", "F(Z) [m]", labelWidth=260, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.box_p_q_distances, self, "focal_p_x", "P(x) [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_p_q_distances, self, "focal_p_z", "P(Z) [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_p_q_distances, self, "focal_q_x", "Q(X) [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_p_q_distances, self, "focal_q_z", "Q(Z) [m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_ideal_lens_type()

    def set_ideal_lens_type(self):
        self.box_focal_distances.setVisible(self.ideal_lens_type == 0)
        self.box_p_q_distances.setVisible(self.ideal_lens_type == 1)

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
        if self.ideal_lens_type == 0:   return S4IdealLens(name=self.getNode().title,
                                                           focal_x=self.focal_x,
                                                           focal_y=self.focal_z)
        elif self.ideal_lens_type == 1: return S4SuperIdealLens(name=self.getNode().title,
                                                                focal_p_x=self.focal_p_x,
                                                                focal_p_y=self.focal_p_z,
                                                                focal_q_x=self.focal_q_x,
                                                                focal_q_y=self.focal_q_z)

    def get_beamline_element_instance(self):
        if self.ideal_lens_type == 0:   return S4IdealLensElement()
        elif self.ideal_lens_type == 1: return S4SuperIdealLensElement()
