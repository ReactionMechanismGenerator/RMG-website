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
Provides template tags for rendering kinetics models in various ways.
"""

import math
import numpy as np
from django import template
from django.utils.safestring import mark_safe
from rmgpy.quantity import Quantity
from rmgpy.kinetics import *

from rmgweb.main.models import UserProfile
from rmgweb.main.tools import getLaTeXScientificNotation, getStructureMarkup

# Register this module as a Django template tag library
register = template.Library()

################################################################################

UNIT_TYPES = {
    'cm': 'length',
    'm': 'length',
    'mol': 'mol',
    'molecule': 'mol',
    's': 'time',
}


def getArrheniusJSMath(A, Aunits, n, nunits, Ea, Eaunits, T0, T0units):
    result = '{0!s}'.format(getLaTeXScientificNotation(A))
    if n != 0:
        if T0 != 1:
            result += r' \left( \frac{{T}}{{ {0:g} \ \mathrm{{ {1!s} }} }} \right)^{{ {2:.2f} }}'.format(T0, T0units, n)
        else:
            result += r' T^{{ {0:.2f} }}'.format(n)
    if Ea > 0:
        result += r' \exp \left( - \, \frac{{ {0:.2f} \ \mathrm{{ {1!s} }} }}{{ R T }} \right)'.format(Ea, Eaunits)
    elif Ea < 0:
        result += r' \exp \left(\frac{{ {0:.2f} \ \mathrm{{ {1!s} }} }}{{ R T }} \right)'.format(-Ea, Eaunits)
    result += ' \ \mathrm{{ {0!s} }}'.format(Aunits)
    return result


def get_rate_unit_dimensionality(units):
    """
    For the given units, deconstruct into dimensions and powers, returned
    as a dictionary. Assumes fairly consistent unit formatting.

    Set of units for which this function was designed:
        's^-1'
        's**-1'
        'm^3/(mol*s)'
        'm**3/(mol*s)'
        'm^3/mol/s'
        'm**3/mol/s'
        'cm^3/(mol*s)'
        'cm**3/(mol*s)'
        'cm^3/mol/s'
        'cm**3/mol/s'
        'm^3/(molecule*s)'
        'm**3/(molecule*s)'
        'm^3/molecule/s'
        'm**3/molecule/s'
        'cm^3/(molecule*s)'
        'cm**3/(molecule*s)'
        'cm^3/molecule/s'
        'cm**3/molecule/s'
        'm^6/(mol^2*s)'
        'm**6/(mol^2*s)'
        'm^6/mol^2/s'
        'm**6/mol^2/s'
        'cm^6/(mol^2*s)'
        'cm**6/(mol^2*s)'
        'cm^6/mol^2/s'
        'cm**6/mol^2/s'
        'm^6/(molecule^2*s)'
        'm**6/(molecule^2*s)'
        'm^6/molecule^2/s'
        'm**6/molecule^2/s'
        'cm^6/(molecule^2*s)'
        'cm**6/(molecule^2*s)'
        'cm^6/molecule^2/s'
        'cm**6/molecule^2/s'
    """
    dimensionality = {}
    units = units.replace('**', '^')

    fractions = units.split('/')
    for i, frac in enumerate(fractions):
        # Remove any parentheses and split by *
        parts = frac.replace('(', '').replace(')', '').split('*')
        for part in parts:
            if '^' in part:
                unit, power = part.split('^')
                power = int(power)
            else:
                unit, power = part, 1
            if i % 2:
                # In denominator, should have negative power
                power = -power
            dimensionality[UNIT_TYPES[unit]] = power

    return dimensionality


def construct_rate_units(dimensionality, desired_units):
    """
    Put the provided unit parts back together into a single unit based on the
    provided dimensionality and units.
    """
    error = False
    units = ''
    if len(dimensionality) == 1:
        # Should just be time units
        unit, power = desired_units['time'], dimensionality['time']
        units = '{0}^{1}'.format(unit, power)
    elif len(dimensionality) == 3:
        # Should be combination of length, mol, and time units
        length = mol = time = ''
        for dimension, power in dimensionality.items():
            if abs(power) == 1:
                exponent = ''
            else:
                exponent = '^{0}'.format(abs(power))
            if dimension == 'length':
                if power < 1:
                    # length units should have positive exponent
                    error = True
                length = desired_units[dimension] + exponent
            elif dimension == 'mol':
                if power > 1:
                    # mol units should have negative exponent
                    error = True
                mol = desired_units[dimension] + exponent
            elif dimension == 'time':
                if power > 1:
                    # time units should have negative exponent
                    error = True
                time = desired_units[dimension] + exponent
        if length and mol and time:
            units = '{0}/({1}*{2})'.format(length, mol, time)
        else:
            error = True
    else:
        error = True

    if error:
        raise ValueError('Unable to construct rate units from the provided dimensionality: {0!r}'.format(dimensionality))

    return units


def reconstruct_rate_units(units, desired_units, add_conc_dim=False):
    """
    Reconstruct the specified units using the desired base units.

    For example, if m^6/(mol^2*s) is provided and the desired units are
    cm^3, molecule, s, then return cm^6/(molecule^2*s).
    """
    dimensionality = get_rate_unit_dimensionality(units)

    if add_conc_dim:
        # Add an additional inverse concentration dimension for low pressure kinetics
        if 'length' in dimensionality:
            dimensionality['length'] += 3
        else:
            dimensionality['length'] = 3
        if 'mol' in dimensionality:
            dimensionality['mol'] -= 1
        else:
            dimensionality['mol'] = -1

    unit_dict = {}
    if desired_units == 'm^3,mol,s':
        unit_dict['length'] = 'm'
        unit_dict['mol'] = 'mol'
        unit_dict['time'] = 's'
    elif desired_units == 'cm^3,mol,s':
        unit_dict['length'] = 'cm'
        unit_dict['mol'] = 'mol'
        unit_dict['time'] = 's'
    elif desired_units == 'm^3,molecule,s':
        unit_dict['length'] = 'm'
        unit_dict['mol'] = 'molecule'
        unit_dict['time'] = 's'
    elif desired_units == 'cm^3,molecule,s':
        unit_dict['length'] = 'cm'
        unit_dict['mol'] = 'molecule'
        unit_dict['time'] = 's'

    return construct_rate_units(dimensionality, unit_dict)


def getRateCoefficientUnits(kinetics, user=None):
    """
    For a given `kinetics` model, return the desired rate coefficient units
    at high and low pressures, the conversion factor from SI to those units
    (high pressure), and the number of reactant species. If a `user` is
    specified, the user's preferred units will be used; otherwise default units
    will be used.
    """
    # Get units from based on the kinetics type
    if isinstance(kinetics, (Arrhenius, ArrheniusEP, SurfaceArrhenius, SurfaceArrheniusBEP, StickingCoefficient, StickingCoefficientBEP)):
        units = kinetics.A.units
    elif isinstance(kinetics, KineticsData):
        units = kinetics.kdata.units
    elif isinstance(kinetics, (PDepArrhenius, MultiArrhenius, MultiPDepArrhenius)):
        return getRateCoefficientUnits(kinetics.arrhenius[0])
    elif isinstance(kinetics, Chebyshev):
        units = kinetics.kunits
    elif isinstance(kinetics, Troe):
        units = kinetics.arrheniusHigh.A.units
    elif isinstance(kinetics, Lindemann):
        units = kinetics.arrheniusHigh.A.units
    elif isinstance(kinetics, ThirdBody):
        units = kinetics.arrheniusLow.A.units
    else:
        raise NotImplementedError('Cannot get units for {0} class.'.format(kinetics.__class__.__name__))

    if user and user.is_authenticated():
        # If user is logged in, get their desired units
        user_profile = UserProfile.objects.get(user=user)
        desired_units = user_profile.rate_coefficient_units
    else:
        # Default base units
        desired_units = 'm^3,mol,s'

    if units == '':
        # Dimensionless
        return '', '', 1
    else:
        # Reconstruct the rate units using the desired base units
        kunits = reconstruct_rate_units(units, desired_units)
        kunits_low = reconstruct_rate_units(units, desired_units, add_conc_dim=True)
        kfactor = Quantity(1, kunits).get_conversion_factor_from_si()

        return kunits, kunits_low, kfactor

################################################################################


@register.filter
def render_kinetics_math(kinetics, user=None):
    """
    Return a math representation of the given `kinetics` using MathJax. If a
    `user` is specified, the user's preferred units will be used; otherwise
    default units will be used.
    """
    if kinetics is None:
        return mark_safe("<p>There are no kinetics for this entry.</p>")
    # Define other units and conversion factors to use
    if user and user.is_authenticated():
        user_profile = UserProfile.objects.get(user=user)
        Tunits = user_profile.temperature_units
        Punits = user_profile.pressure_units
        Eunits = user_profile.energy_units
    else:
        Tunits = 'K'
        Punits = 'Pa'
        Eunits = 'J/mol'
    kunits, kunits_low, kfactor = getRateCoefficientUnits(kinetics, user=user)
    Tfactor = Quantity(1, Tunits).get_conversion_factor_from_si()
    Pfactor = Quantity(1, Punits).get_conversion_factor_from_si()
    Efactor = Quantity(1, Eunits).get_conversion_factor_from_si()
    if kunits == 's^-1':
        kunits = 's^{-1}'

    # The string that will be returned to the template
    result = ''

    if isinstance(kinetics, (Arrhenius, SurfaceArrhenius, StickingCoefficient)):
        # The kinetics is in Arrhenius format
        result += r'<script type="math/tex; mode=display">k(T) = {0!s}</script>'.format(getArrheniusJSMath(
            kinetics.A.value_si * kfactor, kunits,
            kinetics.n.value_si, '',
            kinetics.Ea.value_si * Efactor, Eunits,
            kinetics.T0.value_si * Tfactor, Tunits,
        ))

    elif isinstance(kinetics, (ArrheniusEP, SurfaceArrheniusBEP, StickingCoefficientBEP)):
        # The kinetics is in ArrheniusEP format
        result += r'<script type="math/tex; mode=display">k(T) = {0!s}'.format(getLaTeXScientificNotation(kinetics.A.value_si * kfactor))
        if kinetics.n.value_si != 0:
            result += r' T^{{ {0:.2f} }}'.format(kinetics.n.value_si)
        result += r' \exp \left( - \, \frac{{ {0:.2f} \ \mathrm{{ {1!s} }} + {2:.2f} \Delta H_\mathrm{{rxn}}^\circ }}{{ R T }} \right)'.format(kinetics.E0.value_si * Efactor, Eunits, kinetics.alpha.value_si)
        result += r' \ \mathrm{{ {0!s} }}</script>'.format(kunits)

    elif isinstance(kinetics, KineticsData):
        # The kinetics is in KineticsData format
        result += r'<table class="KineticsData">'
        result += r'<tr><th>Temperature</th><th>Rate coefficient</th></tr>'
        for T, k in zip(kinetics.Tdata.value_si, kinetics.kdata.value_si):
            result += r'<tr><td><script type="math/tex">{0:g} \ \mathrm{{ {1!s} }}</script></td><td><script type="math/tex">{2!s} \ \mathrm{{ {3!s} }}</script></td></tr>'.format(T * Tfactor, Tunits, getLaTeXScientificNotation(k * kfactor), kunits)
        result += r'</table>'
        # fit to an arrhenius
        arr = kinetics.to_arrhenius()
        result += "Fitted to an Arrhenius:"
        result += r'<script type="math/tex; mode=display">k(T) = {0!s}</script>'.format(getArrheniusJSMath(
            arr.A.value_si * kfactor, kunits,
            arr.n.value_si, '',
            arr.Ea.value_si * Efactor, Eunits,
            arr.T0.value_si * Tfactor, Tunits,
        ))

    elif isinstance(kinetics, PDepArrhenius):
        # The kinetics is in PDepArrhenius format
        for P, arrh in zip(kinetics.pressures.value_si, kinetics.arrhenius):
            if isinstance(arrh, Arrhenius):
                result += r'<script type="math/tex; mode=display">k(T, {0} \mathrm{{ {1!s} }}) = {2}</script>'.format(
                    getLaTeXScientificNotation(P * Pfactor), Punits,
                    getArrheniusJSMath(
                        arrh.A.value_si * kfactor, kunits,
                        arrh.n.value_si, '',
                        arrh.Ea.value_si * Efactor, Eunits,
                        arrh.T0.value_si * Tfactor, Tunits,
                    ),
                )
            elif isinstance(arrh, MultiArrhenius):
                start = (r'<script type="math/tex; mode=display">'
                         r'k(T, {0} \mathrm{{ {1!s} }}) = '.format(getLaTeXScientificNotation(P * Pfactor), Punits))
                res = ''
                for i, k in enumerate(arrh.arrhenius):
                    start += 'k_{{ {0:d} }}(T, {1} \mathrm{{ {2!s} }}) + '.format(i + 1, getLaTeXScientificNotation(P * Pfactor), Punits)
                    res += r'<script type="math/tex; mode=display">k_{{ {0:d} }}(T, {1} \mathrm{{ {2!s} }}) = {3}</script>'.format(
                        i + 1, getLaTeXScientificNotation(P * Pfactor), Punits,
                        getArrheniusJSMath(
                            k.A.value_si * kfactor, kunits,
                            k.n.value_si, '',
                            k.Ea.value_si * Efactor, Eunits,
                            k.T0.value_si * Tfactor, Tunits,
                        ),
                    )
                result += start[:-3] + '</script>\n' + res + '<br/>'

    elif isinstance(kinetics, Chebyshev):
        # The kinetics is in Chebyshev format
        result += r"""<script type="math/tex; mode=display">
