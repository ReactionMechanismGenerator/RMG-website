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

import os.path
import re

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
import settings

from rmgpy.chem.molecule import Molecule
from rmgpy.chem.pattern import MoleculePattern
from rmgpy.chem.thermo import *
from rmgpy.chem.kinetics import *

from rmgpy.data.base import Entry
from rmgpy.data.thermo import ThermoDatabase, convertThermoData
from rmgpy.data.kinetics import KineticsDatabase

from forms import *

################################################################################

thermoDatabase = None

def loadThermoDatabase():
    """
    Load the thermodynamics database, if necessary. If the thermodynamics
    database is already loaded, then do nothing.
    """
    global thermoDatabase
    if not thermoDatabase:
        thermoDatabase = ThermoDatabase()
        thermoDatabase.load(path=os.path.join(settings.DATABASE_PATH, 'thermo'))

kineticsDatabase = None

def loadKineticsDatabase():
    """
    Load the kinetics database, if necessary. If the kinetics
    database is already loaded, then do nothing.
    """
    global kineticsDatabase
    if not kineticsDatabase:
        kineticsDatabase = KineticsDatabase()
        kineticsDatabase.load(path=os.path.join(settings.DATABASE_PATH, 'kinetics'))

def getThermoDatabase(section, subsection):
    """
    Return the component of the thermodynamics database corresponding to the
    given `section` and `subsection`. If either of these is invalid, a
    :class:`ValueError` is raised.
    """
    global thermoDatabase

    if section == 'depository':
        try:
            database = thermoDatabase.depository[subsection]
        except KeyError:
            raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)
    elif section == 'libraries':
        libraries = [library for library in thermoDatabase.libraries if library.label == subsection]
        if len(libraries) != 1: raise Http404
        database = libraries[0]
    elif section == 'groups':
        try:
            database = thermoDatabase.groups[subsection]
        except KeyError:
            raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)
    else:
        raise ValueError('Invalid value "%s" for section parameter.' % section)
    return database

def getKineticsDatabase(section, subsection):
    """
    Return the component of the kinetics database corresponding to the
    given `section` and `subsection`. If either of these is invalid, a
    :class:`ValueError` is raised.
    """
    global kineticsDatabase
    
    if section == 'depository':
        try:
            database = kineticsDatabase.depository[subsection]
        except KeyError:
            raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)
    elif section == 'libraries':
        libraries = [library for library in kineticsDatabase.libraries if library.label == subsection]
        if len(libraries) != 1: raise Http404
        database = libraries[0]
    elif section == 'groups':
        try:
            database = kineticsDatabase.groups[subsection]
        except KeyError:
            raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)
    else:
        raise ValueError('Invalid value "%s" for section parameter.' % section)
    return database

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

def getStructureMarkup(item):
    """
    Return the HTML used to markup structure information for the given `item`.
    For a :class:`Molecule`, the markup is an ``<img>`` tag so that we can
    draw the molecule. For a :class:`MoleculePattern`, the markup is the
    adjacency list, wrapped in ``<pre>`` tags.
    """
    if isinstance(item, Molecule):
        # We can draw Molecule objects, so use that instead of an adjacency list
        adjlist = item.toAdjacencyList(removeH=True)
        adjlist = adjlist.replace('\n', ';')
        adjlist = re.sub('\s+', '%20', adjlist)
        structure = '<img src="/molecule/%s"/>' % adjlist
    elif isinstance(item, MoleculePattern):
        # We can draw MoleculePattern objects, so use that instead of an adjacency list
        adjlist = item.toAdjacencyList()
        adjlist = adjlist.replace('\n', ';')
        adjlist = re.sub('\s+', '%20', adjlist)
        structure = '<img src="/pattern/%s"/>' % adjlist
    else:
        structure = ''
    return structure

################################################################################

def index(request):
    """
    The RMG database homepage.
    """
    return render_to_response('database.html', context_instance=RequestContext(request))

