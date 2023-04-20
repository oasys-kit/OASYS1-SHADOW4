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
from syned.beamline.shape import Circle
from shadow4.beamline.optical_elements.refractors.s4_lens import S4Lens, S4LensElement
from orangecontrib.shadow4.widgets.gui.ow_abstract_lens import OWAbstractLens

class OWLens(OWAbstractLens):
    name = "Refractive Lens"
    description = "Shadow Refractive Lens"
    icon = "icons/lens.png"
    priority = 3.1

    def __init__(self):
        super().__init__()

    # ----------------------------------------------------
    # from OpticalElement

    def get_optical_element_instance(self):
        try:    name = self.getNode().title
        except: name = "Refractive Lens"

        um_to_si = 1e-6

        if self.has_finite_diameter == 0: boundary_shape = Circle(radius=um_to_si*self.diameter*0.5)
        else:                             boundary_shape = None
        if self.is_cylinder == 1: cylinder_angle = self.cylinder_angle + 1
        else:                     cylinder_angle = 0

        return S4Lens(name=name,
                      boundary_shape=boundary_shape,
                      material="", # not used
                      thickness=self.interthickness*um_to_si,
                      surface_shape=self.surface_shape,
                      convex_to_the_beam=self.convex_to_the_beam,
                      cylinder_angle=cylinder_angle,
                      ri_calculation_mode=self.ri_calculation_mode,
                      prerefl_file=self.prerefl_file,
                      refraction_index=self.refraction_index,
                      attenuation_coefficient=self.attenuation_coefficient,
                      radius=self.radius*um_to_si,
                      conic_coefficients=None) # TODO: add conic coefficient shape to the GUI

    def get_beamline_element_instance(self):
        return S4LensElement()