\begin{split}
\log k(T,P) &= \sum_{t=1}^{N_T} \sum_{p=1}^{N_P} C_{tp} \phi_t(\tilde{T}) \phi_p(\tilde{P}) [\mathrm{""" + kinetics.kunits + r""" }] \\
\tilde{T} &\equiv \frac{2T^{-1} - T_\mathrm{min}^{-1} - T_\mathrm{max}^{-1}}{T_\mathrm{max}^{-1} - T_\mathrm{min}^{-1}} \\
\tilde{P} &\equiv \frac{2 \log P - \log P_\mathrm{min} - \log P_\mathrm{max}}{\log P_\mathrm{max} - \log P_\mathrm{min}}
\end{split}</script><br/>
<script type="math/tex; mode=display">\mathbf{C} = \begin{bmatrix}
        """
        for t in range(kinetics.degreeT):
            for p in range(kinetics.degreeP):
                if p > 0:
                    result += ' & '
                result += '{0:g}'.format(kinetics.coeffs.value_si[t, p])
            result += '\\\\ \n'
        result += '\end{bmatrix}</script>'

    elif isinstance(kinetics, Troe):
        # The kinetics is in Troe format
        Fcent = r'(1 - \alpha) \exp \left( -T/T_3 \right) + \alpha \exp \left( -T/T_1 \right) + \exp \left( -T_2/T \right)'
        if kinetics.T2 is not None:
            Fcent += r' + \exp \left( -T_2/T \right)'
        result += r"""<script type="math/tex; mode=display">