def thermo(request, section='', subsection=''):
    """
    The RMG database homepage.
    """
    # Make sure section has an allowed value
    if section not in ['depository', 'libraries', 'groups', '']:
        raise Http404

    # Load the thermo database if necessary
    loadThermoDatabase()

    if subsection != '':

        # A subsection was specified, so render a table of the entries in
        # that part of the database
        
        # Determine which subsection we wish to view
        try:
            database = getThermoDatabase(section, subsection)
        except ValueError:
            raise Http404

        # Sort entries by index
        entries0 = database.entries.values()
        entries0.sort(key=lambda entry: entry.index)

        entries = []
        for entry in entries0:

            structure = getStructureMarkup(entry.item)

            if isinstance(entry.data, ThermoGAModel): dataFormat = 'Group additivity'
            elif isinstance(entry.data, WilhoitModel): dataFormat = 'Wilhoit'
            elif isinstance(entry.data, NASAModel): dataFormat = 'NASA'
            elif isinstance(entry.data, str): dataFormat = 'Link'

            entries.append((entry.index,entry.label,structure,dataFormat))

        return render_to_response('thermoTable.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entries': entries}, context_instance=RequestContext(request))

    else:
        # No subsection was specified, so render an outline of the thermo
        # database components
        return render_to_response('thermo.html', {'section': section, 'subsection': subsection, 'thermoDatabase': thermoDatabase}, context_instance=RequestContext(request))

def prepareThermoParameters(thermo):
    """
    Collect the thermodynamic parameters for the provided thermodynamics model
    `thermo` and prepare them for viewing in a template. In particular, we must
    do any string formatting here because we can't do that in the template
    itself.
    """

    thermoData = []
    
    if isinstance(thermo, ThermoGAModel):
        # Thermo data is in group additivity format
        thermoData = ['Group additivity']
        thermoData.extend(['%.2f' % (thermo.H298 / 1000.), '%.2f' % (thermo.S298)])
        thermoData.append('%g' % (thermo.Tmin))
        thermoData.append('%g' % (thermo.Tmax))
        for T, Cp in zip(thermo.Tdata, thermo.Cpdata):
            thermoData.append(('%g' % T, '%.2f' % Cp))

    elif isinstance(thermo, WilhoitModel):
        # Thermo data is in Wilhoit polynomial format
        thermoData = [
            'Wilhoit',
            '%.2f' % (thermo.cp0),
            '%.2f' % (thermo.cpInf),
            '%s' % getLaTeXScientificNotation(thermo.a0),
            '%s' % getLaTeXScientificNotation(thermo.a1),
            '%s' % getLaTeXScientificNotation(thermo.a2),
            '%s' % getLaTeXScientificNotation(thermo.a3),
            '%.2f' % (thermo.H0 / 1000.),
            '%.2f' % (thermo.S0),
            '%.2f' % (thermo.B),
            '%g' % (thermo.Tmin),
            '%g' % (thermo.Tmax),
        ]

    elif isinstance(thermo, NASAModel):
        # Thermo data is in NASA polynomial format
        thermoData = ['NASA']
        for poly in thermo.polynomials:
            thermoData.append([
                '%s' % getLaTeXScientificNotation(poly.cm2),
                '%s' % getLaTeXScientificNotation(poly.cm1),
                '%s' % getLaTeXScientificNotation(poly.c0),
                '%s' % getLaTeXScientificNotation(poly.c1),
                '%s' % getLaTeXScientificNotation(poly.c2),
                '%s' % getLaTeXScientificNotation(poly.c3),
                '%s' % getLaTeXScientificNotation(poly.c4),
                '%s' % getLaTeXScientificNotation(poly.c5),
                '%s' % getLaTeXScientificNotation(poly.c6),
                '%g' % (poly.Tmin),
                '%g' % (poly.Tmax),
            ])

    return thermoData

