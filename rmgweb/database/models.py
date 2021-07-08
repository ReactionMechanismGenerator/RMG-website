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


def get_solvent_list():
    """
    Return list of solvent molecules for initializing solvation search form.
    """
    database.load('solvation', '')
    solvent_list = []
    for label, entry in database.solvation.libraries['solvent'].entries.items():
        abraham_parameter_list = [entry.data.s_g, entry.data.b_g, entry.data.e_g, entry.data.l_g, entry.data.a_g,
                                  entry.data.c_g]
        mintz_parameter_list = [entry.data.s_h, entry.data.b_h, entry.data.e_h, entry.data.l_h, entry.data.a_h,
                                entry.data.c_h]
        if not any(param is None for param in abraham_parameter_list) or not any(param is None for param in mintz_parameter_list):
            solvent_list.append((entry.label, f'{entry.index}. {label}'))
    return solvent_list

def get_solvent_temp_list():
    """
    Return list of solvent molecules for initializing solvation temperature-dependent search form
    and its correct temperature range. e.g. "water: 280 K - 647.10 K"
    """
    database.load('solvation', '')
    solvent_temp_list = []
    solvent_list = get_solvent_list()
    for label, index in solvent_list:
        solvent_data = database.solvation.get_solvent_data(label)
        if solvent_data.name_in_coolprop != None:
            Tc = "%.2f" % (solvent_data.get_solvent_critical_temperature() - 0.01) # 0.01 is subtracted because Tc is not inclusive
            solvent_temp_list.append((label, index + ": 280 K - " + str(Tc) + " K"))
    return solvent_temp_list

solvent_list = get_solvent_list()
solvent_temp_list = get_solvent_temp_list()
solute_estimator_method_list = [('expt', 'Experimental (RMG-database)'),
                                ('SoluteGC', 'Group Contribution Prediction (SoluteGC)'),
                                ('SoluteML', 'Machine Learning Prediction (SoluteML)')]
energy_unit_list = [('kcal/mol', 'kcal/mol'),
                    ('kJ/mol', 'kJ/mol')]

class SolventSelection(models.Model):
    def __init__(self, *args, **kwargs):
        super(SolventSelection, self).__init__(*args, **kwargs)

    species_identifier = models.CharField(verbose_name="Solute Species Identifier", max_length=200, blank=True)
    adjlist = models.TextField(verbose_name="Solute Adjacency List")
    solvent = models.CharField(verbose_name="Solvent (Optional)", choices=solvent_list, max_length=200, blank=True)
    solvent_temp = models.CharField(verbose_name="Solvent", choices=solvent_temp_list, max_length=200, blank=True)
    temp = models.FloatField(default=298.0, verbose_name='Temperature in K (Optional)', blank=True)


class SoluteSearch(models.Model):
    def __init__(self, *args, **kwargs):
        super(SoluteSearch, self).__init__(*args, **kwargs)

    solute_smiles = models.TextField(verbose_name="Solute SMILES(s)", null=True)
    solute_estimator = models.CharField(verbose_name="Solute Parameter Search Method",
                                        choices=solute_estimator_method_list, max_length=200, blank=True)
    solvent = models.CharField(verbose_name="Solvent (Optional)", choices=solvent_list, max_length=200, blank=True)


class SolvationSearchML(models.Model):
    def __init__(self, *args, **kwargs):
        super(SolvationSearchML, self).__init__(*args, **kwargs)

    solvent_solute_smiles = models.TextField(verbose_name="Solvent_Solute SMILES(s)", null=True)
    calc_dGsolv = models.BooleanField(default=False, verbose_name='dGsolv')
    calc_dHsolv = models.BooleanField(default=False, verbose_name='dHsolv')
    calc_dSsolv = models.BooleanField(default=False, verbose_name='dSsolv')
    calc_logK = models.BooleanField(default=False, verbose_name='logK')
    calc_logP = models.BooleanField(default=False, verbose_name='logP')
    option_selected = models.BooleanField(default=False, verbose_name='at least one option selected')
    energy_unit = models.CharField(verbose_name="Preferred unit", choices=energy_unit_list, max_length=200, blank=False,
                                   default='kcal/mol')