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

import math
import re

from django.core.urlresolvers import reverse

################################################################################

def getLaTeXScientificNotation(value):
    """
    Return a LaTeX-formatted string containing the provided `value` in
    scientific notation.
    """
    if value == 0: return '%g' % 0
    exp = int(math.log10(abs(value)))
    mant = value / 10**exp
    if abs(mant) < 1:
        mant *= 10; exp -= 1
    return '%g \\times 10^{%i}' % (mant, exp)

################################################################################

def getStructureMarkup(item):
    """
    Return the HTML used to markup structure information for the given `item`.
    For a :class:`Molecule`, the markup is an ``<img>`` tag so that we can
    draw the molecule. For a :class:`Group`, the markup is the
    adjacency list, wrapped in ``<pre>`` tags.
    """
    from rmgpy.molecule import Molecule
    from rmgpy.group import Group
    from rmgpy.species import Species
    
    if isinstance(item, Molecule):
        # We can draw Molecule objects, so use that instead of an adjacency list
        adjlist = item.toAdjacencyList(removeH=True)
        adjlist = adjlist.replace('\n', ';')
        adjlist = re.sub('\s+', '%20', adjlist)
        structure = '<img src="{0}" alt="{1}" title="{1}"/>'.format(reverse('rmgweb.main.views.drawMolecule', kwargs={'adjlist': adjlist}), '')
    elif isinstance(item, Species):
        # We can draw Species objects, so use that instead of an adjacency list
        adjlist = item.molecule[0].toAdjacencyList(removeH=True)
        adjlist = adjlist.replace('\n', ';')
        adjlist = re.sub('\s+', '%20', adjlist)
        structure = '<img src="{0}" alt="{1}" title="{1}"/>'.format(reverse('rmgweb.main.views.drawMolecule', kwargs={'adjlist': adjlist}), item.label)
    elif isinstance(item, Group):
        # We can draw Group objects, so use that instead of an adjacency list
        adjlist = item.toAdjacencyList()
        adjlist = adjlist.replace('\n', ';')
        adjlist = re.sub('\s+', '%20', adjlist)
        structure = '<img src="{0}" alt="{1}" title="{1}"/>'.format(reverse('rmgweb.main.views.drawGroup', kwargs={'adjlist': adjlist}), '')
    elif isinstance(item, str) or isinstance(item, unicode):
        structure = item
    else:
        structure = ''
    return structure

################################################################################

def prepareThermoParameters(thermo):
    """
    Collect the thermodynamic parameters for the provided thermodynamics model
    `thermo` and prepare them for viewing in a template. In particular, we must
    do any string formatting here because we can't do that in the template
    itself.
    """
    from rmgpy.thermo import ThermoData, Wilhoit, MultiNASA

    thermoParameters = {}
    
    if isinstance(thermo, ThermoData):
        # Thermo data is in group additivity format
        thermoParameters['format'] = 'Group additivity'
        thermoParameters['H298'] = ('%.2f' % (thermo.H298.value / 1000.),'kJ/mol')
        thermoParameters['S298'] = ('%.2f' % (thermo.S298.value),'J/mol \\cdot K')
        Cpdata = []
        for T, Cp in zip(thermo.Tdata.values, thermo.Cpdata.values):
            Cpdata.append(('%g' % (T),'K', '%.2f' % (Cp), 'J/mol \\cdot K'))
        thermoParameters['Cpdata'] = Cpdata
        
    elif isinstance(thermo, Wilhoit):
        # Thermo data is in Wilhoit polynomial format
        thermoParameters['format'] = 'Wilhoit'
        thermoParameters['cp0'] = ('%.2f' % (thermo.cp0.value),'J/mol \\cdot K')
        thermoParameters['cpInf'] = ('%.2f' % (thermo.cpInf.value),'J/mol \\cdot K')
        thermoParameters['a0'] = ('%s' % getLaTeXScientificNotation(thermo.a0.value),'')
        thermoParameters['a1'] = ('%s' % getLaTeXScientificNotation(thermo.a1.value),'')
        thermoParameters['a2'] = ('%s' % getLaTeXScientificNotation(thermo.a2.value),'')
        thermoParameters['a3'] = ('%s' % getLaTeXScientificNotation(thermo.a3.value),'')
        thermoParameters['B'] = ('%.2f' % (thermo.B.value),'K')
        thermoParameters['H0'] = ('%.2f' % (thermo.H0.value / 1000.),'kJ/mol')
        thermoParameters['S0'] = ('%.2f' % (thermo.S0.value),'J/mol \\cdot K')

    elif isinstance(thermo, MultiNASA):
        # Thermo data is in NASA polynomial format
        thermoParameters['format'] = 'NASA'
        thermoParameters['polynomials'] = []
        for poly in thermo.polynomials:
            thermoParameters['polynomials'].append({
                'cm2': '%s' % getLaTeXScientificNotation(poly.cm2),
                'cm1': '%s' % getLaTeXScientificNotation(poly.cm1),
                'c0': '%s' % getLaTeXScientificNotation(poly.c0),
                'c1': '%s' % getLaTeXScientificNotation(poly.c1),
                'c2': '%s' % getLaTeXScientificNotation(poly.c2),
                'c3': '%s' % getLaTeXScientificNotation(poly.c3),
                'c4': '%s' % getLaTeXScientificNotation(poly.c4),
                'c5': '%s' % getLaTeXScientificNotation(poly.c5),
                'c6': '%s' % getLaTeXScientificNotation(poly.c6),
                'Trange': ('%g' % (poly.Tmin.value), '%g' % (poly.Tmax.value), 'K'),
            })

    if thermo.Tmin is not None and thermo.Tmax is not None:
        thermoParameters['Trange'] = ('%g' % (thermo.Tmin.value), '%g' % (thermo.Tmax.value), 'K')
    else:
        thermoParameters['Trange'] = None

    return thermoParameters

