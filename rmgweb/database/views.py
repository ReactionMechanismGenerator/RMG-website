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
import socket

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
        if section in ['libraries', ''] and len(database.kinetics.libraries) == 0:
            database.kinetics.loadLibraries(os.path.join(settings.DATABASE_PATH, 'kinetics', 'libraries'))
        if section in ['families', ''] and len(database.kinetics.families) == 0:
            database.kinetics.loadFamilies(os.path.join(settings.DATABASE_PATH, 'kinetics', 'families'))

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
    
    db = None
    try:
        if section == 'libraries':
            db = database.kinetics.libraries[subsection]
        elif section == 'families':
            subsection = subsection.split('/')
            if subsection[0] != '' and len(subsection) == 2:
                db = database.kinetics.families[subsection[0]]
                if subsection[1] == 'groups':
                    db = db.groups
                elif subsection[1] == 'rules':
                    db = db.rules
                elif subsection[1] == 'training':
                    db = db.training
                elif subsection[1] == 'test':
                    db = db.test
                elif subsection[1] == 'PrIMe':
                    db = db.PrIMe
                else:
                    db = None
        else:
            raise ValueError('Invalid value "%s" for section parameter.' % section)
    except KeyError:
        raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)
    return db

################################################################################

def load(request):
    """
    Load the RMG database and redirect to the database homepage.
    """
    loadDatabase()
    return HttpResponseRedirect(reverse(index))
    
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
        html += '<li class="kineticsEntry">\n'
        html += '<div class="kineticsLabel">'
        if len(entry.children) > 0:
            html += '<img id="button_{0}" class="treeButton" src="/media/tree-collapse.png"/>'.format(entry.index)
        else:
            html += '<img class="treeButton" src="/media/tree-blank.png"/>'
        html += '<a href="{0}">{1}. {2}</a>\n'.format(url, entry.index, entry.label)
        html += '<div class="kineticsData">\n'
        if entry.data is not None:
            for T in [300,400,500,600,800,1000,1500,2000]:
                html += '<span class="kineticsDatum">{0:.2f}</span> '.format(math.log10(entry.data.getRateCoefficient(T, P=1e5)))
        html += '</div>\n'
        # Recursively descend children (depth-first)
        if len(entry.children) > 0:
            html += '<ul id="children_{0}" class="kineticsSubTree">\n'.format(entry.index)
            html += getKineticsTreeHTML(database, section, subsection, entry.children)
            html += '</ul>\n'
        html += '</li>\n'
    return html

