#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------- #
# Copyright (c) 2023, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2023. UChicago Argonne, LLC. This software was produced       #
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
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from syned.beamline.shape import Circle
from shadow4.beamline.optical_elements.refractors.s4_crl import S4CRL, S4CRLElement
from orangecontrib.shadow4.widgets.gui.ow_abstract_lens import OWAbstractLens

class OWCRL(OWAbstractLens):
    name = "Compound Refractive Lens"
    description = "Shadow Compound Refractive Lens"
    icon = "icons/crl.png"
    priority = 3.2

    n_lens                  = Setting(10)
    piling_thickness        = Setting(2.5)

    def __init__(self):
        super().__init__()

    def create_basic_settings_subtabs(self, tabs_basic_settings):
        return oasysgui.createTabPage(tabs_basic_settings, "CRL") # to be populated

    def populate_basic_setting_subtabs(self, basic_setting_subtabs):
        crl_box = oasysgui.widgetBox(basic_setting_subtabs, "CRL Parameters", addSpace=False, orientation="vertical", height=90)

        oasysgui.lineEdit(crl_box, self, "n_lens", "Number of lenses", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(crl_box, self, "piling_thickness", "Piling thickness [mm]", labelWidth=260, valueType=float, orientation="horizontal")

        super(OWCRL, self).populate_basic_setting_subtabs(basic_setting_subtabs)

    def get_optical_element_instance(self):
        try:    name = self.getNode().title
        except: name = "Compound Refractive Lens"

        um_to_si = 1e-6
        mm_to_si = 1e-3

        if self.has_finite_diameter == 0: boundary_shape = Circle(radius=um_to_si * self.diameter * 0.5)
        else:                             boundary_shape = None
        if self.is_cylinder == 1: cylinder_angle = self.cylinder_angle + 1
        else:                     cylinder_angle = 0

        return S4CRL(name=name,
                     n_lens=self.n_lens,
                     piling_thickness=self.piling_thickness*mm_to_si,
                     boundary_shape=boundary_shape,
                     material="", # not used
                     thickness=self.interthickness * um_to_si,
                     surface_shape=self.surface_shape,
                     convex_to_the_beam=self.convex_to_the_beam,
                     cylinder_angle=cylinder_angle,
                     ri_calculation_mode=self.ri_calculation_mode,
                     prerefl_file=self.prerefl_file,
                     refraction_index=self.refraction_index,
                     attenuation_coefficient=self.attenuation_coefficient,
                     radius=self.radius * um_to_si,
                     conic_coefficients=None)  # TODO: add conic coefficient shape to the GUI

    def get_beamline_element_instance(self):
        return S4CRLElement()
