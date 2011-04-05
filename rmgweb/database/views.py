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
from rmgpy.data.thermo import ThermoDatabase
from rmgpy.data.kinetics import KineticsDatabase
from rmgpy.data.rmg import RMGDatabase

from forms import *

################################################################################

database = None

def loadDatabase(component='', section=''):
    """
    Load the requested `component` of the RMG database if not already done.
    """
    global database
    if not database:
        database = RMGDatabase()
        database.thermo = ThermoDatabase()
        database.kinetics = KineticsDatabase()

    if component in ['thermo', '']:
        if section in ['depository', ''] and len(database.thermo.depository) == 0:
            database.thermo.loadDepository(os.path.join(settings.DATABASE_PATH, 'thermo', 'depository'))
        if section in ['libraries', ''] and len(database.thermo.libraries) == 0:
            database.thermo.loadLibraries(os.path.join(settings.DATABASE_PATH, 'thermo', 'libraries'))
        if section in ['groups', ''] and len(database.thermo.groups) == 0:
            database.thermo.loadGroups(os.path.join(settings.DATABASE_PATH, 'thermo', 'groups'))
    if component in ['kinetics', '']:
        if section in ['depository', ''] and len(database.kinetics.depository) == 0:
            database.kinetics.loadDepository(os.path.join(settings.DATABASE_PATH, 'kinetics', 'depository'))
        if section in ['libraries', ''] and len(database.kinetics.libraries) == 0:
            database.kinetics.loadLibraries(os.path.join(settings.DATABASE_PATH, 'kinetics', 'libraries'))
        if section in ['groups', ''] and len(database.kinetics.groups) == 0:
            database.kinetics.loadGroups(os.path.join(settings.DATABASE_PATH, 'kinetics', 'groups'))

    return database

def getThermoDatabase(section, subsection):
    """
    Return the component of the thermodynamics database corresponding to the
    given `section` and `subsection`. If either of these is invalid, a
    :class:`ValueError` is raised.
    """
    global database

    try:
        if section == 'depository':
            db = database.thermo.depository[subsection]
        elif section == 'libraries':
            db = database.thermo.libraries[subsection]
        elif section == 'groups':
            db = database.thermo.groups[subsection]
        else:
            raise ValueError('Invalid value "%s" for section parameter.' % section)
    except KeyError:
        raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)
    return db

def getKineticsDatabase(section, subsection):
    """
    Return the component of the kinetics database corresponding to the
    given `section` and `subsection`. If either of these is invalid, a
    :class:`ValueError` is raised.
    """
    global database
    
    try:
        if section == 'depository':
            db = database.kinetics.depository[subsection]
        elif section == 'libraries':
            db = database.kinetics.libraries[subsection]
        elif section == 'groups':
            db = database.kinetics.groups[subsection]
        else:
            raise ValueError('Invalid value "%s" for section parameter.' % section)
    except KeyError:
        raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)
    return db

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
        structure = '<img src="%s"/>' % reverse('rmgweb.main.views.drawMolecule', kwargs={'adjlist': adjlist})
    elif isinstance(item, MoleculePattern):
        # We can draw MoleculePattern objects, so use that instead of an adjacency list
        adjlist = item.toAdjacencyList()
        adjlist = adjlist.replace('\n', ';')
        adjlist = re.sub('\s+', '%20', adjlist)
        structure = '<img src="%s"/>' % reverse('rmgweb.main.views.drawMoleculePattern', kwargs={'adjlist': adjlist})
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
    database = loadDatabase('thermo', section)

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

            if isinstance(entry.data, ThermoData): dataFormat = 'Group additivity'
            elif isinstance(entry.data, Wilhoit): dataFormat = 'Wilhoit'
            elif isinstance(entry.data, MultiNASA): dataFormat = 'NASA'
            elif isinstance(entry.data, str): dataFormat = 'Link'

            entries.append((entry.index,entry.label,structure,dataFormat))

        return render_to_response('thermoTable.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entries': entries}, context_instance=RequestContext(request))

    else:
        # No subsection was specified, so render an outline of the thermo
        # database components
        thermoDepository = [(label, depository) for label, depository in database.thermo.depository.iteritems()]
        thermoDepository.sort()
        thermoLibraries = [(label, library) for label, library in database.thermo.libraries.iteritems()]
        thermoLibraries.sort()
        thermoGroups = [(label, groups) for label, groups in database.thermo.groups.iteritems()]
        thermoGroups.sort()
        return render_to_response('thermo.html', {'section': section, 'subsection': subsection, 'thermoDepository': thermoDepository, 'thermoLibraries': thermoLibraries, 'thermoGroups': thermoGroups}, context_instance=RequestContext(request))

