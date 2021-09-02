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

"""
Provides template tags for rendering thermodynamics models in various ways.
"""

import numpy as np
from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse
from rmgpy.quantity import Quantity
from rmgpy.thermo import *

from rmgweb.main.tools import getLaTeXScientificNotation
from rmgweb.main.models import UserProfile

# Register this module as a Django template tag library
register = template.Library()

################################################################################


@register.filter
def render_thermo_math(thermo, user=None):
    """
    Return a math representation of the given `thermo` using MathJax. If a
    `user` is specified, the user's preferred units will be used; otherwise
    default units will be used.
    """
    # Define other units and conversion factors to use
    if user and user.is_authenticated:
        user_profile = UserProfile.objects.get(user=user)
        Tunits = user_profile.temperature_units
        Cpunits = user_profile.heat_capacity_units
        Hunits = user_profile.energy_units
        Sunits = user_profile.heat_capacity_units
    else:
        Tunits = 'K'
        Cpunits = 'cal/(mol*K)'
        Hunits = 'kcal/mol'
        Sunits = 'cal/(mol*K)'
    Tfactor = Quantity(1, Tunits).get_conversion_factor_from_si()
    Cpfactor = Quantity(1, Cpunits).get_conversion_factor_from_si()
    Hfactor = Quantity(1, Hunits).get_conversion_factor_from_si()
    Sfactor = Quantity(1, Sunits).get_conversion_factor_from_si()

    # The string that will be returned to the template
    result = ''

    if isinstance(thermo, ThermoData):
        # The thermo is in ThermoData format
        result += '<table class="thermoEntryData">\n'

        if thermo.H298 is not None:
            result += '<tr>'
            result += r'    <td class="key"><script type="math/tex">\Delta H_\mathrm{f}^\circ(298 \ \mathrm{K})</script></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(thermo.H298.value_si * Hfactor, Hunits)
            result += '</tr>\n'

        if thermo.S298 is not None:
            result += '<tr>'
            result += r'    <td class="key"><script type="math/tex">S^\circ(298 \ \mathrm{K})</script></td>'
            result += r'    <td class="equals">=</td>'
            result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(thermo.S298.value_si * Sfactor, Sunits)
            result += '</tr>\n'
        if thermo.Tdata is not None and thermo.Cpdata is not None:
            for T, Cp in zip(thermo.Tdata.value_si, thermo.Cpdata.value_si):
                result += '<tr>'
                result += r'    <td class="key"><script type="math/tex">C_\mathrm{{p}}^\circ({0:g} \ \mathrm{{ {1!s} }})</script></td>'.format(T * Tfactor, Tunits)
                result += r'    <td class="equals">=</td>'
                result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(Cp * Cpfactor, Cpunits)
                result += '</tr>\n'
        result += '</table>\n'

    elif isinstance(thermo, Wilhoit):
        # The thermo is in Wilhoit format
        result += '<script type="math/tex; mode=display">\n'
        result += r'\begin{split}'
        result += r'C_\mathrm{p}(T) &= C_\mathrm{p}(0) + \left[ C_\mathrm{p}(\infty) -'
        result += r'    C_\mathrm{p}(0) \right] y^2 \left[ 1 + (y - 1) \sum_{i=0}^3 a_i y^i \right] \\'
        result += r'H^\circ(T) &= H_0 + \int_0^\infty C_\mathrm{p}(T) \ dT \\'
        result += r'S^\circ(T) &= S_0 + \int_0^\infty \frac{C_\mathrm{p}(T)}{T} \ dT\\'
        result += r'y &\equiv \frac{T}{T + B}'
        result += r'\end{split}'
        result += '</script>\n'

        result += '<table class="thermoEntryData">\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">C_\mathrm{p}(0)</script></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s}  }}</script></td>'.format(thermo.Cp0.value_si * Cpfactor, Cpunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">C_\mathrm{p}(\infty)</script></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(thermo.CpInf.value_si * Cpfactor, Cpunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_0</script></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(thermo.a0))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_1</script></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(thermo.a1))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_2</script></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(thermo.a2))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_3</script></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(thermo.a3))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">H_0</script></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(thermo.H0.value_si * Hfactor, Hunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">S_0</script></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(thermo.S0.value_si * Sfactor, Sunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">B</script></td>'
        result += r'    <td class="equals">=</td>'
        result += r'    <td class="value"><script type="math/tex">{0:.2f} \ \mathrm{{ {1!s} }}</script></td>'.format(thermo.B.value_si * Tfactor, Tunits)
        result += '</tr>\n'
        result += '</table>\n'

    elif isinstance(thermo, NASA):
        # The thermo is in NASA format
        result += '<script type="math/tex; mode=display">\n'
        result += r'\frac{C_\mathrm{p}^\circ(T)}{R} = a_{-2} T^{-2} + a_{-1} T^{-1} + a_0 + a_1 T + a_2 T^2 + a_3 T^3 + a_4 T^4'
        result += '</script>\n'
        result += '<script type="math/tex; mode=display">\n'
        result += r'\frac{H^\circ(T)}{RT} = -a_{-2} T^{-2} + a_{-1} \frac{\ln T}{T} + a_0 + \frac{1}{2} a_1 T + \frac{1}{3} a_2 T^2 + \frac{1}{4} a_3 T^3 + \frac{1}{5} a_4 T^4 + \frac{a_5}{T}'
        result += '</script>\n'
        result += '<script type="math/tex; mode=display">\n'
        result += r'\frac{S^\circ(T)}{R} = -\frac{1}{2} a_{-2} T^{-2} - a_{-1} T^{-1} + a_0 \ln T + a_1 T + \frac{1}{2} a_2 T^2 + \frac{1}{3} a_3 T^3 + \frac{1}{4} a_4 T^4 + a_6'
        result += '</script>\n'

        result += '<table class="thermoEntryData">\n'
        result += '<tr>'
        result += r'    <td class="key">Temperature range</td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value">{0:g} to {1:g} {2!s}</td>'.format(polynomial.Tmin.value_si * Tfactor, polynomial.Tmax.value_si * Tfactor, Tunits)
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_{-2}</script></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(polynomial.cm2))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_{-1}</script></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(polynomial.cm1))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_0</script></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(polynomial.c0))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_1</script></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(polynomial.c1))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_2</script></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(polynomial.c2))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_3</script></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(polynomial.c3))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_4</script></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(polynomial.c4))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_5</script></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(polynomial.c5))
        result += '</tr>\n'
        result += '<tr>'
        result += r'    <td class="key"><script type="math/tex">a_6</script></td>'
        result += r'    <td class="equals">=</td>'
        for polynomial in thermo.polynomials:
            result += r'    <td class="value"><script type="math/tex">{0!s}</script></td>'.format(getLaTeXScientificNotation(polynomial.c6))
        result += '</tr>\n'
        result += '</table>\n'

    elif isinstance(thermo, list):
        # The thermo is a link
        index = thermo[1]
        url = reverse('database:thermo-entry', {'section': section, 'subsection': subsection, 'index': index})
        result += '<table class="thermoEntryData">\n'
        result += '<tr>'
        result += r'    <td class="key">Link:</td>'
        result += r'    <td class="value"><a href="{0!s}">{1}</a></td>'.format(url, index)
        result += '</tr>\n'
        result += '<\table>\n'

    # Temperature range
    if isinstance(thermo, (ThermoData, Wilhoit, NASA)):
        result += '<table class="thermoEntryData">'
        if thermo.Tmin is not None and thermo.Tmax is not None:
            result += '<tr><td class="key">Temperature range</td><td class="equals">=</td><td class="value">{0:g} to {1:g} {2!s}</td></tr>'.format(thermo.Tmin.value_si, thermo.Tmax.value_si, Tunits)
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

    if not isinstance(thermo, (ThermoData, Wilhoit, NASA)):
        return ''

    # Define other units and conversion factors to use
    if user and user.is_authenticated:
        user_profile = UserProfile.objects.get(user=user)
        Tunits = user_profile.temperature_units
        Cpunits = user_profile.heat_capacity_units
        Hunits = user_profile.energy_units
        Sunits = user_profile.heat_capacity_units
        Gunits = user_profile.energy_units
    else:
        Tunits = 'K'
        Cpunits = 'cal/(mol*K)'
        Hunits = 'kcal/mol'
        Sunits = 'cal/(mol*K)'
        Gunits = 'kcal/mol'
    Tfactor = Quantity(1, Tunits).get_conversion_factor_from_si()
    Cpfactor = Quantity(1, Cpunits).get_conversion_factor_from_si()
    Hfactor = Quantity(1, Hunits).get_conversion_factor_from_si()
    Sfactor = Quantity(1, Sunits).get_conversion_factor_from_si()
    Gfactor = Quantity(1, Gunits).get_conversion_factor_from_si()

    if thermo.Tmin is not None and thermo.Tmax is not None:
        Tmin = thermo.Tmin.value_si
        Tmax = thermo.Tmax.value_si
    elif isinstance(thermo, ThermoData) and (thermo.Cp0 is None or thermo.CpInf is None):
        Tmin = 300
        Tmax = 1500
    else:
        Tmin = 300
        Tmax = 2000
    Tdata = []
    Cpdata = []
    Hdata = []
    Sdata = []
    Gdata = []

    try:
        for T in np.arange(Tmin, Tmax+1, 10):
            Tdata.append(T * Tfactor)
            Cpdata.append(thermo.get_heat_capacity(T) * Cpfactor)
            Hdata.append(thermo.get_enthalpy(T) * Hfactor)
            Sdata.append(thermo.get_entropy(T) * Sfactor)
            Gdata.append(thermo.get_free_energy(T) * Gfactor)

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
    except:
        # don't fail completely if thermo data is incomplete
        return ''

################################################################################


@register.filter
def get_items(dictionary, key):
    '''
    By default, Django does not let the user lookup a dictionary value if the key is the loop variable.
    This filter is a workaround to enable using loop variable as a key in a view.
    '''
    return dictionary.get(key)
    