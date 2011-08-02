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
import numpy
import re

from django.core.urlresolvers import reverse

from rmgpy.quantity import constants
from rmgpy.molecule import Molecule

################################################################################

def moleculeToURL(molecule):
    """
    Convert a given :class:`Molecule` object `molecule` to a string 
    representation of its structure suitable for a URL.
    """
    molecule.clearLabeledAtoms()
    adjlist = molecule.toAdjacencyList(removeH=True)
    adjlist = re.sub('\s+', '%20', adjlist.replace('\n', ';'))
    return adjlist

def moleculeFromURL(adjlist):
    """
    Convert a given adjacency list `adjlist` from a URL to the corresponding
    :class:`Molecule` object.
    """
    molecule = Molecule().fromAdjacencyList(str(adjlist.replace(';', '\n')))
    return molecule

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
    elif isinstance(item, Species) and len(item.molecule) > 0:
        # We can draw Species objects, so use that instead of an adjacency list
        adjlist = item.molecule[0].toAdjacencyList(removeH=True)
        adjlist = adjlist.replace('\n', ';')
        adjlist = re.sub('\s+', '%20', adjlist)
        structure = '<img src="{0}" alt="{1}" title="{1}"/>'.format(reverse('rmgweb.main.views.drawMolecule', kwargs={'adjlist': adjlist}), item.label)
    elif isinstance(item, Species) and len(item.molecule) == 0:
        # We can draw Species objects, so use that instead of an adjacency list
        structure = item.label
    elif isinstance(item, Group):
        # We can draw Group objects, so use that instead of an adjacency list
        adjlist = item.toAdjacencyList()
        adjlist_url = adjlist.replace('\n', ';')
        adjlist_url = re.sub('\s+', '%20', adjlist_url)
        structure = '<img src="{0}" alt="{1}" title="{1}" />'.format(reverse('rmgweb.main.views.drawGroup', kwargs={'adjlist': adjlist_url}), adjlist)
        #structure += '<pre style="font-size:small;" class="adjacancy_list">{0}</pre>'.format(adjlist)
    elif isinstance(item, str) or isinstance(item, unicode):
        structure = item
    else:
        structure = ''
    return structure

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
    
    # Generate data to use for plots
    Tdata = []; Qdata = []
    for T in numpy.arange(10, 2001, 10):
        Tdata.append(T)
        Qdata.append(states.getPartitionFunction(T))
    
    Edata = numpy.arange(0, 400001, 1000, numpy.float)
    rhodata = states.getDensityOfStates(Edata)
    Edata = list(Edata)
    rhodata = list(rhodata)
    
    phidata = numpy.arange(0, 2*math.pi, math.pi/200)
    Vdata = []
    for mode in states.modes:
        if isinstance(mode, HinderedRotor):
            Vdata.append(list(mode.getPotential(phidata)))
    phidata = list(phidata)
    
    statesParameters['data'] = {
        'Tdata': Tdata,
        'Qdata': Qdata,
        'Edata': Edata,
        'rhodata': rhodata,
        'phidata': phidata,
        'Vdata': Vdata,
    }
    
    return statesParameters

################################################################################

def prepareCollisionParameters(species):
    """
    Collect the collision parameters for the provided `species` and prepare 
    them for viewing in a template. In particular, we must do any string 
    formatting here because we can't do that in the template itself.
    """
    
    collisionParameters = {}
    
    collisionParameters['molWt'] = '{0:.2f}'.format(species.molecularWeight.value * 1000)
    collisionParameters['sigmaLJ'] = '{0:.2f}'.format(species.lennardJones.sigma.value * 1e10)
    collisionParameters['epsilonLJ'] = '{0:g}'.format(species.lennardJones.epsilon.value / constants.kB)
    
    return collisionParameters
