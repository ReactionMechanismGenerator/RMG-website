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
Provides template tags for rendering kinetics models in various ways.
"""

# Register this module as a Django template tag library
from django import template
register = template.Library()

from django.utils.safestring import mark_safe

import math
import numpy

from rmgweb.main.tools import getLaTeXScientificNotation, getStructureMarkup
from rmgweb.main.models import UserProfile

from rmgpy.quantity import Quantity
from rmgpy.kinetics import *

################################################################################

def getNumberOfReactantsFromUnits(units):
    si_units = {
        's^-1': 1,
        's**-1': 1,
        'm^3/(mol*s)': 2,
        'm**3/(mol*s)': 2,
        'm^3/mol/s': 2,
        'm**3/mol/s': 2,
        'cm^3/(mol*s)': 2,
        'cm**3/(mol*s)': 2,
        'cm^3/mol/s': 2,
        'cm**3/mol/s': 2,
        'm^3/(molecule*s)': 2,
        'm**3/(molecule*s)': 2,
        'm^3/molecule/s': 2,
        'm**3/molecule/s': 2,
        'cm^3/(molecule*s)': 2,
        'cm**3/(molecule*s)': 2,
        'cm^3/molecule/s': 2,
        'cm**3/molecule/s': 2,
        'm^6/(mol^2*s)': 3,
        'm**6/(mol^2*s)': 3,
        'm^6/mol^2/s': 3,
        'm**6/mol^2/s': 3,
        'cm^6/(mol^2*s)': 3,
        'cm**6/(mol^2*s)': 3,
        'cm^6/mol^2/s': 3,
        'cm**6/mol^2/s': 3,
        'm^6/(molecule^2*s)': 3,
        'm**6/(molecule^2*s)': 3,
        'm^6/molecule^2/s': 3,
        'm**6/molecule^2/s': 3,
        'cm^6/(molecule^2*s)': 3,
        'cm**6/(molecule^2*s)': 3,
        'cm^6/molecule^2/s': 3,
        'cm**6/molecule^2/s': 3,
    }
    return si_units[units]

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

def getRateCoefficientUnits(kinetics, user=None):
    """
    For a given `kinetics` model, return the desired rate coefficient units
    at high and low pressures, the conversion factor from SI to those units
    (high pressure), and the number of reactant species. If a `user` is 
    specified, the user's preferred units will be used; otherwise default units
    will be used.
    """
    
    # Determine the number of reactants based on the units of one of the
    # kinetic parameters (which to use depends on the model)
    numReactants = 0
    if isinstance(kinetics, Arrhenius):
        numReactants = getNumberOfReactantsFromUnits(kinetics.A.units)
    elif isinstance(kinetics, ArrheniusEP):
        numReactants = getNumberOfReactantsFromUnits(kinetics.A.units)
    elif isinstance(kinetics, KineticsData):
        numReactants = getNumberOfReactantsFromUnits(kinetics.kdata.units)
    elif isinstance(kinetics, PDepArrhenius):
        numReactants = getNumberOfReactantsFromUnits(kinetics.arrhenius[0].A.units)
    elif isinstance(kinetics, Chebyshev):
        numReactants = getNumberOfReactantsFromUnits(kinetics.kunits)
    elif isinstance(kinetics, Troe):
        numReactants = getNumberOfReactantsFromUnits(kinetics.arrheniusHigh.A.units)
    elif isinstance(kinetics, Lindemann):
        numReactants = getNumberOfReactantsFromUnits(kinetics.arrheniusHigh.A.units)
    elif isinstance(kinetics, ThirdBody):
        numReactants = getNumberOfReactantsFromUnits(kinetics.arrheniusLow.A.units)
    elif isinstance(kinetics, MultiArrhenius):
        return getRateCoefficientUnits(kinetics.arrhenius[0])
    elif isinstance(kinetics, MultiPDepArrhenius):
        return getRateCoefficientUnits(kinetics.arrhenius[0])
    
    # Use the number of reactants to get the rate coefficient units and conversion factor
    kunitsDict = {
        1: 's^-1',
        2: 'm^3/(mol*s)',
        3: 'm^6/(mol^2*s)',
        4: 'm^9/(mol^3*s)',
    }
    if user and user.is_authenticated():
        user_profile = UserProfile.objects.get(user=user)
        if user_profile.rateCoefficientUnits == 'm^3,mol,s':
            kunitsDict = {
                1: 's^-1',
                2: 'm^3/(mol*s)',
                3: 'm^6/(mol^2*s)',
                4: 'm^9/(mol^3*s)',
            }
        elif user_profile.rateCoefficientUnits == 'cm^3,mol,s':
            kunitsDict = {
                1: 's^-1',
                2: 'cm^3/(mol*s)',
                3: 'cm^6/(mol^2*s)',
                4: 'cm^9/(mol^3*s)',
            }
        elif user_profile.rateCoefficientUnits == 'm^3,molecule,s':
            kunitsDict = {
                1: 's^-1',
                2: 'm^3/(molecule*s)',
                3: 'm^6/(molecule^2*s)',
                4: 'm^9/(molecule^3*s)',
            }
        elif user_profile.rateCoefficientUnits == 'cm^3,molecule,s':
            kunitsDict = {
                1: 's^-1',
                2: 'cm^3/(molecule*s)',
                3: 'cm^6/(molecule^2*s)',
                4: 'cm^9/(molecule^3*s)',
            }
            
    kunits = kunitsDict[numReactants]
    kunits_low = kunitsDict[numReactants+1]
    kfactor = Quantity(1, kunits).getConversionFactorFromSI()
    
    return kunits, kunits_low, kfactor, numReactants

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
        Tunits = str(user_profile.temperatureUnits)
        Punits = str(user_profile.pressureUnits)
        Eunits = str(user_profile.energyUnits)
    else:
        Tunits = 'K'
        Punits = 'Pa'
        Eunits = 'J/mol'
    kunits, kunits_low, kfactor, numReactants = getRateCoefficientUnits(kinetics, user=user)
    Tfactor = Quantity(1, Tunits).getConversionFactorFromSI()
    Pfactor = Quantity(1, Punits).getConversionFactorFromSI()
    Efactor = Quantity(1, Eunits).getConversionFactorFromSI()
    if kunits == 's^-1':
        kunits = 's^{-1}'   
    
    # The string that will be returned to the template
    result = ''
    
    if isinstance(kinetics, Arrhenius):
        # The kinetics is in Arrhenius format
        result += r'<script type="math/tex; mode=display">k(T) = {0!s}</script>'.format(getArrheniusJSMath(
            kinetics.A.value_si * kfactor, kunits, 
            kinetics.n.value_si, '', 
            kinetics.Ea.value_si * Efactor, Eunits, 
            kinetics.T0.value_si * Tfactor, Tunits,
        ))
    
    elif isinstance(kinetics, ArrheniusEP):
        # The kinetics is in ArrheniusEP format
        result += r'<script type="math/tex; mode=display">k(T) = {0!s}'.format(getLaTeXScientificNotation(kinetics.A.value_si * kfactor))
        if kinetics.n.value_si != 0:
            result += r' T^{{ {0:.2f} }}'.format(kinetics.n.value_si)
        result += r' \exp \left( - \, \frac{{ {0:.2f} \ \mathrm{{ {1!s} }} + {2:.2f} \Delta H_\mathrm{{rxn}}^\circ }}{{ R T }} \right)'.format(kinetics.E0.value_si * Efactor, Eunits, kinetics.alpha.value_si)
        result += ' \ \mathrm{{ {0!s} }}</script>'.format(kunits)
    
    elif isinstance(kinetics, KineticsData):
        # The kinetics is in KineticsData format
        result += r'<table class="KineticsData">'
        result += r'<tr><th>Temperature</th><th>Rate coefficient</th></tr>'
        for T, k in zip(kinetics.Tdata.value_si, kinetics.kdata.value_si):
            result += r'<tr><td><script type="math/tex">{0:g} \ \mathrm{{ {1!s} }}</script></td><td><script type="math/tex">{2!s} \ \mathrm{{ {3!s} }}</script></td></tr>'.format(T * Tfactor, Tunits, getLaTeXScientificNotation(k * kfactor), kunits)
        result += r'</table>'
        # fit to an arrhenius
        arr = kinetics.toArrhenius()
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
            result += r'<script type="math/tex; mode=display">k(T, \ {0:.3g} \ \mathrm{{ {1!s} }}) = {2}</script>'.format(
                P * Pfactor, Punits, 
                getArrheniusJSMath(
                    arrh.A.value_si * kfactor, kunits, 
                    arrh.n.value_si, '', 
                    arrh.Ea.value_si * Efactor, Eunits, 
                    arrh.T0.value_si * Tfactor, Tunits,
                ),
            )
            
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
                if p > 0: result += ' & '
                result += '{0:g}'.format(kinetics.coeffs.value_si[t,p])
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
        
    elif isinstance(kinetics, (MultiArrhenius,MultiPDepArrhenius)):
        # The kinetics is in MultiArrhenius or MultiPDepArrhenius format
        result = ''
        start = ''
        for i, k in enumerate(kinetics.arrhenius):
            res = render_kinetics_math(k, user=user)
            start += '{0} + '.format(res.split(' = ')[0].replace('<div class="math">k(T', 'k_{{ {0:d} }}(T'.format(i+1), 1))
            result += res.replace('k(T', 'k_{{ {0:d} }}(T'.format(i+1), 1) + '<br/>'
        
        result = r"""<script type="math/tex; mode=display">
