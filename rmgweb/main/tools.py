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

import urllib

import math
from django.urls import reverse
from rmgpy.molecule.group import Group
from rmgpy.molecule.molecule import Molecule
from rmgpy.species import Species

################################################################################


def moleculeToAdjlist(molecule):
    """
    Convert a given :class:`Molecule` object `molecule` to a string
    representation of its structure suitable for a URL.
    """
    mol = molecule.copy(deep=True)
    mol.clear_labeled_atoms()
    adjlist = mol.to_adjacency_list(remove_h=False)
    return adjlist


def moleculeToInfo(molecule):
    """
    Creates an html rendering which includes molecule structure image but
    also allows you to click on it to enter a molecule info page.
    """
    href = reverse('database:molecule-entry', kwargs={'adjlist': molecule.to_adjacency_list()})
    structure_markup = getStructureMarkup(molecule)
    markup = '<a href="' + href + '">' + structure_markup + '</a>'
    return markup


def moleculeFromURL(adjlist):
    """
    Convert a given adjacency list `adjlist` from a URL to the corresponding
    :class:`Molecule` object.
    """
    adjlist = urllib.parse.unquote(adjlist)
    molecule = Molecule().from_adjacency_list(adjlist)
    return molecule

################################################################################


def groupToURL(group):
    """
    Convert a given :class:`Group` object `group` to a string
    representation of its structure suitable for a URL.
    """
    gro = group.copy(deep=True)
    gro.clear_labeled_atoms()
    adjlist = gro.to_adjacency_list(remove_h=False)
    return adjlist


def groupToInfo(group):
    """
    Creates an html rendering which includes group structure image but
    also allows you to click on it to enter a group info page.
    """
    href = reverse('database:group-entry', kwargs={'adjlist': group.to_adjacency_list()})
    structure_markup = getStructureMarkup(group)
    markup = '<a href="' + href + '">' + structure_markup + '</a>'
    return markup


def groupFromURL(adjlist):
    """
    Convert a given adjacency list `adjlist` from a URL to the corresponding
    :class:`Group` object.
    """
    adjlist = urllib.parse.unquote(adjlist)
    group = Group().from_adjacency_list(adjlist)
    return group

################################################################################


def getStructureInfo(object):
    """
    Convert either a Entry, Molecule, Species, or Group object to its html
    markup containing a clickable image of the group or molecule that contains
    a link to its information page.
    """
    from rmgpy.data.base import Entry, LogicNode, LogicOr, LogicAnd
    from rmgpy.species import Species

    if isinstance(object, Entry):
        object = object.item

    if isinstance(object, Molecule):
        return moleculeToInfo(object)
    elif isinstance(object, Species):
        return moleculeToInfo(object.molecule[0])
    elif isinstance(object, Group):
        return groupToInfo(object)
    elif isinstance(object, (LogicNode, LogicOr, LogicAnd)):
        return str(object)
    else:
        return ''
################################################################################


def getLaTeXScientificNotation(value):
    """
    Return a LaTeX-formatted string containing the provided `value` in
    scientific notation.
    """
    if value == 0:
        return '0'
    negative = value < 0
    value = abs(value)
    exp = int(math.log10(abs(value)))
    mant = value / 10**exp
    if abs(mant) < 1:
        mant *= 10
        exp -= 1
    return '{0}{1:g} \\times 10^{{{2:d}}}'.format('-' if negative else '', mant, exp)

################################################################################


def getStructureMarkup(item):
    """
    Return the HTML used to markup structure information for the given `item`.
    For a :class:`Molecule`, the markup is an ``<img>`` tag so that we can
    draw the molecule. For a :class:`Group`, the markup is the
    adjacency list, wrapped in ``<pre>`` tags.
    """
    if isinstance(item, Molecule):
        # We can draw Molecule objects, so use that instead of an adjacency list
        adjlist = item.to_adjacency_list(remove_h=False)
        url = urllib.parse.quote(adjlist)
        structure = '<img src="{0}" alt="{1}" title="{1}"/>'.format(reverse('draw-molecule', kwargs={'adjlist': url}), adjlist)
    elif isinstance(item, Species) and len(item.molecule) > 0:
        # We can draw Species objects, so use that instead of an adjacency list
        adjlist = item.molecule[0].to_adjacency_list(remove_h=False)
        url = urllib.parse.quote(adjlist)
        structure = '<img src="{0}" alt="{1}" title="{1}"/>'.format(reverse('draw-molecule', kwargs={'adjlist': url}), item.label)
    elif isinstance(item, Species) and len(item.molecule) == 0:
        # We can draw Species objects, so use that instead of an adjacency list
        structure = item.label
    elif isinstance(item, Group):
        # We can draw Group objects, so use that instead of an adjacency list
        adjlist = item.to_adjacency_list()
        url = urllib.parse.quote(adjlist)
        structure = '<img src="{0}" alt="{1}" title="{1}" />'.format(reverse('draw-group', kwargs={'adjlist': url}), adjlist)
        # structure += '<pre style="font-size:small;" class="adjacancy_list">{0}</pre>'.format(adjlist)
    elif isinstance(item, str) or isinstance(item, str):
        structure = item
    else:
        structure = ''
    return structure