def thermoEntry(request, section, subsection, index):
    """
    A view for showing an entry in a thermodynamics database.
    """

    # Load the thermo database if necessary
    loadThermoDatabase()

    # Determine the entry we wish to view
    try:
        database = getThermoDatabase(section, subsection)
    except ValueError:
        raise Http404
    index = int(index)
    try:
        entry = database.entries[index]
    except KeyError:
        raise Http404

    # Get the structure of the item we are viewing
    structure = getStructureMarkup(entry.item)

    # Prepare the thermo data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, str):
        thermoData = ['Link', database.entries[entry.data].index]
    else:
        thermoData = prepareThermoParameters(entry.data)

    reference = entry.reference
    if reference[1:3] == '. ':
        reference = reference[0:2] + '\ ' + reference[2:]

    return render_to_response('thermoEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'structure': structure, 'reference': reference, 'thermoData': thermoData}, context_instance=RequestContext(request))

def thermoSearch(request):
    """
    A view of a form for specifying a molecule to search the database for
    thermodynamics properties.
    """

    # Load the thermo database if necessary
    loadThermoDatabase()

    if request.method == 'POST':
        form = ThermoSearchForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            adjlist = form.cleaned_data['species']
            adjlist = adjlist.replace('\n', ';')
            adjlist = re.sub('\s+', '%20', adjlist)
            return HttpResponseRedirect(reverse(thermoData, kwargs={'adjlist': adjlist}))
    else:
        form = ThermoSearchForm()
    
    return render_to_response('thermoSearch.html', {'form': form}, context_instance=RequestContext(request))

def thermoData(request, adjlist):
    """
    Returns an image of the provided adjacency list `adjlist` for a molecule.
    Note that the newline character cannot be represented in a URL;
    semicolons should be used instead.
    """
    from rmgpy.chem.molecule import Molecule
    
    # Load the thermo database if necessary
    loadThermoDatabase()

    adjlist = str(adjlist.replace(';', '\n'))
    molecule = Molecule().fromAdjacencyList(adjlist)

    # Get the thermo data for the molecule
    thermoDataList = []
    for data, library, entry in thermoDatabase.getAllThermoData(molecule):
        if library is None:
            source = 'Group additivity'
            href = ''
            data = convertThermoData(data, molecule, WilhoitModel)
            data = convertThermoData(data, molecule, NASAModel)
            entry = Entry(data=data)
        elif library in thermoDatabase.depository.values():
            source = 'Depository'
            href = reverse(thermoEntry, kwargs={'section': 'depository', 'subsection': library.label, 'index': entry.index})
        elif library in thermoDatabase.libraries:
            source = library.name
            href = reverse(thermoEntry, kwargs={'section': 'libraries', 'subsection': library.label, 'index': entry.index})
        thermoDataList.append((
            entry,
            prepareThermoParameters(data),
            source,
            href,
        ))
        print entry.data
    
    # Get the structure of the item we are viewing
    structure = getStructureMarkup(molecule)

    return render_to_response('thermoData.html', {'structure': structure, 'thermoDataList': thermoDataList}, context_instance=RequestContext(request))

################################################################################

def kinetics(request, section='', subsection=''):
    """
    The RMG database homepage.
    """
    # Make sure section has an allowed value
    if section not in ['depository', 'libraries', 'groups', '']:
        raise Http404

    # Load the kinetics database, if necessary
    loadKineticsDatabase()

    if subsection != '':

        # A subsection was specified, so render a table of the entries in
        # that part of the database

        # Determine which subsection we wish to view
        try:
            database = getKineticsDatabase(section, subsection)
        except ValueError:
            raise Http404

        # Sort entries by index
        entries0 = database.entries.values()
        entries0.sort(key=lambda entry: entry.index)

        entries = []
        for entry in entries0:

            reactants = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.reactants])
            products = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.products])
            arrow = '&hArr;' if entry.item.reversible else '&rarr;'

            dataFormat = ''
            if isinstance(entry.data, KineticsDataModel): dataFormat = 'KineticsData'
            elif isinstance(entry.data, ArrheniusModel): dataFormat = 'Arrhenius'
            elif isinstance(entry.data, str): dataFormat = 'Link'
            elif isinstance(entry.data, ArrheniusEPModel): dataFormat = 'ArrheniusEP'
            elif isinstance(entry.data, MultiArrheniusModel): dataFormat = 'MultiArrhenius'
            elif isinstance(entry.data, PDepArrheniusModel): dataFormat = 'PDepArrhenius'
            elif isinstance(entry.data, ChebyshevModel): dataFormat = 'Chebyshev'
            elif isinstance(entry.data, TroeModel): dataFormat = 'Troe'
            elif isinstance(entry.data, LindemannModel): dataFormat = 'Lindemann'
            elif isinstance(entry.data, ThirdBodyModel): dataFormat = 'ThirdBody'
            
            entries.append((entry.index,entry.label,reactants,arrow,products,dataFormat))

        return render_to_response('kineticsTable.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entries': entries}, context_instance=RequestContext(request))

    else:
        # No subsection was specified, so render an outline of the kinetics
        # database components
        return render_to_response('kinetics.html', {'section': section, 'subsection': subsection, 'kineticsDatabase': kineticsDatabase}, context_instance=RequestContext(request))