k(T,P) = {0!s}
</script><br/>
        """.format(start[:-3]) + result

    # Collision efficiencies
    if hasattr(kinetics, 'efficiencies'):
        result += '<table>\n'
        result += '<tr><th colspan="2">Collision efficiencies</th></tr>'
        for smiles, eff in kinetics.efficiencies.iteritems():
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
        Tunits = str(user_profile.temperatureUnits)
        Punits = str(user_profile.pressureUnits)
        Eunits = str(user_profile.energyUnits)
    else:
        Tunits = 'K'
        Punits = 'Pa'
        Eunits = 'J/mol'
    kunits, kunits_low, kfactor, numReactants = getRateCoefficientUnits(kinetics, user=user)
    Tfactor = Quantity(1, Tunits).getConversionFactorFromSI()
    Pfactor = Quantity(1, Punits).getConversionFactorFromSI()
    Efactor = Quantity(1, Eunits).getConversionFactorFromSI()
        
    # Generate data to use for plots
    Tdata = []; Pdata = []; kdata = []
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
    
    for Tinv in numpy.linspace(1.0 / Tmax, 1.0 / Tmin, points):
        Tdata.append(1.0 / Tinv)
    if kinetics.isPressureDependent():
        for logP in numpy.arange(math.log10(Pmin), math.log10(Pmax)+0.001, 1):
            Pdata.append(10**logP)
        for P in Pdata:
            klist = []
            for T in Tdata:
                klist.append(kinetics.getRateCoefficient(T,P) * kfactor)
            kdata.append(klist)
    elif isinstance(kinetics, ArrheniusEP):
        for T in Tdata:
            kdata.append(kinetics.getRateCoefficient(T, dHrxn=0) * kfactor)
    else:
        for T in Tdata:
            kdata.append(kinetics.getRateCoefficient(T) * kfactor)
    
    Tdata2 = []; Pdata2 = []; kdata2 = []
    for Tinv in numpy.linspace(1.0 / Tmax, 1.0 / Tmin, points / 10):
        Tdata2.append(1.0 / Tinv)
    if kinetics.isPressureDependent():
        for logP in numpy.arange(math.log10(Pmin), math.log10(Pmax)+0.001, 0.1):
            Pdata2.append(10**logP)
        for P in Pdata2:
            klist = []
            for T in Tdata2:
                klist.append(kinetics.getRateCoefficient(T,P) * kfactor)
            kdata2.append(klist)
    elif isinstance(kinetics, ArrheniusEP):
        for T in Tdata2:
            kdata2.append(kinetics.getRateCoefficient(T, dHrxn=0) * kfactor)
    else:
        for T in Tdata2:
            kdata2.append(kinetics.getRateCoefficient(T) * kfactor)
    
    if return_A_n_Ea:
        "We are only interested in the (fitted) Arrhenius parameters (and their units)"
        Tlist = numpy.array([T * Tfactor for T in Tdata], numpy.float64)
        
        if kinetics.isPressureDependent():
            # Use the highest pressure we have available
            klist = numpy.array(kdata[-1], numpy.float64)
            pressure_note = " (At {0} {1})".format(Pdata[-1],Punits)
        else:
            klist = numpy.array(kdata, numpy.float64)
            pressure_note = ""

        kModel = Arrhenius().fitToData(Tlist, klist, kunits)
    
        return mark_safe("""A = {0}; n = {1}; Ea = {2}; Aunits = "{3}"; Eunits = "{4}"; Pnote = "{5}";""".format(
                            kModel.A.value_si * kfactor,
                            kModel.n.value_si,
                            kModel.Ea.value_si * Efactor,
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
    kunits, kunits_low, kfactor, numReactants = getRateCoefficientUnits(kinetics)
    rate = kinetics.getRateCoefficient(temperature, pressure)*kfactor
    result = '<script type="math/tex; mode=display">k(T, P) = {0!s}'.format(getLaTeXScientificNotation(rate))
    result += '\ \mathrm{{ {0!s} }}</script>'.format(kunits)
    return mark_safe(result)

###############################################################################

@register.filter
def get_user_kfactor(kinetics, user=None):
    """
    Return the scaling factor required for average kinetics plotting.
    """
    kunits, kunits_low, kfactor, numReactants = getRateCoefficientUnits(kinetics, user=user)
    
    return mark_safe("""kfactor = {0};""".format(kfactor))
