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

from rmgweb.main.tools import getLaTeXScientificNotation, getStructureMarkup

from rmgpy.quantity import Quantity
from rmgpy.kinetics import *

################################################################################

def getNumberOfReactantsFromUnits(units):
    si_units = {
        's^-1': 1,
        'm^3/(mol*s)': 2,
        'cm^3/(mol*s)': 2,
        'm^3/(molecule*s)': 2,
        'cm^3/(molcule*s)': 2,
    }
    return si_units[units]

def getArrheniusJSMath(A, Aunits, n, nunits, Ea, Eaunits, T0, T0units):
    result = '{0!s}'.format(getLaTeXScientificNotation(A))
    if n != 0:
        if T0 != 1:
            result += r' \left( \frac{T}{{ {0:g} \ \mathrm{{ {1!s} }} }} \right)^{{ {2:.2f} }}'.format(T0, T0units, n)
        else:
            result += r' T^{{ {0:.2f} }}'.format(n)
    if Ea != 0:
        result += r' \exp \left( - \, \frac{{ {0:.2f} \ \mathrm{{ {1!s} }} }}{{ R T }} \right)'.format(Ea, Eaunits)
    result += ' \ \mathrm{{ {0!s} }}'.format(Aunits)
    return result

def getRateCoefficientUnits(kinetics):
    """
    For a given `kinetics` model, return the desired rate coefficient units
    at high and low pressures, the conversion factor from SI to those units
    (high pressure), and the number of reactant species.    
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
    elif isinstance(kinetics, ThirdBody): # also matches Lindemann and Troe
        numReactants = getNumberOfReactantsFromUnits(kinetics.arrheniusHigh.A.units)
    elif isinstance(kinetics, MultiKinetics):
        return getRateCoefficientUnits(kinetics.kineticsList[0])
    
    # Use the number of reactants to get the rate coefficient units and conversion factor
    if numReactants == 1:
        kunits = 's^-1'
        kunits_low = 'cm^3/(mol*s)'
    elif numReactants == 2:
        kunits = 'cm^3/(mol*s)'
        kunits_low = 'cm^6/(mol^2*s)'
    elif numReactants == 3:
        kunits = 'cm^6/(mol^2*s)'
        kunits_low = 'cm^9/(mol^3*s)'
    else:
        kunits = ''
        kunits_low = ''
        
    kfactor = Quantity(1, kunits).getConversionFactorFromSI()
    
    return kunits, kunits_low, kfactor, numReactants

################################################################################

@register.filter
def render_kinetics_math(kinetics):
    """
    Return a math representation of the given `kinetics` using jsMath.
    """
    
    # Define other units and conversion factors to use
    Tunits = 'K'
    Tfactor = Quantity(1, Tunits).getConversionFactorFromSI()
    Punits = 'bar'
    Pfactor = Quantity(1, Punits).getConversionFactorFromSI()
    Eunits = 'kcal/mol'
    Efactor = Quantity(1, Eunits).getConversionFactorFromSI()
    kunits, kunits_low, kfactor, numReactants = getRateCoefficientUnits(kinetics)
    if kunits == 's^-1':
        kunits = 's^{-1}'   
    
    # The string that will be returned to the template
    result = ''
    
    if isinstance(kinetics, Arrhenius):
        # The kinetics is in Arrhenius format
        result += r'<div class="math">k(T) = {0!s}</div>'.format(getArrheniusJSMath(
            kinetics.A.value * kfactor, kunits, 
            kinetics.n.value, '', 
            kinetics.Ea.value * Efactor, Eunits, 
            kinetics.T0.value * Tfactor, Tunits,
        ))
    
    elif isinstance(kinetics, ArrheniusEP):
        # The kinetics is in ArrheniusEP format
        result += r'<div class="math">k(T) = {0!s}'.format(getLaTeXScientificNotation(kinetics.A.value * kfactor))
        if kinetics.n.value != 0:
            result += r' T^{{ {0:.2f} }}'.format(kinetics.n.value)
        result += r' \exp \left( - \, \frac{{ {0:.2f} \ \mathrm{{ {1!s} }} + {2:.2f} \Delta H_\mathrm{{rxn}}^\circ }}{{ R T }} \right)'.format(kinetics.E0.value * Efactor, Eunits, kinetics.alpha.value)
        result += ' \ \mathrm{{ {0!s} }}</div>'.format(kunits)
    
    elif isinstance(kinetics, KineticsData):
        # The kinetics is in KineticsData format
        result += r'<table>'
        result += r'<tr><th>Temperature</th><th>Rate coefficient</th></tr>'
        for T, k in zip(kinetics.Tdata.values, kinetics.kdata.values):
            result += r'<tr><td><span class="math">{0:g} \ \mathrm{{ {1!s} }}</span></td><td><span class="math">{2!s} \ \mathrm{{ {3!s} }}</span></td></tr>'.format(T * Tfactor, Tunits, getLaTeXScientificNotation(k * kfactor), kunits)
        result += r'</table>'
        
    elif isinstance(kinetics, PDepArrhenius):
        # The kinetics is in PDepArrhenius format
        for P, arrh in zip(kinetics.pressures.values, kinetics.arrhenius):
            result += r'<div class="math">k(T, \ {0:g} \ \mathrm{{ {1!s} }}) = {2}</div>'.format(
                P * Pfactor, Punits, 
                getArrheniusJSMath(
                    arrh.A.value * kfactor, kunits, 
                    arrh.n.value, '', 
                    arrh.Ea.value * Efactor, Eunits, 
                    arrh.T0.value * Tfactor, Tunits,
                ),
            )
            
    elif isinstance(kinetics, Chebyshev):
        # The kinetics is in Chebyshev format
        result += r"""<div class="math">
