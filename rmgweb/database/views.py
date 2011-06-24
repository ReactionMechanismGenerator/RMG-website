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

from rmgpy.molecule import Molecule
from rmgpy.group import Group
from rmgpy.thermo import *
from rmgpy.kinetics import *

from rmgpy.data.base import Entry
from rmgpy.data.thermo import ThermoDatabase
from rmgpy.data.kinetics import *
from rmgpy.data.rmg import RMGDatabase

from forms import *
from rmgweb.main.tools import *

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
            
            if entry.data is None:
                dataFormat = 'None'
                entry.index = 0
            
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
        thermoParameters = ['Link', database.entries[entry.data].index]
        thermoModel = None
    else:
        thermoParameters = prepareThermoParameters(entry.data)
        thermoModel = entry.data
        
    reference = ''; referenceLink = ''; referenceType = ''
    if entry.reference is not None:
        reference = str(entry.reference)
        referenceLink = entry.reference.url

    return render_to_response('thermoEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'structure': structure, 'reference': reference, 'referenceLink': referenceLink, 'referenceType': referenceType, 'thermoParameters': thermoParameters, 'thermoModel': thermoModel}, context_instance=RequestContext(request))

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
        elif library in database.thermo.libraries.values():
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

def getDatabaseTreeAsList(database, entries):
    """
    Return a list of entries in a given database, sorted by the order they
    appear in the tree (as determined via a depth-first search).
    """
    tree = []
    for entry in entries:
        # Write current node
        tree.append(entry)
        # Recursively descend children (depth-first)
        tree.extend(getDatabaseTreeAsList(database, entry.children))
    return tree

def getKineticsTreeHTML(database, section, subsection, entries):
    """
    Return a string of HTML markup used for displaying information about
    kinetics entries in a given `database` as a tree of unordered lists.
    """
    html = ''
    for entry in entries:
        # Write current node
        url = reverse(kineticsEntry, kwargs={'section': section, 'subsection': subsection, 'index': entry.index})
        html += '<li class="kineticsEntry"><div class="kineticsLabel"><a href="{0}">{1}. {2}</a><div class="kineticsData">[data for {1}]</div></div></li>\n'.format(url, entry.index, entry.label)
        # Recursively descend children (depth-first)
        if len(entry.children) > 0:
            html += '<ul class="kineticsSubTree">\n'
            html += getKineticsTreeHTML(database, section, subsection, entry.children)
            html += '</ul>\n'
    return html

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
        if database.top is not None and len(database.top) > 0:
            # If there is a tree in this database, only consider the entries
            # that are in the tree
            entries0 = getDatabaseTreeAsList(database, database.top)
            tree = '<ul class="kineticsTree">\n{0}\n</ul>\n'.format(getKineticsTreeHTML(database, section, subsection, database.top))
        else:
            # If there is not a tree, consider all entries
            entries0 = database.entries.values()
            # Sort the entries by index and label
            entries0.sort(key=lambda entry: (entry.index, entry.label))
            tree = ''
            
        entries = []

        for entry0 in entries0:

            dataFormat = ''
            if isinstance(entry0.data, KineticsData): dataFormat = 'KineticsData'
            elif isinstance(entry0.data, Arrhenius): dataFormat = 'Arrhenius'
            elif isinstance(entry0.data, str): dataFormat = 'Link'
            elif isinstance(entry0.data, ArrheniusEP): dataFormat = 'ArrheniusEP'
            elif isinstance(entry0.data, MultiArrhenius): dataFormat = 'MultiArrhenius'
            elif isinstance(entry0.data, PDepArrhenius): dataFormat = 'PDepArrhenius'
            elif isinstance(entry0.data, Chebyshev): dataFormat = 'Chebyshev'
            elif isinstance(entry0.data, Troe): dataFormat = 'Troe'
            elif isinstance(entry0.data, Lindemann): dataFormat = 'Lindemann'
            elif isinstance(entry0.data, ThirdBody): dataFormat = 'ThirdBody'

            entry = {
                'index': entry0.index,
                'label': entry0.label,
                'dataFormat': dataFormat,
            }
            if section == 'depository' or section == 'libraries':
                entry['reactants'] = ' + '.join([getStructureMarkup(reactant) for reactant in entry0.item.reactants])
                entry['products'] = ' + '.join([getStructureMarkup(reactant) for reactant in entry0.item.products])
                entry['arrow'] = '&hArr;' if entry0.item.reversible else '&rarr;'
            elif section == 'groups':
                entry['structure'] = getStructureMarkup(entry0.item)
            else:
                raise Http404
            
            entries.append(entry)
            
        return render_to_response('kineticsTable.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entries': entries, 'tree': tree}, context_instance=RequestContext(request))

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
        
    reference = ''; referenceLink = ''; referenceType = ''
    if entry.reference is not None:
        reference = str(entry.reference)
        referenceLink = entry.reference.url

    numReactants = 0; degeneracy = 1
    if section in ['depository', 'libraries']:
        numReactants = len(entry.item.reactants)
        degeneracy = entry.item.degeneracy
    elif section == 'groups':
        numReactants = len(database.forwardTemplate.reactants)

    # Prepare the kinetics data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, str):
        kineticsParameters = ['Link', database.entries[entry.data].index]
        kineticsModel = None
    else:
        kineticsParameters = prepareKineticsParameters(entry.data, numReactants, degeneracy)
        kineticsModel = entry.data
        
    if section in ['depository', 'libraries']:
        reactants = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.reactants])
        products = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.products])
        arrow = '&hArr;' if entry.item.reversible else '&rarr;'
        return render_to_response('kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'reactants': reactants, 'arrow': arrow, 'products': products, 'reference': reference, 'referenceLink': referenceLink, 'referenceType': referenceType, 'kineticsParameters': kineticsParameters, 'kineticsModel': kineticsModel}, context_instance=RequestContext(request))
    elif section == 'groups':
        structure = getStructureMarkup(entry.item)
        return render_to_response('kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'structure': structure, 'reference': reference, 'referenceLink': referenceLink, 'referenceType': referenceType, 'kineticsParameters': kineticsParameters, 'kineticsModel': kineticsModel}, context_instance=RequestContext(request))
    else:
        raise Http404

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
    for reaction in database.kinetics.generateReactions(reactants, products):
        reactants = ' + '.join([getStructureMarkup(reactant) for reactant in reaction.reactants])
        arrow = '&hArr;' if reaction.reversible else '&rarr;'
        products = ' + '.join([getStructureMarkup(reactant) for reactant in reaction.products])
        if isinstance(reaction, TemplateReaction):
            source = '%s (Group additivity)' % (reaction.family.name)
            href = ''
            entry = Entry(data=reaction.kinetics)
        elif isinstance(reaction, DepositoryReaction):
            source = '%s (depository)' % (reaction.depository.name)
            href = reverse(kineticsEntry, kwargs={'section': 'depository', 'subsection': reaction.depository.label, 'index': reaction.entry.index})
            entry = reaction.entry
        elif isinstance(reaction, LibraryReaction):
            source = reaction.library.name
            href = reverse(kineticsEntry, kwargs={'section': 'libraries', 'subsection': reaction.library.label, 'index': reaction.entry.index})
            entry = reaction.entry
        print reaction.kinetics, reaction
        kineticsDataList.append([reactants, arrow, products, entry, prepareKineticsParameters(reaction.kinetics, len(reaction.reactants), reaction.degeneracy), source, href])

    return render_to_response('kineticsData.html', {'kineticsDataList': kineticsDataList, 'plotWidth': 500, 'plotHeight': 400 + 15 * len(kineticsDataList)}, context_instance=RequestContext(request))


def moleculeSearch(request):
    """
    Creates webpage form to display molecule chemgraph upon entering adjacency list, smiles, or inchi, as well as searches for thermochemistry data.
    """

    if request.method == 'POST':
        posted = MoleculeSearchForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()

        if posted.is_valid():
                adjlist = posted.cleaned_data['species']
                inchi = posted.cleaned_data['species_inchi']
                smiles = posted.cleaned_data['species_smiles']

                if adjlist != '':
                    molecule = Molecule()
                    molecule.fromAdjacencyList(adjlist)
                    structure = getStructureMarkup(molecule)
                    initial['species_inchi'] = molecule.toInChI()
                    initial['species_smiles'] = molecule.toSMILES()


                elif inchi != '':
                     molecule = Molecule()
                     molecule.fromInChI(inchi)
                     adjlist = molecule.toAdjacencyList()
                     structure = getStructureMarkup(molecule)
                     print molecule.toAdjacencyList()
                     initial['species'] = molecule.toAdjacencyList()
                     initial['species_smiles'] = molecule.toSMILES()

                elif smiles != '':
                    molecule = Molecule()
                    molecule.fromSMILES(smiles)
                    adjlist = molecule.toAdjacencyList()
                    structure = getStructureMarkup(molecule)
                    initial['species'] = molecule.toAdjacencyList()
                    initial['species_inchi'] = molecule.toInChI()

                else:
                    structure = ''
        else:
            structure = ''

        form = MoleculeSearchForm(initial, error_class=DivErrorList)

        if 'thermo' in request.POST:
            return HttpResponseRedirect(reverse(thermoData, kwargs={'adjlist': adjlist}))

        if 'reset' in request.POST:
            form = MoleculeSearchForm()
            structure = ''

    else:
         form = MoleculeSearchForm()
         structure = ''
    
    return render_to_response('moleculeSearch.html', {'structure':structure,'form': form}, context_instance=RequestContext(request))