################################################################################

def prepareKineticsParameters(kinetics, numReactants, degeneracy):
    """
    Collect the kinetics parameters for the provided kinetics model `kinetics`
    and prepare them for viewing in a template. In particular, we must do any
    string formatting here because we can't do that in the template itself.
    """
    from rmgpy.kinetics import *

    kineticsParameters = {}

    if numReactants == 1:
        kunits = 's^{-1}'
    elif numReactants == 2:
        kunits = 'm^3/mol \\cdot s'
    else:
        kunits = 'm^%g/mol^%s \\cdot s' % (3*(numReactants-1), numReactants-1)

    if isinstance(kinetics, KineticsData):
        # Kinetics data is in KineticsData format
        kineticsParameters['format'] = 'KineticsData'
        kineticsParameters['kdata'] = []
        for T, k in zip(kinetics.Tdata.values, kinetics.kdata.values):
            kineticsParameters['kdata'].append(('%g' % (T),'K', getLaTeXScientificNotation(k), kunits))

    elif isinstance(kinetics, Arrhenius):
        # Kinetics data is in Arrhenius format
        kineticsParameters['format'] = 'Arrhenius'
        kineticsParameters['A'] = (getLaTeXScientificNotation(kinetics.A.value), kunits)
        kineticsParameters['n'] = ('%.2f' % (kinetics.n.value), '')
        kineticsParameters['Ea'] = ('%.2f' % (kinetics.Ea.value / 1000.), 'kJ/mol')
        kineticsParameters['T0'] = ('%g' % (kinetics.T0.value), 'K')

    elif isinstance(kinetics, ArrheniusEP):
        # Kinetics data is in ArrheniusEP format
        kineticsParameters['format'] = 'ArrheniusEP'
        kineticsParameters['A'] = (getLaTeXScientificNotation(kinetics.A.value), kunits)
        kineticsParameters['n'] = ('%.2f' % (kinetics.n.value), '')
        kineticsParameters['E0'] = ('%.2f' % (kinetics.E0.value / 1000.), 'kJ/mol')
        kineticsParameters['alpha'] = ('%g' % (kinetics.alpha.value), '')

    elif isinstance(kinetics, MultiArrhenius):
        # Kinetics data is in MultiArrhenius format
        kineticsParameters['format'] = 'MultiArrhenius'
        kineticsParameters['arrheniusList'] = []
        for arrh in kinetics.arrheniusList:
            kineticsParameters['arrheniusList'].append({
                'A': (getLaTeXScientificNotation(arrh.A.value), kunits),
                'n': ('%.2f' % (arrh.n.value), ''),
                'Ea': ('%.2f' % (arrh.Ea.value / 1000.), 'kJ/mol'),
                'T0': ('%g' % (arrh.T0.value), 'K'),
            })
            
    elif isinstance(kinetics, PDepArrhenius):
        # Kinetics data is in PDepArrhenius format
        kineticsParameters['format'] = 'PDepArrhenius'
        for P, arrh in zip(kinetics.pressures, kinetics.arrhenius):
            kineticsParameters['arrhenius'].append({
                'A': (getLaTeXScientificNotation(arrh.A.value), kunits),
                'n': ('%.2f' % (arrh.n.value), ''),
                'Ea': ('%.2f' % (arrh.Ea.value / 1000.), 'kJ/mol'),
                'T0': ('%g' % (arrh.T0.value), 'K'),
                'P': ('%g' % (P.value / 1e5), 'bar'),
            })

    elif isinstance(kinetics, Chebyshev):
        # Kinetics data is in Chebyshev format
        kineticsParameters['format'] = 'Chebyshev'
        coeffs = []
        for i in range(kinetics.degreeT):
            coeffs.append(['%g' % kinetics.coeffs[i,j] for j in range(kinetics.degreeP)])
        kineticsParameters['coeffs'] = (coeffs, kunits)
        
    elif isinstance(kinetics, Troe):
        # Kinetics data is in Troe format
        kineticsParameters['format'] = 'Troe'
        kineticsParameters['arrheniusHigh'] = {
            'A': (getLaTeXScientificNotation(kinetics.arrheniusHigh.A.value), kunits),
            'n': ('%.2f' % (kinetics.arrheniusHigh.n.value), ''),
            'Ea': ('%.2f' % (kinetics.arrheniusHigh.Ea.value / 1000.), 'kJ/mol'),
            'T0': ('%g' % (kinetics.arrheniusHigh.T0.value), 'K'),
        }
        kineticsParameters['arrheniusLow'] = {
            'A': (getLaTeXScientificNotation(kinetics.arrheniusLow.A.value), kunits),
            'n': ('%.2f' % (kinetics.arrheniusLow.n.value), ''),
            'Ea': ('%.2f' % (kinetics.arrheniusLow.Ea.value / 1000.), 'kJ/mol'),
            'T0': ('%g' % (kinetics.arrheniusLow.T0.value), 'K'),
        }
        kineticsParameters['alpha'] = ('%g' % (kinetics.alpha.value),'')
        kineticsParameters['T3'] = ('%g' % (kinetics.T3.value),'K')
        kineticsParameters['T1'] = ('%g' % (kinetics.T1.value),'K')
        if kinetics.T2 is not None:
            kineticsParameters['T2'] = ('%g' % (kinetics.T2.value),'K')
        else:
            kineticsParameters['T2'] = 'None'
        
    elif isinstance(kinetics, Lindemann):
        # Kinetics data is in Lindemann format
        kineticsParameters['format'] = 'Lindemann'
        kineticsParameters['arrheniusHigh'] = {
            'A': (getLaTeXScientificNotation(kinetics.arrheniusHigh.A.value), kunits),
            'n': ('%.2f' % (kinetics.arrheniusHigh.n.value), ''),
            'Ea': ('%.2f' % (kinetics.arrheniusHigh.Ea.value / 1000.), 'kJ/mol'),
            'T0': ('%g' % (kinetics.arrheniusHigh.T0.value), 'K'),
        }
        kineticsParameters['arrheniusLow'] = {
            'A': (getLaTeXScientificNotation(kinetics.arrheniusLow.A.value), kunits),
            'n': ('%.2f' % (kinetics.arrheniusLow.n.value), ''),
            'Ea': ('%.2f' % (kinetics.arrheniusLow.Ea.value / 1000.), 'kJ/mol'),
            'T0': ('%g' % (kinetics.arrheniusLow.T0.value), 'K'),
        }

    elif isinstance(kinetics, ThirdBody):
        # Kinetics data is in ThirdBody format
        kineticsParameters['format'] = 'ThirdBody'
        kineticsParameters['arrheniusHigh'] = {
            'A': (getLaTeXScientificNotation(kinetics.arrheniusHigh.A.value), kunits),
            'n': ('%.2f' % (kinetics.arrheniusHigh.n.value), ''),
            'Ea': ('%.2f' % (kinetics.arrheniusHigh.Ea.value / 1000.), 'kJ/mol'),
            'T0': ('%g' % (kinetics.arrheniusHigh.T0.value), 'K'),
        }

    # Also include collision efficiencies for the relevant kinetics models
    efficiencies = []
    if isinstance(kinetics, ThirdBody):
        molecules = [(molecule.getFormula(), molecule) for molecule in kinetics.efficiencies]
        molecules.sort()
        for formula, molecule in molecules:
            efficiencies.append((getStructureMarkup(molecule), '%g' % kinetics.efficiencies[molecule]))
        kineticsParameters['efficiencies'] = efficiencies

    # Also include the reaction path degeneracy
    kineticsParameters['degeneracy'] = '%i' % (degeneracy)

    # Set temperature and pressure ranges
    if kinetics is not None and kinetics.Tmin is not None and kinetics.Tmax is not None:
        kineticsParameters['Trange'] = ('%g' % (kinetics.Tmin.value), '%g' % (kinetics.Tmax.value), 'K')
    else:
        kineticsParameters['Trange'] = None
    if kinetics is not None and kinetics.Pmin is not None and kinetics.Pmax is not None:
        kineticsParameters['Prange'] = ('%g' % (kinetics.Pmin.value / 1e5), '%g' % (kinetics.Pmax.value / 1e5), 'bar')
    else:
        kineticsParameters['Prange'] = None

    return kineticsParameters