\begin{split}
\log k(T,P) &= \sum_{t=1}^{N_T} \sum_{p=1}^{N_P} C_{tp} \phi_t(\tilde{T}) \phi_p(\tilde{P}) [\mathrm{ {{ kineticsParameters.coeffs.1 }} }] \\
\tilde{T} &\equiv \frac{2T^{-1} - T_\mathrm{min}^{-1} - T_\mathrm{max}^{-1}}{T_\mathrm{max}^{-1} - T_\mathrm{min}^{-1}} \\
\tilde{P} &\equiv \frac{2 \log P - \log P_\mathrm{min} - \log P_\mathrm{max}}{\log P_\mathrm{max} - \log P_\mathrm{min}}
\end{split}</div><br/>
<div class="math">\mathbf{C} = \begin{bmatrix}
        """
        for t in range(kinetics.degreeT):
            for p in range(kinetics.degreeP):
                if p > 0: result += ' & '
                result += '{0:g}'.format(kinetics.coeffs[t,p])
            result += '\\\\ \n'
        result += '\end{bmatrix}</div>'
    
    elif isinstance(kinetics, Troe):
        # The kinetics is in Troe format
        Fcent = r'(1 - \alpha) \exp \left( -T/T_3 \right) + \alpha \exp \left( -T/T_1 \right) + \exp \left( -T_2/T \right)'
        if kinetics.T2 is not None:
            Fcent += r' + \exp \left( -T_2/T \right)'
        result += r"""<div class="math">
\begin{{split}}
k(T,P) &= k_\infty(T) \left[ \frac{{P_\mathrm{{r}}}}{{1 + P_\mathrm{{r}}}} \right] F \\
P_\mathrm{{r}} &= \frac{{k_0(T)}}{{k_\infty(T)}} [\mathrm{{M}}] \\
\log F &= \left\{{1 + \left[ \frac{{\log P_\mathrm{{r}} + c}}{{n - d (\log P_\mathrm{{r}} + c)}} \right]^2 \right\}}^{{-1}} \log F_\mathrm{{cent}} \\
c &= -0.4 - 0.67 \log F_\mathrm{{cent}} \\
n &= 0.75 - 1.27 \log F_\mathrm{{cent}} \\
d &= 0.14 \\
F_\mathrm{{cent}} &= {0}
\end{{split}}
</div><div class="math">\begin{{split}}
        """.format(Fcent)
        result += r'k_\infty(T) &= {0!s} \\'.format(getArrheniusJSMath(
            kinetics.arrheniusHigh.A.value * kfactor, kunits, 
            kinetics.arrheniusHigh.n.value, '', 
            kinetics.arrheniusHigh.Ea.value * Efactor, Eunits, 
            kinetics.arrheniusHigh.T0.value * Tfactor, Tunits,
        ))
        result += r'k_0(T) &= {0!s} \\'.format(getArrheniusJSMath(
            kinetics.arrheniusLow.A.value * kfactor * kfactor, kunits_low, 
            kinetics.arrheniusLow.n.value, '', 
            kinetics.arrheniusLow.Ea.value * Efactor, Eunits, 
            kinetics.arrheniusLow.T0.value * Tfactor, Tunits,
        ))
        result += r'\alpha &= {0:g} \\'.format(kinetics.alpha.value)
        result += r'T_3 &= {0:g} \ \mathrm{{ {1!s} }} \\'.format(kinetics.T3.value * Tfactor, Tunits)
        result += r'T_1 &= {0:g} \ \mathrm{{ {1!s} }} \\'.format(kinetics.T1.value * Tfactor, Tunits)
        if kinetics.T2 is not None:
            result += r'T_2 &= {0:g} \ \mathrm{{ {1!s} }} \\'.format(kinetics.T2.value * Tfactor, Tunits)
        result += r'\end{split}</div>'
    
    elif isinstance(kinetics, Lindemann):
        # The kinetics is in Lindemann format
        result += r"""<div class="math">
