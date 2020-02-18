#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#                                                                             #
# RMG Website - A Django-powered website for Reaction Mechanism Generator     #
#                                                                             #
# Copyright (c) 2011-2018 Prof. William H. Green (whgreen@mit.edu),           #
# Prof. Richard H. West (r.west@neu.edu) and the RMG Team (rmg_dev@mit.edu)   #
#                                                                             #
# Permission is hereby granted, free of charge, to any person obtaining a     #
# copy of this software and associated documentation files (the 'Software'),  #
# to deal in the Software without restriction, including without limitation   #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,    #
# and/or sell copies of the Software, and to permit persons to whom the       #
# Software is furnished to do so, subject to the following conditions:        #
#                                                                             #
# The above copyright notice and this permission notice shall be included in  #
# all copies or substantial portions of the Software.                         #
#                                                                             #
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,    #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER      #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER         #
# DEALINGS IN THE SOFTWARE.                                                   #
#                                                                             #
###############################################################################

from django.db import models

from rmgweb.database.tools import database


def getSolventList():
    """
    Return list of solvent molecules for initializing solvation search form.
    If any of the Mintz parameters are None, that solvent is not shown in the list since it will cause error.
    """
    database.load('solvation', '')
    solvent_list = []
    for index, entry in database.solvation.libraries['solvent'].entries.items():
        mintz_parameter_list = [entry.data.s_h, entry.data.b_h, entry.data.e_h, entry.data.l_h, entry.data.a_h,
                                entry.data.c_h]
        if not any(h is None for h in mintz_parameter_list):
            solvent_list.append((entry.label, index))
    return solvent_list

def get_solvent_temp_list():
    """
    Return list of solvent molecules for initializing solvation temperature-dependent search form
    and its correct temperature range. e.g. "water: 280 K - 647.10 K"
    """
    database.load('solvation', '')
    solvent_temp_list = []
    for index, entry in database.solvation.libraries['solvent'].entries.items():
        if entry.data.name_in_coolprop != None:
            Tc = "%.2f" % entry.data.get_solvent_critical_temperature()
            solvent_temp_list.append((entry.label, index + ": 280 K - " + str(Tc) + " K"))
    return solvent_temp_list

solvent_list = getSolventList()
solvent_temp_list = get_solvent_temp_list()

class SolventSelection(models.Model):
    def __init__(self, *args, **kwargs):
        super(SolventSelection, self).__init__(*args, **kwargs)

    species_identifier = models.CharField(verbose_name="Solute Species Identifier", max_length=200, blank=True)
    adjlist = models.TextField(verbose_name="Solute Adjacency List")
    solvent = models.CharField(verbose_name="Solvent (Optional)", choices=solvent_list, max_length=200, blank=True)
    solvent_temp = models.CharField(verbose_name="Solvent", choices=solvent_temp_list, max_length=200, blank=True)
    temp = models.FloatField(default=298.0, verbose_name='Temperature in K (Optional)', blank=True)
