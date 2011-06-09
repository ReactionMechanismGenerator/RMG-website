#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
#
#	RMG Website - A Django-powered website for Reaction Mechanism Generator
#
#	Copyright (c) 2011 Prof. William H. Green (whgreen@mit.edu) and the
#	RMG Team (rmg_dev@mit.edu)
#
#	Permission is hereby granted, free of charge, to any person obtaining a
#	copy of this software and associated documentation files (the 'Software'),
#	to deal in the Software without restriction, including without limitation
#	the rights to use, copy, modify, merge, publish, distribute, sublicense,
#	and/or sell copies of the Software, and to permit persons to whom the
#	Software is furnished to do so, subject to the following conditions:
#
#	The above copyright notice and this permission notice shall be included in
#	all copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#	DEALINGS IN THE SOFTWARE.
#
################################################################################

"""
This module defines the Django forms used by the pdep app.
"""

from django import forms

from models import *

################################################################################

class EditNetworkForm(forms.ModelForm):
    """
    A Django form for editing a MEASURE input file.
    """
    class Meta:
        model = Network
        fields = ('inputText',)

################################################################################

class UploadNetworkForm(forms.ModelForm):
    """
    A Django form for uploading a MEASURE input file.
    """
    class Meta:
        model = Network
        fields = ('inputFile',)

################################################################################

class PlotKineticsForm(forms.Form):
    """
    A Django form for choosing parameters for generating k(T,P) vs. T and P
    plots.
    """
    reactant = forms.ChoiceField(choices=[], label='Reactant configuration')
    T = forms.FloatField(initial=1000, label='Temperature of k(T,P) vs. P plot (K)')
    P = forms.FloatField(initial=1, label='Pressure of k(T,P) vs. T plot (bar)')

    def __init__(self, configurations, *args, **kwargs):
        super(PlotKineticsForm, self).__init__(*args, **kwargs)
        choices = [(config, config) for config in configurations]
        self.fields['reactant'].choices = choices