\begin{{split}}
k(T,P) &= k_\infty(T) \left[ \frac{{P_\mathrm{{r}}}}{{1 + P_\mathrm{{r}}}} \right] \\
P_\mathrm{{r}} &= \frac{{k_0(T)}}{{k_\infty(T)}} [\mathrm{{M}}] \\
\end{{split}}
</div><div class="math">\begin{{split}}
        """.format()
        result += r'k_\infty(T) &= {0!s} \\'.format(getArrheniusJSMath(
            kinetics.arrheniusHigh.A.value * kfactor, kunits, 
            kinetics.arrheniusHigh.n.value, '', 
            kinetics.arrheniusHigh.Ea.value * Efactor, Eunits, 
            kinetics.arrheniusHigh.T0.value * Tfactor, Tunits,
        ))
        result += r'k_0(T) &= {0!s} \\'.format(getArrheniusJSMath(
            kinetics.arrheniusLow.A.value * kfactor * kfactor, kunits_low, 
            kinetics.arrheniusLow.n.value, '', 
            kinetics.arrheniusLow.Ea.value * Efactor, Eunits, 
            kinetics.arrheniusLow.T0.value * Tfactor, Tunits,
        ))
        result += r'\end{split}</div>'
    
    elif isinstance(kinetics, ThirdBody):
        # The kinetics is in ThirdBody format
        result += r"""<div class="math">
k(T,P) = k_0(T) [\mathrm{{M}}]
</div><div class="math">
        """.format()
        result += r'k_0(T) = {0!s}'.format(getArrheniusJSMath(
            kinetics.arrheniusHigh.A.value * kfactor * kfactor, kunits_low, 
            kinetics.arrheniusHigh.n.value, '', 
            kinetics.arrheniusHigh.Ea.value * Efactor, Eunits, 
            kinetics.arrheniusHigh.T0.value * Tfactor, Tunits,
        ))
        result += '</div>'
        
    elif isinstance(kinetics, MultiKinetics):
        # The kinetics is in MultiKinetics format
        result = ''
        start = ''
        for i, k in enumerate(kinetics.kineticsList):
            res = render_kinetics_math(k)
            start += '{0} + '.format(res.split(' = ')[0].replace('<div class="math">k(T', 'k_{{ {0:d} }}(T'.format(i+1), 1))
            result += res.replace('k(T', 'k_{{ {0:d} }}(T'.format(i+1), 1) + '<br/>'
        
        result = r"""<div class="math">
k(T,P) = {0!s}
</div><br/>
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
        result += '<tr><td class="key">Temperature range</td><td class="equals">=</td><td class="value">{0:g} to {1:g} {2!s}</td></tr>'.format(kinetics.Tmin.value * Tfactor, kinetics.Tmax.value * Tfactor, Tunits)
    if kinetics.Pmin is not None and kinetics.Pmax is not None:
        result += '<tr><td class="key">Pressure range</td><td class="equals">=</td><td class="value">{0:g} to {1:g} {2!s}</td></tr>'.format(kinetics.Pmin.value * Pfactor, kinetics.Pmax.value * Pfactor, Punits)
    result += '</table>'

    return mark_safe(result)
