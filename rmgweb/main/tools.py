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

import rmgpy.constants as constants
from rmgpy.molecule.molecule import Molecule

################################################################################

def moleculeToURL(molecule):
    """
    Convert a given :class:`Molecule` object `molecule` to a string 
    representation of its structure suitable for a URL.
    """
    mol = molecule.copy(deep=True)
    mol.clearLabeledAtoms()
    adjlist = mol.toAdjacencyList(removeH=False)
    adjlist = re.sub('\s+', '%20', adjlist.replace('\n', ';'))
    return adjlist

def moleculeToInfo(molecule):
    """
    Creates an html rendering which includes molecule structure image but
    also allows you to click on it to enter a molecule info page.
    """

    from rmgweb.database.views import moleculeEntry
    href = reverse(moleculeEntry, kwargs={'adjlist': molecule.toAdjacencyList()})
    structureMarkup = getStructureMarkup(molecule)
    markup = '<a href="'+ href + '">' + structureMarkup + '</a>'
    return markup

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
    if value == 0: return '0'
    negative = value < 0
    value = abs(value)
    exp = int(math.log10(abs(value)))
    mant = value / 10**exp
    if abs(mant) < 1:
        mant *= 10; exp -= 1
    return '{0}{1:g} \\times 10^{{{2:d}}}'.format('-' if negative else '', mant, exp)

################################################################################

def getStructureMarkup(item):
    """
    Return the HTML used to markup structure information for the given `item`.
    For a :class:`Molecule`, the markup is an ``<img>`` tag so that we can
    draw the molecule. For a :class:`Group`, the markup is the
    adjacency list, wrapped in ``<pre>`` tags.
    """
    from rmgpy.molecule.molecule import Molecule
    from rmgpy.molecule.group import Group
    from rmgpy.species import Species
    
    if isinstance(item, Molecule):
        # We can draw Molecule objects, so use that instead of an adjacency list
        adjlist = item.toAdjacencyList(removeH=False)
        adjlist2 = adjlist.replace('\n', ';')
        adjlist2 = re.sub('\s+', '%20', adjlist2)
        structure = '<img src="{0}" alt="{1}" title="{1}"/>'.format(reverse('rmgweb.main.views.drawMolecule', kwargs={'adjlist': adjlist2}), adjlist)
    elif isinstance(item, Species) and len(item.molecule) > 0:
        # We can draw Species objects, so use that instead of an adjacency list
        adjlist = item.molecule[0].toAdjacencyList(removeH=False)
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
