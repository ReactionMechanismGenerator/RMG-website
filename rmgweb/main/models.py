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

from django.db import models
from django.contrib.auth.models import User

################################################################################

ENERGY_UNITS = [
    ('J/mol', 'J/mol'),
    ('kJ/mol', 'kJ/mol'),
    ('cal/mol', 'cal/mol'),
    ('kcal/mol', 'kcal/mol'),
    ('cm^-1', 'cm^-1'),
]

HEATCAPACITY_UNITS = [
    ('J/(mol*K)', 'J/mol*K'),
    ('kJ/(mol*K)', 'kJ/mol*K'),
    ('cal/(mol*K)', 'cal/mol*K'),
    ('kcal/(mol*K)', 'kcal/mol*K'),
]


RATECOEFFICIENT_UNITS = [
    ('m^3,mol,s', 'm^3, mol, s'),
    ('cm^3,mol,s', 'cm^3, mol, s'),
    ('m^3,molecule,s', 'm^3, molecule, s'),
    ('cm^3,molecule,s', 'cm^3, molecule, s'),
]

TEMPERATURE_UNITS = [
    ('K', 'K'),
]

PRESSURE_UNITS = [
    ('Pa', 'Pa'),
    ('bar', 'bar'),
    ('atm', 'atm'),
    ('torr', 'torr'),
]

################################################################################

class UserProfile(models.Model):
    """
    A model containing user profile information. Some of the information is
    stored in the :class:`User` class built into Django; this class provides
    extra custom information.
    """
    user = models.OneToOneField(User)
    organization = models.CharField(max_length=100)
    website = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    # Preferred units
    energyUnits = models.CharField(verbose_name='Energy units', max_length=100, choices=ENERGY_UNITS, default='kcal/mol')
    heatCapacityUnits = models.CharField(verbose_name='Heat capacity units', max_length=100, choices=HEATCAPACITY_UNITS, default='cal/(mol*K)')
    rateCoefficientUnits = models.CharField(verbose_name='Rate coefficient units', max_length=100, choices=RATECOEFFICIENT_UNITS, default='cm^3,mol,s')
    temperatureUnits = models.CharField(verbose_name='Temperature units', max_length=100, choices=TEMPERATURE_UNITS, default='K')
    pressureUnits = models.CharField(verbose_name='Pressure units', max_length=100, choices=PRESSURE_UNITS, default='bar')