\begin{{split}}
k(T,P) &= k_\infty(T) \left[ \frac{{P_\mathrm{{r}}}}{{1 + P_\mathrm{{r}}}} \right] F \\
P_\mathrm{{r}} &= \frac{{k_0(T)}}{{k_\infty(T)}} [\mathrm{{M}}] \\
\log F &= \left\{{1 + \left[ \frac{{\log P_\mathrm{{r}} + c}}{{n - d (\log P_\mathrm{{r}} + c)}} \right]^2 \right\}}^{{-1}} \log F_\mathrm{{cent}} \\
c &= -0.4 - 0.67 \log F_\mathrm{{cent}} \\
n &= 0.75 - 1.27 \log F_\mathrm{{cent}} \\
d &= 0.14 \\
F_\mathrm{{cent}} &= {0}
\end{{split}}
</script><script type="math/tex; mode=display">\begin{{split}}
        """.format(Fcent)
        result += r'k_\infty(T) &= {0!s} \\'.format(getArrheniusJSMath(
            kinetics.arrheniusHigh.A.value_si * kfactor, kunits,
            kinetics.arrheniusHigh.n.value_si, '',
            kinetics.arrheniusHigh.Ea.value_si * Efactor, Eunits,
            kinetics.arrheniusHigh.T0.value_si * Tfactor, Tunits,
        ))
        result += r'k_0(T) &= {0!s} \\'.format(getArrheniusJSMath(
            kinetics.arrheniusLow.A.value_si * kfactor * kfactor, kunits_low,
            kinetics.arrheniusLow.n.value_si, '',
            kinetics.arrheniusLow.Ea.value_si * Efactor, Eunits,
            kinetics.arrheniusLow.T0.value_si * Tfactor, Tunits,
        ))
        result += r'\alpha &= {0:g} \\'.format(kinetics.alpha)
        result += r'T_3 &= {0:g} \ \mathrm{{ {1!s} }} \\'.format(kinetics.T3.value_si * Tfactor, Tunits)
        result += r'T_1 &= {0:g} \ \mathrm{{ {1!s} }} \\'.format(kinetics.T1.value_si * Tfactor, Tunits)
        if kinetics.T2 is not None:
            result += r'T_2 &= {0:g} \ \mathrm{{ {1!s} }} \\'.format(kinetics.T2.value_si * Tfactor, Tunits)
        result += r'\end{split}</script>'

    elif isinstance(kinetics, Lindemann):
        # The kinetics is in Lindemann format
        result += r"""<script type="math/tex; mode=display">