################################################################################

def prepareStatesParameters(states):
    """
    Collect the molecular degrees of freedom parameters for the provided states
    model `states` and prepare them for viewing in a template. In particular, 
    we must do any string formatting here because we can't do that in the 
    template itself.
    """
    from rmgpy.statmech import Translation, RigidRotor, HarmonicOscillator, HinderedRotor
    from rmgpy.quantity import constants
    
    statesParameters = {
        'translation': None,
        'rotation': None,
        'vibration': None,
        'torsion': None,
    }

    for mode in states.modes:
        modeParameters = {}
        
        if isinstance(mode, Translation):
            modeParameters['mass'] = '{0:g}'.format(mode.mass * 1000)
            statesParameters['rotation'] = modeParameters
        
        elif isinstance(mode, RigidRotor):
            if mode.linear:
                modeParameters['linearity'] = 'Linear'
                modeParameters['inertia'] = ['{0:.1f}'.format(mode.inertia.value * constants.Na * 1e23)]
            else:
                modeParameters['linearity'] = 'Nonlinear'
                modeParameters['inertia'] = ['{0:.1f}'.format(inertia * constants.Na * 1e23) for inertia in mode.inertia.values]
                modeParameters['symmetry'] = '{0:d}'.format(mode.symmetry)
            statesParameters['rotation'] = modeParameters
        
        elif isinstance(mode, HarmonicOscillator):
            modeParameters['frequencies'] = ['{0:.1f}'.format(freq) for freq in mode.frequencies.values]
            statesParameters['vibration'] = modeParameters
        
        elif isinstance(mode, HinderedRotor):
            if statesParameters['torsion'] is None:
                statesParameters['torsion'] = []
            modeParameters['inertia'] = '{0:.1f}'.format(mode.inertia.value * constants.Na * 1e23)
            modeParameters['symmetry'] = '{0:d}'.format(mode.symmetry)
            if mode.fourier is not None:
                modeParameters['barrier'] = None
                modeParameters['fourierA'] = ['{0:g}'.format(a_k) for a_k in mode.fourier.values[0,:]]  
                modeParameters['fourierB'] = ['{0:g}'.format(b_k) for b_k in mode.fourier.values[1,:]]  
            elif mode.barrier is not None:
                modeParameters['barrier'] = '{0:.1f}'.format(mode.barrier.value / 1000.)
                modeParameters['fourierA'] = None
                modeParameters['fourierB'] = None
            statesParameters['torsion'].append(modeParameters)
            
    statesParameters['spinMultiplicity'] = '{0:d}'.format(states.spinMultiplicity)
    
    return statesParameters