def kinetics(request, section='', subsection=''):
    """
    The RMG database homepage.
    """
    # Make sure section has an allowed value
    if section not in ['libraries', 'families', '']:
        raise Http404

    # Load the kinetics database, if necessary
    rmgDatabase = loadDatabase('kinetics', section)

    # Determine which subsection we wish to view
    database = None
    try:
        database = getKineticsDatabase(section, subsection)
    except ValueError:
        pass

    if database is not None:

        # A subsection was specified, so render a table of the entries in
        # that part of the database

        isGroupDatabase = False

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
            if isinstance(database, KineticsGroups):
                isGroupDatabase = True
                entry['structure'] = getStructureMarkup(entry0.item)
                entry['parent'] = entry0.parent
                entry['children'] = entry0.children
            else:
                entry['reactants'] = ' + '.join([getStructureMarkup(reactant) for reactant in entry0.item.reactants])
                entry['products'] = ' + '.join([getStructureMarkup(reactant) for reactant in entry0.item.products])
                entry['arrow'] = '&hArr;' if entry0.item.reversible else '&rarr;'
            
            entries.append(entry)
            
        return render_to_response('kineticsTable.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entries': entries, 'tree': tree, 'isGroupDatabase': isGroupDatabase}, context_instance=RequestContext(request))

    else:
        # No subsection was specified, so render an outline of the kinetics
        # database components
        kineticsLibraries = [(label, library) for label, library in rmgDatabase.kinetics.libraries.iteritems() if subsection in label]
        kineticsLibraries.sort()
        kineticsFamilies = [(label, family) for label, family in rmgDatabase.kinetics.families.iteritems() if subsection in label]
        kineticsFamilies.sort()
        return render_to_response('kinetics.html', {'section': section, 'subsection': subsection, 'kineticsLibraries': kineticsLibraries, 'kineticsFamilies': kineticsFamilies}, context_instance=RequestContext(request))
        
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
    if isinstance(database, KineticsGroups):
        numReactants = database.numReactants
    else:
        numReactants = len(entry.item.reactants)
        degeneracy = entry.item.degeneracy
    
    # Prepare the kinetics data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, str):
        kineticsParameters = ['Link', database.entries[entry.data].index]
        kineticsModel = None
    else:
        kineticsParameters = prepareKineticsParameters(entry.data, numReactants, degeneracy)
        kineticsModel = entry.data
        
    if isinstance(database, KineticsGroups):
        structure = getStructureMarkup(entry.item)
        return render_to_response('kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'structure': structure, 'reference': reference, 'referenceLink': referenceLink, 'referenceType': referenceType, 'kineticsParameters': kineticsParameters, 'kineticsModel': kineticsModel}, context_instance=RequestContext(request))
    else:
        reactants = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.reactants])
        products = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.products])
        arrow = '&hArr;' if entry.item.reversible else '&rarr;'
        return render_to_response('kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'reactants': reactants, 'arrow': arrow, 'products': products, 'reference': reference, 'referenceLink': referenceLink, 'referenceType': referenceType, 'kineticsParameters': kineticsParameters, 'kineticsModel': kineticsModel}, context_instance=RequestContext(request))    

def kineticsJavaEntry(request, entry, reactants_fig, products_fig, kineticsParameters, kineticsModel):
    section = ''
    subsection = ''
    databaseName = 'RMG-Java Database'
    reference = ''
    referenceLink = ''
    referenceType = ''
    arrow = '&hArr;'
    return render_to_response('kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': databaseName, 'entry': entry, 'reactants': reactants_fig, 'arrow': arrow, 'products': products_fig, 'reference': reference, 'referenceLink': referenceLink, 'referenceType': referenceType, 'kineticsParameters': kineticsParameters, 'kineticsModel': kineticsModel}, context_instance=RequestContext(request))

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

    # Go through database and group additivity kinetics entries
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

    ########################################
    # Find the RMG-Java kinetics entries

    #####
    def cleanresponse(response):
        """
        This function cleans up response from PopulateReactions server and gives a
        species dictionary and reactions list.
        """

        def formspecies(species):
            """
            This function takes a species string from RMG-Java containing both name
            and adjlist and returns them separately.
            """
            lines = species.split("\n")
            species_name = lines[0]
            adjlist = "\n".join(lines[1:])
            return species_name, adjlist

        # Split species dictionary from reactions list
        response = response.split("\n\n\n")
        species_list = response[0].split("\n\n")
        reactions = response[1].split("\n\n")
        reactions = reactions[1]

        # split species into adjacency lists with names
        species_dict = [formspecies(item) for item in species_list]

        # split reactions into list of single line reactions
        reactions_list = reactions.split("\n")

        return species_dict, reactions_list

 
    #####
    def searchreaction(reactionline, reactant1, reactant2, product1, product2):
        """
        Reads reaction line and returns True if reaction occurs:
        reactant1 + reactant2 --> product1 + product2
        
        Finds both bimolecular and unimolecular reactions for only 1 reactant input, or only 1 product 
        """

        lines = reactionline.split("\t")

        reaction_string = lines[0]
        reactants, products = reaction_string.split(" --> ")

        if reactants.find(reactant1) == -1 or reactants.find(reactant2) == -1 or products.find(product1) == -1 or products.find(product2) == -1:
            return False
        else:
            return True

    def extractkinetics(reactionline):
        """
        Takes a reaction line from RMG and creates Arrhenius object from
        the kinetic data, as well as extracts names of reactants, products and comments.

        Units from RMG-Java are in cm3, mol, s.
        Reference Temperature T0 = 1 K.
        """
        lines = reactionline.split("\t")

        reaction_string = lines[0]
        reactants, products = reaction_string.split(" --> ")
        reactants = reactants.split(" + ")
        products = products.split(" + ")

        KineticsModel = Arrhenius(
            A = (float(lines[1]),"cm**3/mol/s"),
            n = float(lines[2]),
            Ea = (float(lines[3]),"kcal/mol"),
            T0 = (1,"K"),
        )

        comments = "\t".join(lines[4:])
        entry = Entry(longDesc=comments)

        return reactants, products, KineticsModel, entry

    def identifyspecies(species_dict, species):
        """
        Given a species_dict list and the species adjacency list, identifies
        whether species is found in the list and returns its name if found.
        """
        molecule = Molecule().fromAdjacencyList(species)
        for name, adjlist in species_dict:
            listmolecule = Molecule().fromAdjacencyList(adjlist)
            if molecule.isIsomorphic(listmolecule) == True:
                return name

        return False

    def getspeciesstructure(species_dict, speciesname):
        """
        Given a species_dict list and the name of the species, returns structure of the species.
        Returns blank structure if not found.
        """
        structure = ''
        for name, adjlist in species_dict:
            if speciesname == name:
                molecule = Molecule().fromAdjacencyList(str(adjlist.replace(';', '\n')))
                structure = getStructureMarkup(molecule)
                return structure

        return structure

    # First send search request to PopulateReactions server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(10)
    client_socket.connect(("localhost", 5000))

    # Generate species list for Java request
    header1 = 'reactant1 (molecule/cm3) 1\n'
    popreactants = header1 + reactant1 + '\n\n'
    if reactant2 != '':
        header2 = 'reactant2 (molecule/cm3) 1\n'
        popreactants = popreactants + header2 + reactant2 + '\n\n'
    popreactants = popreactants + 'END' +'\n'

    # Send request to server
    print "SENDING REQUEST FOR RMG-JAVA SEARCH TO SERVER"
    client_socket.sendall(popreactants)
    partial_response = client_socket.recv(512)
    response = partial_response
    while partial_response:
        partial_response = client_socket.recv(512)
        response += partial_response
    client_socket.close()
    print "FINISHED REQUEST. CLOSED CONNECTION TO SERVER"

    # Clean response from server
    species_dict, reactions_list = cleanresponse(response)

    # Name the species in reaction
    reactant1_name = species_dict[0][0]

    reactant2_name = ''
    if reactant2 != '':
        reactant2_name = species_dict[1][0]
        # BIMOLECULAR

    product1_name = ''
    if product1 != '':
        product1_name = identifyspecies(species_dict, product1)

    product2_name = ''
    if product2 != '':
        product2_name = identifyspecies(species_dict, product2)


    # Both products were actually found in species dictionary or were blank
    if product1_name != False and product2_name != False:

        # Constants for all entries
        degeneracy = 1
        source = 'RMG-Java'

        # Search for da Reactions
        print 'SEARCHING FOR REACTIONS...\n'
        for reactionline in reactions_list:
            print reactionline + '\n'
            # Search for both forward and backward reactions
            indicator1 = searchreaction(reactionline, reactant1_name, reactant2_name, product1_name, product2_name)
            indicator2 = searchreaction(reactionline, product1_name, product2_name, reactant1_name, reactant2_name)

            if indicator1 == True or indicator2 == True:
                print 'FOUND A REACTION!'
                reactants, products, kineticsModel, entry = extractkinetics(reactionline)
                numReactants = len(reactants)
                numProducts = len(products)
                kineticsParameters = prepareKineticsParameters(kineticsModel, numReactants, degeneracy)

                # draw figures
                reactants_structures = [getspeciesstructure(species_dict, speciesname) for speciesname in reactants]
                products_structures = [getspeciesstructure(species_dict, speciesname) for speciesname in products]
                if numReactants == 2:
                    reactants_fig = ' + '.join(reactants_structures)
                else:
                    reactants_fig = reactants_structures[0]
                if numProducts == 2:
                    products_fig = ' + '.join(products_structures)
                else:
                    products_fig = products_structures[0]

                # Unused vars for render_to_response
                section = ''
                subsection = ''
                databaseName = 'RMG-Java Database'
                reference = ''
                referenceLink = ''
                referenceType = ''
                arrow = '&hArr;'

                #return render_to_response('kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': databaseName, 'entry': entry, 'reactants': reactants_fig, 'arrow': arrow, 'products': products_fig, 'reference': reference, 'referenceLink': referenceLink, 'referenceType': referenceType, 'kineticsParameters': kineticsParameters, 'kineticsModel': kineticsModel}, context_instance=RequestContext(request))
                
                #href = reverse(kineticsJavaEntry, kwargs={'entry': entry,'reactants_fig': reactants_fig, 'products_fig': products_fig, 'kineticsParameters': kineticsParameters, 'kineticsModel': kineticsModel})
                href = 'dummy link'
                kineticsDataList.append([reactants_fig, arrow, products_fig, entry, kineticsParameters, source, href])

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