def prepareKineticsParameters(kinetics):
    """
    Collect the thermodynamic parameters for the provided thermodynamics model
    `thermo` and prepare them for viewing in a template. In particular, we must
    do any string formatting here because we can't do that in the template
    itself.
    """

    kineticsData = []

    if isinstance(kinetics, KineticsDataModel):
        # Kinetics data is in KineticsData format
        kineticsData = ['KineticsData']
        kineticsData.append('%g' % (kinetics.Tmin))
        kineticsData.append('%g' % (kinetics.Tmax))
        data = []
        for T, k in zip(kinetics.Tdata, kinetics.kdata):
            data.append(('%g' % T, getLaTeXScientificNotation(k)))
        kineticsData.append(data)

    elif isinstance(kinetics, ArrheniusModel):
        # Kinetics data is in Arrhenius format
        kineticsData = ['Arrhenius']
        kineticsData.extend([getLaTeXScientificNotation(kinetics.A), '%.2f' % (kinetics.n), '%.2f' % (kinetics.Ea / 1000.), '%g' % (kinetics.T0)])
        kineticsData.append('%g' % (kinetics.Tmin))
        kineticsData.append('%g' % (kinetics.Tmax))

    elif isinstance(kinetics, ArrheniusEPModel):
        # Kinetics data is in ArrheniusEP format
        kineticsData = ['Arrhenius']
        kineticsData.extend([getLaTeXScientificNotation(kinetics.A), '%.2f' % (kinetics.n), '%g' % (kinetics.alpha), '%.2f' % (kinetics.E0 / 1000.)])
        kineticsData.append('%g' % (kinetics.Tmin))
        kineticsData.append('%g' % (kinetics.Tmax))

    elif isinstance(kinetics, MultiArrheniusModel):
        # Kinetics data is in MultiArrhenius format
        kineticsData = ['MultiArrhenius']
        arrheniusList = []
        for arrh in kinetics.arrheniusList:
            arrheniusList.append([getLaTeXScientificNotation(arrh.A), '%.2f' % (arrh.n), '%.2f' % (arrh.Ea / 1000.), '%g' % (arrh.T0)])
        kineticsData.append(arrheniusList)
        kineticsData.append('%g' % (kinetics.Tmin))
        kineticsData.append('%g' % (kinetics.Tmax))

    elif isinstance(kinetics, PDepArrheniusModel):
        # Kinetics data is in PDepArrhenius format
        kineticsData = ['PDepArrhenius']
        pdeparrhenius = []
        for P, arrh in zip(kinetics.pressures, kinetics.arrhenius):
            pdeparrhenius.append([getLaTeXScientificNotation(arrh.A), '%.2f' % (arrh.n), '%g' % (arrh.alpha), '%.2f' % (arrh.E0 / 1000.), '%g' % (P / 1.0e5)])
        kineticsData.append(pdeparrhenius)
        kineticsData.append('%g' % (kinetics.Tmin))
        kineticsData.append('%g' % (kinetics.Tmax))
        kineticsData.append('%g' % (kinetics.Pmin / 1.0e5))
        kineticsData.append('%g' % (kinetics.Pmax / 1.0e5))
        
    elif isinstance(kinetics, ChebyshevModel):
        # Kinetics data is in Chebyshev format
        kineticsData = ['Chebyshev']
        chebyshev = []
        for i in range(kinetics.degreeT):
            chebyshev.append(['%g' % kinetics.coeffs[i,j] for j in range(kinetics.degreeP)])
        kineticsData.append(chebyshev)
        kineticsData.append('%g' % (kinetics.Tmin))
        kineticsData.append('%g' % (kinetics.Tmax))
        kineticsData.append('%g' % (kinetics.Pmin / 1.0e5))
        kineticsData.append('%g' % (kinetics.Pmax / 1.0e5))

    elif isinstance(kinetics, TroeModel):
        # Kinetics data is in Troe format
        kineticsData = ['Troe']
        kineticsData.append([getLaTeXScientificNotation(kinetics.arrheniusHigh.A), '%.2f' % (kinetics.arrheniusHigh.n), '%.2f' % (kinetics.arrheniusHigh.Ea / 1000.), '%g' % (kinetics.arrheniusHigh.T0)])
        kineticsData.append([getLaTeXScientificNotation(kinetics.arrheniusLow.A), '%.2f' % (kinetics.arrheniusLow.n), '%.2f' % (kinetics.arrheniusLow.Ea / 1000.), '%g' % (kinetics.arrheniusLow.T0)])
        kineticsData.extend(['%g' % kinetics.alpha, '%g' % (kinetics.T3), '%g' % (kinetics.T1), '%g' % (kinetics.T2)])
        kineticsData.append('%g' % (kinetics.Tmin))
        kineticsData.append('%g' % (kinetics.Tmax))
        kineticsData.append('%g' % (kinetics.Pmin / 1.0e5))
        kineticsData.append('%g' % (kinetics.Pmax / 1.0e5))

    elif isinstance(kinetics, LindemannModel):
        # Kinetics data is in Lindemann format
        kineticsData = ['Lindemann']
        kineticsData.append([getLaTeXScientificNotation(kinetics.arrheniusHigh.A), '%.2f' % (kinetics.arrheniusHigh.n), '%.2f' % (kinetics.arrheniusHigh.Ea / 1000.), '%g' % (kinetics.arrheniusHigh.T0)])
        kineticsData.append([getLaTeXScientificNotation(kinetics.arrheniusLow.A), '%.2f' % (kinetics.arrheniusLow.n), '%.2f' % (kinetics.arrheniusLow.Ea / 1000.), '%g' % (kinetics.arrheniusLow.T0)])
        kineticsData.append('%g' % (kinetics.Tmin))
        kineticsData.append('%g' % (kinetics.Tmax))
        kineticsData.append('%g' % (kinetics.Pmin / 1.0e5))
        kineticsData.append('%g' % (kinetics.Pmax / 1.0e5))
        
    elif isinstance(kinetics, ThirdBodyModel):
        # Kinetics data is in ThirdBody format
        kineticsData = ['ThirdBody']
        kineticsData.append([getLaTeXScientificNotation(kinetics.arrheniusHigh.A), '%.2f' % (kinetics.arrheniusHigh.n), '%.2f' % (kinetics.arrheniusHigh.Ea / 1000.), '%g' % (kinetics.arrheniusHigh.T0)])
        kineticsData.append('%g' % (kinetics.Tmin))
        kineticsData.append('%g' % (kinetics.Tmax))
        kineticsData.append('%g' % (kinetics.Pmin / 1.0e5))
        kineticsData.append('%g' % (kinetics.Pmax / 1.0e5))

    # Also include collision efficiencies for the relevant kinetics models
    efficiencies = []
    if isinstance(kinetics, ThirdBodyModel):
        for molecule, efficiency in kinetics.efficiencies.iteritems():
            efficiencies.append((getStructureMarkup(molecule), '%g' % efficiency))
    kineticsData.append(efficiencies)
    
    return kineticsData

def kineticsEntry(request, section, subsection, index):
    """
    A view for showing an entry in a kinetics database.
    """

    # Load the kinetics database, if necessary
    loadKineticsDatabase()

    # Determine the entry we wish to view
    try:
        database = getKineticsDatabase(section, subsection)
    except ValueError:
        raise Http404
    index = int(index)
    try:
        entry = database.entries[index]
    except KeyError:
        raise Http404
        
    # Get the structure of the item we are viewing
    reactants = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.reactants])
    products = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.products])
    arrow = '&hArr;' if entry.item.reversible else '&rarr;'
    reference = entry.reference
    if reference[1:3] == '. ':
        reference = reference[0:2] + '\ ' + reference[2:]

    # Prepare the kinetics data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, str):
        kineticsData = ['Link', database.entries[entry.data].index]
    else:
        kineticsData = prepareKineticsParameters(entry.data)

    return render_to_response('kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'reactants': reactants, 'arrow': arrow, 'products': products, 'reference': reference, 'kineticsData': kineticsData}, context_instance=RequestContext(request))