def prepareThermoParameters(thermo):
    """
    Collect the thermodynamic parameters for the provided thermodynamics model
    `thermo` and prepare them for viewing in a template. In particular, we must
    do any string formatting here because we can't do that in the template
    itself.
    """

    thermoData = {}
    
    if isinstance(thermo, ThermoData):
        # Thermo data is in group additivity format
        thermoData['format'] = 'Group additivity'
        thermoData['H298'] = ('%.2f' % (thermo.H298.value / 1000.),'kJ/mol')
        thermoData['S298'] = ('%.2f' % (thermo.S298.value),'J/mol \\cdot K')
        Cpdata = []
        for T, Cp in zip(thermo.Tdata.values, thermo.Cpdata.values):
            Cpdata.append(('%g' % (T),'K', '%.2f' % (Cp), 'J/mol \\cdot K'))
        thermoData['Cpdata'] = Cpdata
        
    elif isinstance(thermo, Wilhoit):
        # Thermo data is in Wilhoit polynomial format
        thermoData['format'] = 'Wilhoit'
        thermoData['cp0'] = ('%.2f' % (thermo.cp0.value),'J/mol \\cdot K')
        thermoData['cpInf'] = ('%.2f' % (thermo.cpInf.value),'J/mol \\cdot K')
        thermoData['a0'] = ('%s' % getLaTeXScientificNotation(thermo.a0.value),'')
        thermoData['a1'] = ('%s' % getLaTeXScientificNotation(thermo.a1.value),'')
        thermoData['a2'] = ('%s' % getLaTeXScientificNotation(thermo.a2.value),'')
        thermoData['a3'] = ('%s' % getLaTeXScientificNotation(thermo.a3.value),'')
        thermoData['B'] = ('%.2f' % (thermo.B.value),'K')
        thermoData['H0'] = ('%.2f' % (thermo.H0.value / 1000.),'kJ/mol')
        thermoData['S0'] = ('%.2f' % (thermo.S0.value),'J/mol \\cdot K')

    elif isinstance(thermo, MultiNASA):
        # Thermo data is in NASA polynomial format
        thermoData['format'] = 'NASA'
        thermoData['polynomials'] = []
        for poly in thermo.polynomials:
            thermoData['polynomials'].append({
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
        thermoData['Trange'] = ('%g' % (thermo.Tmin.value), '%g' % (thermo.Tmax.value), 'K')
    else:
        thermoData['Trange'] = None

    return thermoData

def thermoEntry(request, section, subsection, index):
    """
    A view for showing an entry in a thermodynamics database.
    """

    # Load the thermo database if necessary
    loadDatabase('thermo', section)

    # Determine the entry we wish to view
    try:
        database = getThermoDatabase(section, subsection)
    except ValueError:
        raise Http404
    index = int(index)
    for entry in database.entries.values():
        if entry.index == index:
            break
    else:
        raise Http404

    # Get the structure of the item we are viewing
    structure = getStructureMarkup(entry.item)

    # Prepare the thermo data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, str):
        thermoData = ['Link', database.entries[entry.data].index]
    else:
        thermoData = prepareThermoParameters(entry.data)

    reference = str(entry.reference)
    if reference[1:3] == '. ':
        reference = reference[0:2] + '\ ' + reference[2:]

    return render_to_response('thermoEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'structure': structure, 'reference': reference, 'thermoData': thermoData}, context_instance=RequestContext(request))

def thermoSearch(request):
    """
    A view of a form for specifying a molecule to search the database for
    thermodynamics properties.
    """

    # Load the thermo database if necessary
    loadDatabase('thermo')

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
    loadDatabase('thermo')

    adjlist = str(adjlist.replace(';', '\n'))
    molecule = Molecule().fromAdjacencyList(adjlist)

    # Get the thermo data for the molecule
    thermoDataList = []
    for data, library, entry in database.thermo.getAllThermoData(molecule):
        if library is None:
            source = 'Group additivity'
            href = ''
            #data = convertThermoData(data, molecule, Wilhoit)
            #data = convertThermoData(data, molecule, MultiNASA)
            entry = Entry(data=data)
        elif library in database.thermo.depository.values():
            source = 'Depository'
            href = reverse(thermoEntry, kwargs={'section': 'depository', 'subsection': library.label, 'index': entry.index})
        elif library in database.thermo.libraries:
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

    return render_to_response('thermoData.html', {'structure': structure, 'thermoDataList': thermoDataList, 'plotWidth': 500, 'plotHeight': 400 + 15 * len(thermoDataList)}, context_instance=RequestContext(request))

################################################################################

def kinetics(request, section='', subsection=''):
    """
    The RMG database homepage.
    """
    # Make sure section has an allowed value
    if section not in ['depository', 'libraries', 'groups', '']:
        raise Http404

    # Load the kinetics database, if necessary
    database = loadDatabase('kinetics', section)

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
            if isinstance(entry.data, KineticsData): dataFormat = 'KineticsData'
            elif isinstance(entry.data, Arrhenius): dataFormat = 'Arrhenius'
            elif isinstance(entry.data, str): dataFormat = 'Link'
            elif isinstance(entry.data, ArrheniusEP): dataFormat = 'ArrheniusEP'
            elif isinstance(entry.data, MultiArrhenius): dataFormat = 'MultiArrhenius'
            elif isinstance(entry.data, PDepArrhenius): dataFormat = 'PDepArrhenius'
            elif isinstance(entry.data, Chebyshev): dataFormat = 'Chebyshev'
            elif isinstance(entry.data, Troe): dataFormat = 'Troe'
            elif isinstance(entry.data, Lindemann): dataFormat = 'Lindemann'
            elif isinstance(entry.data, ThirdBody): dataFormat = 'ThirdBody'
            
            entries.append((entry.index,entry.label,reactants,arrow,products,dataFormat))

        return render_to_response('kineticsTable.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entries': entries}, context_instance=RequestContext(request))

    else:
        # No subsection was specified, so render an outline of the kinetics
        # database components
        kineticsDepository = [(label, depository) for label, depository in database.kinetics.depository.iteritems()]
        kineticsDepository.sort()
        kineticsLibraries = [(label, library) for label, library in database.kinetics.libraries.iteritems()]
        kineticsLibraries.sort()
        kineticsGroups = [(label, groups) for label, groups in database.kinetics.groups.iteritems()]
        kineticsGroups.sort()
        return render_to_response('kinetics.html', {'section': section, 'subsection': subsection, 'kineticsDepository': kineticsDepository, 'kineticsLibraries': kineticsLibraries, 'kineticsGroups': kineticsGroups}, context_instance=RequestContext(request))
        
def prepareKineticsParameters(kinetics, numReactants, degeneracy):
    """
    Collect the kinetics parameters for the provided kinetics model `kinetics`
    and prepare them for viewing in a template. In particular, we must do any
    string formatting here because we can't do that in the template itself.
    """

    kineticsData = {}

    if numReactants == 1:
        kunits = 's^{-1}'
    elif numReactants == 2:
        kunits = 'm^3/mol \\cdot s'
    else:
        kunits = 'm^%g/mol^%s \\cdot s' % (3*(numReactants-1), numReactants-1)

    if isinstance(kinetics, KineticsData):
        # Kinetics data is in KineticsData format
        kineticsData['format'] = 'KineticsData'
        kineticsData['kdata'] = []
        for T, k in zip(kinetics.Tdata.values, kinetics.kdata.values):
            kineticsData['kdata'].append(('%g' % (T),'K', getLaTeXScientificNotation(k), kunits))

    elif isinstance(kinetics, Arrhenius):
        # Kinetics data is in Arrhenius format
        kineticsData['format'] = 'Arrhenius'
        kineticsData['A'] = (getLaTeXScientificNotation(kinetics.A.value), kunits)
        kineticsData['n'] = ('%.2f' % (kinetics.n.value), '')
        kineticsData['Ea'] = ('%.2f' % (kinetics.Ea.value / 1000.), 'kJ/mol')
        kineticsData['T0'] = ('%g' % (kinetics.T0.value), 'K')

    elif isinstance(kinetics, ArrheniusEP):
        # Kinetics data is in ArrheniusEP format
        kineticsData['format'] = 'ArrheniusEP'
        kineticsData['A'] = (getLaTeXScientificNotation(kinetics.A.value), kunits)
        kineticsData['n'] = ('%.2f' % (kinetics.n.value), '')
        kineticsData['E0'] = ('%.2f' % (kinetics.E0.value / 1000.), 'kJ/mol')
        kineticsData['alpha'] = ('%g' % (kinetics.alpha.value), '')

    elif isinstance(kinetics, MultiArrhenius):
        # Kinetics data is in MultiArrhenius format
        kineticsData['format'] = 'MultiArrhenius'
        kineticsData['arrheniusList'] = []
        for arrh in kinetics.arrheniusList:
            kineticsData['arrheniusList'].append({
                'A': (getLaTeXScientificNotation(arrh.A.value), kunits),
                'n': ('%.2f' % (arrh.n.value), ''),
                'Ea': ('%.2f' % (arrh.Ea.value / 1000.), 'kJ/mol'),
                'T0': ('%g' % (arrh.T0.value), 'K'),
            })
            
    elif isinstance(kinetics, PDepArrhenius):
        # Kinetics data is in PDepArrhenius format
        kineticsData['format'] = 'PDepArrhenius'
        for P, arrh in zip(kinetics.pressures, kinetics.arrhenius):
            kineticsData['arrhenius'].append({
                'A': (getLaTeXScientificNotation(arrh.A.value), kunits),
                'n': ('%.2f' % (arrh.n.value), ''),
                'Ea': ('%.2f' % (arrh.Ea.value / 1000.), 'kJ/mol'),
                'T0': ('%g' % (arrh.T0.value), 'K'),
                'P': ('%g' % (P.value / 1e5), 'bar'),
            })

    elif isinstance(kinetics, Chebyshev):
        # Kinetics data is in Chebyshev format
        kineticsData['format'] = 'Chebyshev'
        coeffs = []
        for i in range(kinetics.degreeT):
            coeffs.append(['%g' % kinetics.coeffs[i,j] for j in range(kinetics.degreeP)])
        kineticsData['coeffs'] = (coeffs, kunits)
        
    elif isinstance(kinetics, Troe):
        # Kinetics data is in Troe format
        kineticsData['format'] = 'Troe'
        kineticsData['arrheniusHigh'] = {
            'A': (getLaTeXScientificNotation(kinetics.arrheniusHigh.A.value), kunits),
            'n': ('%.2f' % (kinetics.arrheniusHigh.n.value), ''),
            'Ea': ('%.2f' % (kinetics.arrheniusHigh.Ea.value / 1000.), 'kJ/mol'),
            'T0': ('%g' % (kinetics.arrheniusHigh.T0.value), 'K'),
        }
        kineticsData['arrheniusLow'] = {
            'A': (getLaTeXScientificNotation(kinetics.arrheniusLow.A.value), kunits),
            'n': ('%.2f' % (kinetics.arrheniusLow.n.value), ''),
            'Ea': ('%.2f' % (kinetics.arrheniusLow.Ea.value / 1000.), 'kJ/mol'),
            'T0': ('%g' % (kinetics.arrheniusLow.T0.value), 'K'),
        }
        kineticsData['alpha'] = ('%g' % (kinetics.alpha.value),'')
        kineticsData['T3'] = ('%g' % (kinetics.T3.value),'K')
        kineticsData['T1'] = ('%g' % (kinetics.T1.value),'K')
        if kinetics.T2 is not None:
            kineticsData['T2'] = ('%g' % (kinetics.T2.value),'K')
        else:
            kineticsData['T2'] = 'None'
        
    elif isinstance(kinetics, Lindemann):
        # Kinetics data is in Lindemann format
        kineticsData['format'] = 'Lindemann'
        kineticsData['arrheniusHigh'] = {
            'A': (getLaTeXScientificNotation(kinetics.arrheniusHigh.A.value), kunits),
            'n': ('%.2f' % (kinetics.arrheniusHigh.n.value), ''),
            'Ea': ('%.2f' % (kinetics.arrheniusHigh.Ea.value / 1000.), 'kJ/mol'),
            'T0': ('%g' % (kinetics.arrheniusHigh.T0.value), 'K'),
        }
        kineticsData['arrheniusLow'] = {
            'A': (getLaTeXScientificNotation(kinetics.arrheniusLow.A.value), kunits),
            'n': ('%.2f' % (kinetics.arrheniusLow.n.value), ''),
            'Ea': ('%.2f' % (kinetics.arrheniusLow.Ea.value / 1000.), 'kJ/mol'),
            'T0': ('%g' % (kinetics.arrheniusLow.T0.value), 'K'),
        }

    elif isinstance(kinetics, ThirdBody):
        # Kinetics data is in ThirdBody format
        kineticsData['format'] = 'ThirdBody'
        kineticsData['arrheniusHigh'] = {
            'A': (getLaTeXScientificNotation(kinetics.arrheniusHigh.A.value), kunits),
            'n': ('%.2f' % (kinetics.arrheniusHigh.n.value), ''),
            'Ea': ('%.2f' % (kinetics.arrheniusHigh.Ea.value / 1000.), 'kJ/mol'),
            'T0': ('%g' % (kinetics.arrheniusHigh.T0.value), 'K'),
        }

    # Also include collision efficiencies for the relevant kinetics models
    efficiencies = []
    if isinstance(kinetics, ThirdBody):
        for molecule, efficiency in kinetics.efficiencies.iteritems():
            efficiencies.append((getStructureMarkup(molecule), '%g' % efficiency))
        kineticsData['efficiencies'] = efficiencies

    # Also include the reaction path degeneracy
    kineticsData['degeneracy'] = '%i' % (degeneracy)

    # Set temperature and pressure ranges
    if kinetics.Tmin is not None and kinetics.Tmax is not None:
        kineticsData['Trange'] = ('%g' % (kinetics.Tmin.value), '%g' % (kinetics.Tmax.value), 'K')
    else:
        kineticsData['Trange'] = None
    if kinetics.Pmin is not None and kinetics.Pmax is not None:
        kineticsData['Prange'] = ('%g' % (kinetics.Pmin.value / 1e5), '%g' % (kinetics.Pmax.value / 1e5), 'bar')
    else:
        kineticsData['Prange'] = None

    return kineticsData

def kineticsEntry(request, section, subsection, index):
    """
    A view for showing an entry in a kinetics database.
    """

    # Load the kinetics database, if necessary
    loadDatabase('kinetics', section)

    # Determine the entry we wish to view
    try:
        database = getKineticsDatabase(section, subsection)
    except ValueError:
        raise Http404
    index = int(index)
    for entry in database.entries.values():
        if entry.index == index:
            break
    else:
        raise Http404
        
    # Get the structure of the item we are viewing
    reactants = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.reactants])
    products = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.products])
    arrow = '&hArr;' if entry.item.reversible else '&rarr;'
    reference = entry.reference
    if reference is not None and reference[1:3] == '. ':
        reference = reference[0:2] + '\ ' + reference[2:]

    # Prepare the kinetics data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, str):
        kineticsData = ['Link', database.entries[entry.data].index]
    else:
        kineticsData = prepareKineticsParameters(entry.data, len(entry.item.reactants), entry.item.degeneracy)

    return render_to_response('kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'reactants': reactants, 'arrow': arrow, 'products': products, 'reference': reference, 'kineticsData': kineticsData}, context_instance=RequestContext(request))

def kineticsSearch(request):
    """
    A view of a form for specifying a set of reactants to search the database
    for reactions.
    """

    # Load the kinetics database if necessary
    loadDatabase('kinetics')

    if request.method == 'POST':
        form = KineticsSearchForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            kwargs = {}

            reactant1 = form.cleaned_data['reactant1']
            kwargs['reactant1'] = re.sub('\s+', '%20', reactant1.replace('\n', ';'))

            reactant2 = form.cleaned_data['reactant2']
            if reactant2 != '':
                kwargs['reactant2'] = re.sub('\s+', '%20', reactant2.replace('\n', ';'))

            product1 = form.cleaned_data['product1']
            if product1 != '':
                kwargs['product1'] = re.sub('\s+', '%20', product1.replace('\n', ';'))

            product2 = form.cleaned_data['product2']
            if product2 != '':
                kwargs['product2'] = re.sub('\s+', '%20', product2.replace('\n', ';'))

            return HttpResponseRedirect(reverse(kineticsData, kwargs=kwargs))
    else:
        form = KineticsSearchForm()

    return render_to_response('kineticsSearch.html', {'form': form}, context_instance=RequestContext(request))

def kineticsData(request, reactant1, reactant2='', product1='', product2=''):
    """
    A view used to present a list of reactions and the associated kinetics
    for each.
    """
    from rmgpy.chem.molecule import Molecule

    # Load the kinetics database if necessary
    loadDatabase('kinetics')

    reactants = []

    reactant1 = str(reactant1.replace(';', '\n'))
    reactants.append(Molecule().fromAdjacencyList(reactant1))

    if reactant2 != '':
        reactants.append(Molecule().fromAdjacencyList(str(reactant2.replace(';', '\n'))))

    if product1 != '' or product2 != '':
        products = []
        if product1 != '':
            products.append(Molecule().fromAdjacencyList(str(product1.replace(';', '\n'))))
        if product2 != '':
            products.append(Molecule().fromAdjacencyList(str(product2.replace(';', '\n'))))
    else:
        products = None
    
    # Get the kinetics data for the reaction
    kineticsDataList = []
    for reaction, kinetics, library, entry in database.kinetics.generateReactions(reactants, products):
        reactants = ' + '.join([getStructureMarkup(reactant) for reactant in reaction.reactants])
        arrow = '&hArr;' if reaction.reversible else '&rarr;'
        products = ' + '.join([getStructureMarkup(reactant) for reactant in reaction.products])
        if library in database.kinetics.groups.values():
            source = '%s (Group additivity)' % (library.name)
            href = ''
            entry = Entry(data=kinetics)
        elif library in database.kinetics.depository.values():
            source = '%s (depository)' % (library.name)
            href = reverse(kineticsEntry, kwargs={'section': 'depository', 'subsection': library.label, 'index': entry.index})
        elif library in database.kinetics.libraries:
            source = library.name
            href = reverse(kineticsEntry, kwargs={'section': 'libraries', 'subsection': library.label, 'index': entry.index})
        kineticsDataList.append([reactants, arrow, products, entry, prepareKineticsParameters(kinetics, len(reaction.reactants), reaction.degeneracy), source, href])

    return render_to_response('kineticsData.html', {'kineticsDataList': kineticsDataList, 'plotWidth': 500, 'plotHeight': 400 + 15 * len(kineticsDataList)}, context_instance=RequestContext(request))