\begin{{split}}
k(T,P) &= k_\infty(T) \left[ \frac{{P_\mathrm{{r}}}}{{1 + P_\mathrm{{r}}}} \right] \\
P_\mathrm{{r}} &= \frac{{k_0(T)}}{{k_\infty(T)}} [\mathrm{{M}}] \\
\end{{split}}
</script><script type="math/tex; mode=display">\begin{{split}}
        """.format()
        result += r'k_\infty(T) &= {0!s} \\'.format(getArrheniusJSMath(
            kinetics.arrheniusHigh.A.value_si * kfactor, kunits,
            kinetics.arrheniusHigh.n.value_si, '',
            kinetics.arrheniusHigh.Ea.value_si * Efactor, Eunits,
            kinetics.arrheniusHigh.T0.value_si * Tfactor, Tunits,
        ))
        result += r'k_0(T) &= {0!s} \\'.format(getArrheniusJSMath(
            kinetics.arrheniusLow.A.value_si * kfactor * kfactor, kunits_low,
            kinetics.arrheniusLow.n.value_si, '',
            kinetics.arrheniusLow.Ea.value_si * Efactor, Eunits,
            kinetics.arrheniusLow.T0.value_si * Tfactor, Tunits,
        ))
        result += r'\end{split}</script>'

    elif isinstance(kinetics, ThirdBody):
        # The kinetics is in ThirdBody format
        result += r"""<script type="math/tex; mode=display">
