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
Provides template tags for rendering thermodynamics models in various ways.
"""

# Register this module as a Django template tag library
from django import template
register = template.Library()

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

import numpy

from rmgweb.main.tools import getLaTeXScientificNotation, getStructureMarkup
from rmgweb.main.models import UserProfile

from rmgpy.quantity import Quantity
from rmgpy.thermo import *

################################################################################

@register.filter
def render_thermo_math(thermo, user=None):
    """
    Return a math representation of the given `thermo` using jsMath. If a 
    `user` is specified, the user's preferred units will be used; otherwise 
    default units will be used.
    """
    # Define other units and conversion factors to use
    if user and user.is_authenticated():
        user_profile = UserProfile.objects.get(user=user)
        Tunits = str(user_profile.temperatureUnits)
        Punits = str(user_profile.pressureUnits)
        Cpunits = str(user_profile.heatCapacityUnits)
        Hunits = str(user_profile.energyUnits)
        Sunits = str(user_profile.heatCapacityUnits)
        Gunits = str(user_profile.energyUnits)
    else:
        Tunits = 'K'
        Punits = 'bar'
        Cpunits = 'cal/(mol*K)'
        Hunits = 'kcal/mol'
        Sunits = 'cal/(mol*K)'
        Gunits = 'kcal/mol'
    Tfactor = Quantity(1, Tunits).getConversionFactorFromSI()
    Pfactor = Quantity(1, Punits).getConversionFactorFromSI()
    Cpfactor = Quantity(1, Cpunits).getConversionFactorFromSI()
    Hfactor = Quantity(1, Hunits).getConversionFactorFromSI()
    Sfactor = Quantity(1, Sunits).getConversionFactorFromSI()
    Gfactor = Quantity(1, Gunits).getConversionFactorFromSI()
    
    # The string that will be returned to the template
    result = ''
    
    if isinstance(thermo, ThermoData):
        # The thermo is in ThermoData format
        result += '<table class="thermoEntryData">\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">\Delta H_\mathrm{f}^\circ(298 \ \mathrm{K})</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(thermo.H298.value * Hfactor, Hunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">\Delta S_\mathrm{f}^\circ(298 \ \mathrm{K})</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(thermo.S298.value * Sfactor, Sunits)
        result += '</tr>\n'
        for T, Cp in zip(thermo.Tdata.values, thermo.Cpdata.values):
            result += '<tr>'
            result += r'    <td class="key"><span class="math">C_\mathrm{{p}}^\circ({0:g} \ \mathrm{{ {1!s} }})</span></td>'.format(T * Tfactor, Tunits)
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(Cp * Cpfactor, Cpunits)
            result += '</tr>\n'
        result += '</table>\n'
    
    elif isinstance(thermo, Wilhoit):
        # The thermo is in Wilhoit format
        result += '<div class="math">\n'
        result += r'\begin{split}'
        result += r'C_\mathrm{p}(T) &= C_\mathrm{p}(0) + \left[ C_\mathrm{p}(\infty) -'
        result += r'    C_\mathrm{p}(0) \right] y^2 \left[ 1 + (y - 1) \sum_{i=0}^3 a_i y^i \right] \\'
        result += r'H^\circ(T) &= H_0 + \int_0^\infty C_\mathrm{p}(T) \ dT \\'
        result += r'S^\circ(T) &= S_0 + \int_0^\infty \frac{C_\mathrm{p}(T)}{T} \ dT\\'
        result += r'y &\equiv \frac{T}{T + B}'
        result += r'\end{split}'
        result += '</div>\n'

        result += '<table class="thermoEntryData">\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">C_\mathrm{p}(0)</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s}  }}</span></td>'.format(thermo.cp0.value * Cpfactor, Cpunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">C_\mathrm{p}(\infty)</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(thermo.cpInf.value * Cpfactor, Cpunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_0</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(thermo.a0.value))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_1</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(thermo.a1.value))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_2</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(thermo.a2.value))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_3</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(thermo.a3.value))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">H_0</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(thermo.H0.value * Hfactor, Hunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">S_0</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(thermo.S0.value * Sfactor, Sunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">B</span></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><span class="math">{0:.2f} \ \mathrm{{ {1!s} }}</span></td>'.format(thermo.B.value * Tfactor, Tunits)
        result += '</tr>\n'
        result += '</table>\n'
    
    elif isinstance(thermo, MultiNASA):
        # The thermo is in MultiNASA format
        result += '<div class="math">\n'
        result += r'\frac{C_\mathrm{p}^\circ(T)}{R} = a_{-2} T^{-2} + a_{-1} T^{-1} + a_0 + a_1 T + a_2 T^2 + a_3 T^3 + a_4 T^4'
        result += '</div>\n'
        result += '<div class="math">\n'
        result += r'\frac{H^\circ(T)}{RT} = -a_{-2} T^{-2} + a_{-1} \frac{\ln T}{T} + a_0 + \frac{1}{2} a_1 T + \frac{1}{3} a_2 T^2 + \frac{1}{4} a_3 T^3 + \frac{1}{5} a_4 T^4 + \frac{a_5}{T}'
        result += '</div>\n'
        result += '<div class="math">\n'
        result += r'\frac{S^\circ(T)}{R} = -\frac{1}{2} a_{-2} T^{-2} - a_{-1} T^{-1} + a_0 \ln T + a_1 T + \frac{1}{2} a_2 T^2 + \frac{1}{3} a_3 T^3 + \frac{1}{4} a_4 T^4 + a_6'
        result += '</div>\n'

        result += '<table class="thermoEntryData">\n'
        result += '<tr>'
        result += r'    <td class="key">Temperature range</td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value">{0:g} to {1:g} {2!s}</td>'.format(polynomial.Tmin.value * Tfactor, polynomial.Tmax.value * Tfactor, Tunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_{-2}</span></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(polynomial.cm2))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_{-1}</span></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(polynomial.cm1))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_0</span></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(polynomial.c0))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_1</span></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(polynomial.c1))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_2</span></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(polynomial.c2))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_3</span></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(polynomial.c3))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_4</span></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(polynomial.c4))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_5</span></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(polynomial.c5))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><span class="math">a_6</span></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><span class="math">{0!s}</span></td>'.format(getLaTeXScientificNotation(polynomial.c6))
        result += '</tr>\n'
        result += '</table>\n'
    
    elif isinstance(thermo, list):
        # The thermo is a link
        index = thermo[1]
        url = reverse('database.views.thermoEntry', {'section': section, 'subsection': subsection, 'index': index})
        result += '<table class="thermoEntryData">\n'
        result += '<tr>'
        result += r'    <td class="key">Link:</td>'
        result += r'    <td class="value"><a href="{0!s}">{1}</a></td>'.format(url, index)
        result += '</tr>\n'
        result += '<\table>\n'
    
    # Temperature range
    if isinstance(thermo, (ThermoData, Wilhoit, MultiNASA)):
        result += '<table class="thermoEntryData">'
        if thermo.Tmin is not None and thermo.Tmax is not None:
            result += '<tr><td class="key">Temperature range</td><td class="equals">=</td><td class="value">{0:g} to {1:g} {2!s}</td></tr>'.format(thermo.Tmin.value * Tfactor, thermo.Tmax.value * Tfactor, Tunits)
        result += '</table>'

    return mark_safe(result)

################################################################################

@register.filter
def get_thermo_data(thermo, user=None):
    """
    Generate and return a set of thermodynamics data suitable for plotting
    using Highcharts. If a `user` is specified, the user's preferred units
    will be used; otherwise default units will be used.
    """
    
    if not isinstance(thermo, (ThermoData, Wilhoit, MultiNASA)):
        return ''
    
    # Define other units and conversion factors to use
    if user and user.is_authenticated():
        user_profile = UserProfile.objects.get(user=user)
        Tunits = str(user_profile.temperatureUnits)
        Punits = str(user_profile.pressureUnits)
        Cpunits = str(user_profile.heatCapacityUnits)
        Hunits = str(user_profile.energyUnits)
        Sunits = str(user_profile.heatCapacityUnits)
        Gunits = str(user_profile.energyUnits)
    else:
        Tunits = 'K'
        Punits = 'bar'
        Cpunits = 'cal/(mol*K)'
        Hunits = 'kcal/mol'
        Sunits = 'cal/(mol*K)'
        Gunits = 'kcal/mol'
    Tfactor = Quantity(1, Tunits).getConversionFactorFromSI()
    Pfactor = Quantity(1, Punits).getConversionFactorFromSI()
    Cpfactor = Quantity(1, Cpunits).getConversionFactorFromSI()
    Hfactor = Quantity(1, Hunits).getConversionFactorFromSI()
    Sfactor = Quantity(1, Sunits).getConversionFactorFromSI()
    Gfactor = Quantity(1, Gunits).getConversionFactorFromSI()
        
    if thermo.Tmin is not None and thermo.Tmax is not None:
        Tmin = thermo.Tmin.value
        Tmax = thermo.Tmax.value
    else:
        Tmin = 300
        Tmax = 2000
    Tdata = []; Cpdata = []; Hdata = []; Sdata = []; Gdata = []
    for T in numpy.arange(Tmin, Tmax+1, 10):
        Tdata.append(T * Tfactor)
        Cpdata.append(thermo.getHeatCapacity(T) * Cpfactor)
        Hdata.append(thermo.getEnthalpy(T) * Hfactor)
        Sdata.append(thermo.getEntropy(T) * Sfactor)
        Gdata.append(thermo.getFreeEnergy(T) * Gfactor)
    
    return mark_safe("""
Tlist = {0};
Cplist = {1};
Hlist = {2};
Slist = {3};
Glist = {4};
Tunits = "{5!s}";
Cpunits = "{6!s}";
Hunits = "{7!s}";
Sunits = "{8!s}";
Gunits = "{9!s}";
    """.format(
        Tdata,
        Cpdata, 
        Hdata,
        Sdata, 
        Gdata, 
        Tunits, 
        Cpunits, 
        Hunits,
        Sunits,
        Gunits,
    ))