k(T,P) = k_0(T) [\mathrm{{M}}]
</script><script type="math/tex; mode=display">
        """.format()
        result += r'k_0(T) = {0!s}'.format(getArrheniusJSMath(
            kinetics.arrheniusLow.A.value_si * kfactor * kfactor, kunits_low,
            kinetics.arrheniusLow.n.value_si, '',
            kinetics.arrheniusLow.Ea.value_si * Efactor, Eunits,
            kinetics.arrheniusLow.T0.value_si * Tfactor, Tunits,
        ))
        result += '</script>'

    elif isinstance(kinetics, (MultiArrhenius, MultiPDepArrhenius)):
        # The kinetics is in MultiArrhenius or MultiPDepArrhenius format
        result = ''
        start = r'<script type="math/tex; mode=display">k(T, P) = '
        for i, k in enumerate(kinetics.arrhenius):
            res = render_kinetics_math(k, user=user)
            start += 'k_{{ {0:d} }}(T, P) + '.format(i+1)
            result += res.replace('k(T', 'k_{{ {0:d} }}(T'.format(i+1)) + '<br/>'

        result = start[:-3] + '</script><br/>' + result

    # Collision efficiencies
    if hasattr(kinetics, 'efficiencies') and kinetics.efficiencies:
        result += '<table>\n'
        result += '<tr><th colspan="2">Collision efficiencies</th></tr>'
        for smiles, eff in kinetics.efficiencies.items():
            result += '<tr><td>{0}</td><td>{1:g}</td></tr>\n'.format(getStructureMarkup(smiles), eff)
        result += '</table><br/>\n'

    # Temperature and pressure ranges
    result += '<table class="kineticsEntryData">'
    if kinetics.Tmin is not None and kinetics.Tmax is not None:
        result += '<tr><td class="key">Temperature range</td><td class="equals">=</td><td class="value">{0:g} to {1:g} {2!s}</td></tr>'.format(kinetics.Tmin.value_si * Tfactor, kinetics.Tmax.value_si * Tfactor, Tunits)
    if kinetics.Pmin is not None and kinetics.Pmax is not None:
        result += '<tr><td class="key">Pressure range</td><td class="equals">=</td><td class="value">{0:g} to {1:g} {2!s}</td></tr>'.format(kinetics.Pmin.value_si * Pfactor, kinetics.Pmax.value_si * Pfactor, Punits)
    result += '</table>'

    return mark_safe(result)

################################################################################


@register.filter
def get_rate_coefficients(kinetics, user=None):
    """
    Generate and return a set of :math:`k(T,P)` data suitable for plotting
    using Highcharts. If a `user` is specified, the user's preferred units
    will be used; otherwise default units will be used.
    If `user=='A_n_Ea'` then it fits an Arrhenius expression and returns
    the parameters (and their units).
    """
    if kinetics is None:
        return "// There are no kinetics for this entry."

    if user == "A_n_Ea":
        # Not a user, but a request to just return the Arrhenius coefficients
        return_A_n_Ea = True
        user = None
    else:
        return_A_n_Ea = False

    # Define other units and conversion factors to use
    if user and user.is_authenticated():
        user_profile = UserProfile.objects.get(user=user)
        Tunits = user_profile.temperature_units
        Punits = user_profile.pressure_units
        Eunits = user_profile.energy_units
    else:
        Tunits = 'K'
        Punits = 'Pa'
        Eunits = 'J/mol'
    kunits, kunits_low, kfactor = getRateCoefficientUnits(kinetics, user=user)
    Tfactor = Quantity(1, Tunits).get_conversion_factor_from_si()
    Pfactor = Quantity(1, Punits).get_conversion_factor_from_si()
    Efactor = Quantity(1, Eunits).get_conversion_factor_from_si()

    # Generate data to use for plots
    Tdata = []
    Pdata = []
    kdata = []
    if kinetics.Tmin is not None and kinetics.Tmax is not None:
        if kinetics.Tmin.value_si == kinetics.Tmax.value_si:
            Tmin = kinetics.Tmin.value_si - 5
            Tmax = kinetics.Tmax.value_si + 5
        else:
            Tmin = kinetics.Tmin.value_si
            Tmax = kinetics.Tmax.value_si
    else:
        Tmin = 300
        Tmax = 2000
    if kinetics.Pmin is not None and kinetics.Pmax is not None:
        Pmin = kinetics.Pmin.value_si
        Pmax = kinetics.Pmax.value_si
    else:
        Pmin = 1e3
        Pmax = 1e7

    # Number of points in Tlist (ten times that in Pdep's Tlist2)
    points = 50

    for Tinv in np.linspace(1.0 / Tmax, 1.0 / Tmin, points):
        Tdata.append(1.0 / Tinv)
    if kinetics.is_pressure_dependent():
        for logP in np.arange(math.log10(Pmin), math.log10(Pmax)+0.001, 1):
            Pdata.append(10**logP)
        for P in Pdata:
            klist = []
            for T in Tdata:
                klist.append(kinetics.get_rate_coefficient(T, P) * kfactor)
            kdata.append(klist)
    elif isinstance(kinetics, ArrheniusEP):
        for T in Tdata:
            kdata.append(kinetics.get_rate_coefficient(T, dHrxn=0) * kfactor)
    elif isinstance(kinetics, (StickingCoefficient, StickingCoefficientBEP)):
        for T in Tdata:
            kdata.append(kinetics.get_sticking_coefficient(T) * kfactor)
    else:
        for T in Tdata:
            kdata.append(kinetics.get_rate_coefficient(T) * kfactor)

    Tdata2 = []
    Pdata2 = []
    kdata2 = []
    for Tinv in np.linspace(1.0 / Tmax, 1.0 / Tmin, points // 10):
        Tdata2.append(1.0 / Tinv)
    if kinetics.is_pressure_dependent():
        for logP in np.arange(math.log10(Pmin), math.log10(Pmax)+0.001, 0.1):
            Pdata2.append(10**logP)
        for P in Pdata2:
            klist = []
            for T in Tdata2:
                klist.append(kinetics.get_rate_coefficient(T, P) * kfactor)
            kdata2.append(klist)
    elif isinstance(kinetics, ArrheniusEP):
        for T in Tdata2:
            kdata2.append(kinetics.get_rate_coefficient(T, dHrxn=0) * kfactor)
    elif isinstance(kinetics, (StickingCoefficient, StickingCoefficientBEP)):
        for T in Tdata:
            kdata2.append(kinetics.get_sticking_coefficient(T) * kfactor)
    else:
        for T in Tdata2:
            kdata2.append(kinetics.get_rate_coefficient(T) * kfactor)

    if return_A_n_Ea:
        "We are only interested in the (fitted) Arrhenius parameters (and their units)"
        Tlist = np.array([T * Tfactor for T in Tdata], np.float64)

        if kinetics.is_pressure_dependent():
            # Use the highest pressure we have available
            klist = np.array(kdata[-1], np.float64)
            pressure_note = " (At {0} {1})".format(Pdata[-1], Punits)
            k_model = Arrhenius().fit_to_data(Tlist, klist, kunits)
        elif isinstance(kinetics, (StickingCoefficient, StickingCoefficientBEP)):
            klist = np.array(kdata, np.float64)
            pressure_note = ""
            k_model = StickingCoefficient().fit_to_data(Tlist, klist, kunits)
        elif isinstance(kinetics, (SurfaceArrhenius, SurfaceArrheniusBEP)):
            klist = np.array(kdata, np.float64)
            pressure_note = ""
            k_model = SurfaceArrhenius().fit_to_data(Tlist, klist, kunits)
        else:
            klist = np.array(kdata, np.float64)
            pressure_note = ""
            k_model = Arrhenius().fit_to_data(Tlist, klist, kunits)

        return mark_safe("""A = {0}; n = {1}; Ea = {2}; Aunits = "{3}"; Eunits = "{4}"; Pnote = "{5}";""".format(
                            k_model.A.value_si * kfactor,
                            k_model.n.value_si,
                            k_model.Ea.value_si * Efactor,
                            kunits,
                            Eunits,
                            pressure_note
                        ))

    return mark_safe("""Tlist = {0};Plist = {1};klist = {2};
                        Tlist2 = {3};Plist2 = {4}; klist2 = {5};
                        Tunits = "{6}";Punits = "{7}";kunits = "{8}";""".format(
                             [T * Tfactor for T in Tdata],
                             [P * Pfactor for P in Pdata],
                             kdata,
                             [T * Tfactor for T in Tdata2],
                             [P * Pfactor for P in Pdata2],
                             kdata2,
                             Tunits,
                             Punits,
                             kunits,
                         ))


###############################################################################

@register.filter
def get_specific_rate(kinetics, eval):
    """
    Return the rate in nice units given a specified temperature.
    Outputs in pretty Latex scientific notation.
    """
    if kinetics is None:
        return "// There are no kinetics for this entry."
    temperature, pressure = eval
    kunits, kunits_low, kfactor = getRateCoefficientUnits(kinetics)
    rate = kinetics.get_rate_coefficient(temperature, pressure)*kfactor
    result = '<script type="math/tex; mode=display">k(T, P) = {0!s}'.format(getLaTeXScientificNotation(rate))
    result += '\ \mathrm{{ {0!s} }}</script>'.format(kunits)
    return mark_safe(result)

###############################################################################


@register.filter
def get_user_kfactor(kinetics, user=None):
    """
    Return the scaling factor required for average kinetics plotting.
    """
    kunits, kunits_low, kfactor = getRateCoefficientUnits(kinetics, user=user)

    return mark_safe("""kfactor = {0};""".format(kfactor))
