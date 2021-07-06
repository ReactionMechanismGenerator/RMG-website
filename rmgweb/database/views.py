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

import http.cookiejar
import io
import json
import math
import os
import re
import shutil
import subprocess
import urllib
from functools import reduce

import rmgpy
from rmgpy.data.base import Entry, LogicAnd, LogicNode, LogicOr
from rmgpy.data.kinetics import KineticsDepository, KineticsGroups, \
                                TemplateReaction, LibraryReaction
from rmgpy.data.kinetics.depository import DepositoryReaction
from rmgpy.data.reference import Article, Book
from rmgpy.data.solvation import SoluteData, SolventData, SolvationCorrection
from rmgpy.data.statmech import GroupFrequencies
from rmgpy.data.thermo import find_cp0_and_cpinf
from rmgpy.data.transport import CriticalPointGroupContribution, TransportData
from rmgpy.exceptions import AtomTypeError, ReactionError
from rmgpy.kinetics import Arrhenius, ArrheniusEP, ArrheniusBM, KineticsData
from rmgpy.molecule import Group, Molecule, Atom, Bond
from rmgpy.molecule.adjlist import Saturator
from rmgpy.molecule.resonance import analyze_molecule, generate_resonance_structures
from rmgpy.molecule.filtration import filter_structures
from rmgpy.quantity import Quantity
from rmgpy.reaction import Reaction
from rmgpy.species import Species
from rmgpy.thermo import NASA, ThermoData, Wilhoit
from rmgpy.thermo.thermoengine import process_thermo_data

from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse

try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup

import rmgweb.settings
from rmgweb.database.forms import DivErrorList, EniSearchForm, KineticsEntryEditForm, \
                                  KineticsSearchForm, MoleculeSearchForm, RateEvaluationForm
from rmgweb.database.tools import database, generateReactions, generateSpeciesThermo, reactionHasReactants
from rmgweb.main.tools import getStructureInfo, groupToInfo, moleculeFromURL, moleculeToAdjlist

# from rmgweb.main.tools import moleculeToURL, moleculeFromURL

################################################################################


def load(request):
    """
    Load the RMG database and redirect to the database homepage.
    """
    database.load()
    return HttpResponseRedirect(reverse('database:index'))


def index(request):
    """
    The RMG database homepage.
    """
    return render(request, 'database.html')


def export(request, type):
    """
    Export the RMG database to the old RMG-Java format.
    """
    # Build archive filenames from git hash and compression type
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                  cwd=rmgweb.settings.DATABASE_PATH)[:7]
    base = 'RMG_database_{0}'.format(sha)
    file_zip = '{0}.zip'.format(base)
    file_tar = '{0}.tar.gz'.format(base)
    if type == 'zip':
        file = file_zip
    elif type == 'tar.gz':
        file = file_tar

    # Set output path
    path = os.path.join(rmgweb.settings.PROJECT_PATH, '..', 'database', 'export')
    output = os.path.join(path, 'RMG_database')

    # Assert archives do not already exist
    if not os.path.exists(os.path.join(path, file)):

        # Export old database
        cmd_export = ['python', rmgweb.settings.DATABASE_PATH + '../scripts/exportOldDatabase.py', output]
        subprocess.check_call(cmd_export)

        # Compress database to zip
        cmd_zip = ['zip', '-r', base, 'RMG_database']
        subprocess.check_output(cmd_zip, cwd=path)

        # Compress database to tar.gz
        cmd_tar = ['tar', '-czf', file_tar, 'RMG_database']
        subprocess.check_output(cmd_tar, cwd=path)

        # Make compressed databases group-writable
        os.chmod(os.path.join(path, file_zip), 0o664)
        os.chmod(os.path.join(path, file_tar), 0o664)

        # Remove exported database
        shutil.rmtree(output)

    # Redirect to requested compressed database
    return HttpResponseRedirect('export/{0}'.format(file))

#################################################################################################################################################


def transport(request, section='', subsection=''):
    """
    This function displays the transport database.
    """
    # Make sure section has an allowed value
    if section not in ['libraries', 'groups', '']:
        raise Http404

    database.load('transport', section)

    if subsection != '':

        # A subsection was specified, so render a table of the entries in
        # that part of the database

        # Determine which subsection we wish to view
        try:
            db = database.get_transport_database(section, subsection)
        except ValueError:
            raise Http404

        # Sort entries by index
        entries0 = list(db.entries.values())
        entries0.sort(key=lambda entry: entry.index)

        entries = []
        for entry in entries0:

            structure = getStructureInfo(entry.item)

            if isinstance(entry.data, CriticalPointGroupContribution):
                data_format = 'CriticalPointGroupContribution'
            elif isinstance(entry.data, TransportData):
                data_format = 'TransportData'

            elif entry.data is None:
                data_format = 'None'
                entry.index = 0

            else:
                data_format = 'Other'

            entries.append((entry.index, entry.label, structure, data_format))

        return render(request, 'transportTable.html',
                      {'section': section, 'subsection': subsection,
                       'databaseName': db.name, 'entries': entries}
                      )

    else:
        # No subsection was specified, so render an outline of the transport
        # database components and sort them
        transport_libraries = [(label, database.transport.libraries[label]) for label in database.transport.library_order]
        transport_libraries.sort()
        transport_groups = [(label, groups) for label, groups in database.transport.groups.items()]
        transport_groups.sort()
        return render(request, 'transport.html',
                      {'section': section, 'subsection': subsection,
                       'transportLibraries': transport_libraries, 'transportGroups': transport_groups}
                      )


def transportEntry(request, section, subsection, index):
    """
    A view for showing an entry in a transport database.
    """
    # Load the transport database
    database.load('transport', section)

    # Determine the entry we wish to view
    try:
        db = database.get_transport_database(section, subsection)
    except ValueError:
        raise Http404

    index = int(index)
    if index != 0 and index != -1:
        for entry in db.entries.values():
            if entry.index == index:
                break
        else:
            raise Http404
    else:
        if index == 0:
            index = min(entry.index for entry in db.entries.values() if entry.index > 0)
        else:
            index = max(entry.index for entry in db.entries.values() if entry.index > 0)
        return HttpResponseRedirect(reverse('database:transport-entry',
                                            kwargs={'section': section,
                                                    'subsection': subsection,
                                                    'index': index,
                                                    }))

    # Get the structure of the item we are viewing
    structure = getStructureInfo(entry.item)

    # Prepare the transport data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, str):
        transport = ['Link', db.entries[entry.data].index]
    else:
        transport = entry.data

    reference_type = ''
    reference = entry.reference
    return render(request, 'transportEntry.html',
                  {'section': section, 'subsection': subsection,
                   'databaseName': db.name, 'entry': entry,
                   'structure': structure, 'reference': reference,
                   'referenceType': reference_type, 'transport': transport})


def transportData(request, adjlist):
    """
    Returns an entry with the transport data when an adjacency list
    for a molecule is provided.  The transport data is estimated by RMG.
    """
    # Load the transport database if necessary
    database.load('transport')

    adjlist = urllib.parse.unquote(adjlist)
    molecule = Molecule().from_adjacency_list(adjlist)
    species = Species(molecule=[molecule])
    species.generate_resonance_structures()

    # Get the transport data for the molecule
    transport_data_list = []
    for data, library, entry in database.transport.get_all_transport_properties(species):
        if library is None:
            source = 'Group additivity'
            href = ''
            symmetry_number = species.get_symmetry_number()
            entry = Entry(data=data)
        elif library in database.transport.libraries.values():
            source = library.label
            href = reverse('database:transport-entry',
                           kwargs={'section': 'libraries',
                                   'subsection': library.label,
                                   'index': entry.index})
        transport_data_list.append((
            entry,
            data,
            source,
            href,
        ))

    # Get the structure of the item we are viewing
    structure = getStructureInfo(molecule)

    return render(request, 'transportData.html',
                  {'molecule': molecule,
                   'structure': structure,
                   'transportDataList': transport_data_list,
                   'symmetryNumber': symmetry_number})

#################################################################################################################################################

def solvationIndex(request):
    """
    The solvation tools homepage.
    """
    return render(request, 'solvationTools.html')


def solvation(request, section='', subsection=''):
    """
    This function displays the solvation database.
    """
    # Make sure section has an allowed value
    if section not in ['libraries', 'groups', '']:
        raise Http404

    database.load('solvation', section)

    if subsection != '':

        # A subsection was specified, so render a table of the entries in
        # that part of the database

        # Determine which subsection we wish to view
        try:
            db = database.get_solvation_database(section, subsection)
        except ValueError:
            raise Http404
        # Sort entries by index
        entries0 = list(db.entries.values())
        entries0.sort(key=lambda entry: entry.index)

        entries = []
        for entry in entries0:
            structures = []

            if type(entry.item) is list: # the case for solvents
                for structure in entry.item:
                    structures.append(getStructureInfo(structure))
            else: # single values for solutes
                structures.append(getStructureInfo(entry.item))

            if isinstance(entry.data, SoluteData):
                data_format = 'SoluteData'
            elif isinstance(entry.data, SolventData):
                data_format = 'SolventData'

            elif entry.data is None:
                data_format = 'None'
                # entry.index = 0

            else:
                data_format = 'Other'

            entries.append((entry.index, entry.label, structures, data_format))

        return render(request, 'solvationTable.html',
                      {'section': section,
                       'subsection': subsection,
                       'databaseName': db.name,
                       'entries': entries})

    else:
        # No subsection was specified, so render an outline of the solvation
        # database components and sort them
        solvation_libraries = []
        solvation_libraries.append(('solvent', database.solvation.libraries['solvent']))
        solvation_libraries.append(('solute', database.solvation.libraries['solute']))
        solvation_libraries.sort()
        solvation_groups = [(label, groups) for label, groups in database.solvation.groups.items()]
        solvation_groups.sort()
        return render(request, 'solvation.html',
                      {'section': section,
                       'subsection': subsection,
                       'solvationLibraries': solvation_libraries,
                       'solvationGroups': solvation_groups})


def solvationEntry(request, section, subsection, index):
    """
    A view for showing an entry in a solvation database.
    """
    # Load the solvation database
    database.load('solvation', section)

    # Determine the entry we wish to view
    try:
        db = database.get_solvation_database(section, subsection)
    except ValueError:
        raise Http404

    index = int(index)
    for entry in db.entries.values():
        if entry.index == index:
            break
    else:
        raise Http404

    # Get the structures of the item we are viewing
    structures = []

    if type(entry.item) is list: # the case for solvents
        for structure in entry.item:
            structures.append(getStructureInfo(structure))
    else: # single values for solutes
        structures.append(getStructureInfo(entry.item))

    # Prepare the solvation data for passing to the template. This includes all string formatting,
    # since we can't do that in the template.
    # Case 1. A solvation group uses the values of other group. In this case, get the href link of that group.
    if isinstance(entry.data, str):
        lib_index = db.entries[entry.data].index
        href = reverse('database:solvation-entry',
                       kwargs={'section': section, 'subsection': subsection, 'index': lib_index})
        solvation = ['Link', href, entry.data]
    # Case 2. A solvation group has empty data because it is a general group that doesn't need the group value.
    # Returns None for this
    elif entry.data is None:
        solvation = None
    # Case 3. The entry has an actual solute or solvent data. Returns the entry.
    else:
        solvation = entry

    reference_type = ''
    reference = entry.reference
    return render(request, 'solvationEntry.html',
                  {'section': section, 'subsection': subsection,
                   'databaseName': db.name, 'entry': entry,
                   'structures': structures, 'reference': reference,
                   'referenceType': reference_type, 'solvation': solvation})


def solvationData(request, solute_adjlist, solvent='', solvent_temp='', temp=''):
    """
    Returns an entry with the solute data for a given molecule
    when the solute_adjlist is provided. If solvent is provided,
    the interaction solvation quantities are also displayed.
    The solvation data is estimated by RMG.
    """
    # from rmgpy.data.solvation import getAllSoluteData
    # Load the solvation database if necessary
    database.load('solvation')
    db = database.get_solvation_database('', '')

    # obtain solvent data if it's specified.  Then get the interaction solvation properties and store them in solvationDataList
    # if the temperature-dependent option is selected, temperature-dependent option overrides the first option and
    # obtain solvent data for solvent_temp and solvation data at the specified temperature
    solvent_data = None
    solvent_label = None
    if solvent_temp != 'None':
        solvent_data = db.get_solvent_data(solvent_temp)  # only 1 entry for solvent data
        solvent_label = solvent_temp
    elif solvent != 'None':
        solvent_data = db.get_solvent_data(solvent)  # only 1 entry for solvent data
        solvent_label = solvent

    solvent_data_info = None
    if not solvent_label is None:
        lib_index = database.solvation.libraries['solvent'].entries[solvent_label].index
        solvent_href = reverse('database:solvation-entry',
                               kwargs={'section': 'libraries', 'subsection': 'solvent',
                                       'index': lib_index})
        solvent_data_info = (solvent_label, solvent_data, solvent_href)

    # molecule = Molecule().from_adjacency_list(adjlist)
    molecule = moleculeFromURL(solute_adjlist)
    solute = Species(molecule=[molecule])
    solute.generate_resonance_structures()

    # obtain solute data.
    solvation_data_list = []
    word_list = []
    ref_dict = {}
    for data, library, entry in db.get_all_solute_data(solute):    # length either 1 or 2 entries
        if library is None:
            source = 'Group additivity'
            href = ''
            ref_dict, word_list = parseSoluteDataComment(data.comment)
            entry = Entry(data=data)
        else:
            source = 'Solute Descriptors Library'
            href = reverse('database:solvation-entry',
                           kwargs={'section': 'libraries', 'subsection': 'solute', 'index': entry.index})
        # get solvation correction if solvent_data is not None
        correction = ''
        correction_temp = ''
        if solvent_data:
            if solvent_temp != 'None':
                temp = float(temp)
                Kfactor = db.get_Kfactor(data, solvent_data, temp)
                dGsolv = db.get_T_dep_solvation_energy(data, solvent_data, temp)
                correction_temp = [Kfactor, dGsolv, temp]
            # get the available solvation corrections
            abraham_parameter_list = [solvent_data.s_g, solvent_data.b_g, solvent_data.e_g, solvent_data.l_g,
                                      solvent_data.a_g, solvent_data.c_g]
            mintz_parameter_list = [solvent_data.s_h, solvent_data.b_h, solvent_data.e_h, solvent_data.l_h,
                                    solvent_data.a_h, solvent_data.c_h]
            dGsolv298 = None
            dHsolv298 = None
            dSsolv298 = None
            if not any(param is None for param in abraham_parameter_list):
                dGsolv298 = db.calc_g(data, solvent_data)
            if not any(param is None for param in mintz_parameter_list):
                dHsolv298 = db.calc_h(data, solvent_data)
            if dGsolv298 is not None and dHsolv298 is not None:
                dSsolv298 = db.calc_s(dGsolv298, dHsolv298)
            correction = SolvationCorrection(enthalpy=dHsolv298, gibbs=dGsolv298, entropy=dSsolv298)

        solvation_data_list.append((
            entry,
            data,
            source,
            href,
            correction,
            correction_temp,
        ))


    # Get the structure of the item we are viewing. Get the solvent structures if the input solvent is passed in.
    solvent_structures = []
    structures = None
    if solvent_temp != 'None':
        structures = db.libraries['solvent'].entries[solvent_temp].item
    elif solvent != 'None':
        structures = db.libraries['solvent'].entries[solvent].item
    if structures:
        for structure in structures: # we expect this to always be a list, as we are parsing solvents
            solvent_structures.append(getStructureInfo(structure))

    solute_structure = getStructureInfo(molecule)
    

    return render(request, 'solvationData.html',
                  {'molecule': molecule,
                   'solventStructures': solvent_structures,
                   'soluteStructure': solute_structure,
                   'solvationDataList': solvation_data_list,
                   'solventDataInfo': solvent_data_info,
                   'ref_dict': ref_dict,
                   'word_list': word_list})


def parseSoluteDataComment(comment):
    """
    Takes a SoluteData comment (or any string) as input. Returns a dictionary whose keys
    correspond to groups or libraries exactly as they appear in the string, and whose values
    correspond to href links that direct to the specific library or group's database page.
    """

    ref_dict = {}
    word_list = []

    # Search for library strings.
    # Example: Solvation thermo for [O]CCCCl from Solute library: Solute library: butan-1-ol + halogen(Cl-(Cs-CsHH)) + radical(ROJ)
    library_split_string = comment.split("Solute library: ")
    if len(library_split_string) > 1:  # if a match was found for "Solute library: "
        library_substring = library_split_string[1].split('+')
        lib_solute_species = library_substring[0].strip() # Example: 'butan-1-ol'
        lib_source_full = comment.split('+')[0].strip()
        word_list.append(lib_source_full)
        try:
            lib_index = database.solvation.libraries['solute'].entries[lib_solute_species].index
            ref_dict[lib_source_full] = reverse('database:solvation-entry',
                                                    kwargs={'section': 'libraries', 'subsection': 'solute',
                                                            'index': lib_index})
        except KeyError:
            ref_dict[lib_source_full] = reverse('database:solvation',
                                                    kwargs={'section': 'libraries', 'subsection': 'solute'})

        # remove the library string after we process it
        comment = comment.replace(lib_source_full, '')

    # Search for group additivity substrings
    word_list += comment.split()
    groups_substrings = [word for word in comment.split() if
                         "missing" not in word and '(' and ')' in word]  # Example: ['halogen(Cl-(Cs-CsHH))', 'radical(ROJ)']

    for word in groups_substrings:
        group_source_full = word  # Example: 'halogen(Cl-(Cs-CsHH))'
        group_name = word.split('(', 1)[0]  # Example: 'halogen'
        word = word.split('(', 1)[1]  # Example: 'Cl-(Cs-CsHH))'
        word = word[::-1].replace(')', '', 1)[::-1]  # Example: 'Cl-(Cs-CsHH)'
        if word.endswith('.'):
            word = word[::-1].replace('.', '', 1)[::-1]
        try:
            group_index = database.solvation.groups[group_name].entries[word].index
            ref_dict[group_source_full] = reverse('database:solvation-entry',
                                                  kwargs={'section': 'groups', 'subsection': group_name,
                                                          'index': group_index})
        except KeyError:
            pass

    return ref_dict, word_list



def solvationSolventData(request, solvent_adjlist):
    """
    Returns an entry with the solvent data for a given molecule
    when the solvent_adjlist is provided. If the given solvent
    molecule is not available in the RMG-database, then nothing
    is displayed.
    """
    # Load the solvation database if necessary
    database.load('solvation')
    db = database.get_solvation_database('', '')

    molecule = moleculeFromURL(solvent_adjlist)
    solvent = Species(molecule=[molecule])
    solvent.generate_resonance_structures()

    # obtain solvent data.
    solvent_data_list = db.get_all_solvent_data(solvent)    # this gives a list of tuple (solvent_label, solvent_entry)
    # get the href for each solvent
    solvent_info_list = []
    for solvent_label, solvent_entry in solvent_data_list:
        lib_index = database.solvation.libraries['solvent'].entries[solvent_label].index
        solvent_href = reverse('database:solvation-entry',
                               kwargs={'section': 'libraries', 'subsection': 'solvent',
                                       'index': lib_index})
        solvent_info_list.append((solvent_label, solvent_entry, solvent_href))

    # Get the structure of the item we are viewing
    structure = getStructureInfo(molecule)

    return render(request, 'solvationSolventData.html',
                  {'molecule': molecule,
                   'structure': structure,
                   'solventInfoList': solvent_info_list})


#################################################################################################################################################


def statmech(request, section='', subsection=''):
    """
    This function displays the statmech database.
    """
    # Make sure section has an allowed value
    if section not in ['depository', 'libraries', 'groups', '']:
        raise Http404

    database.load('statmech', section)

    if subsection != '':

        # A subsection was specified, so render a table of the entries in
        # that part of the database

        # Determine which subsection we wish to view
        try:
            db = database.get_statmech_database(section, subsection)
        except ValueError:
            raise Http404

        # Sort entries by index
        entries0 = list(db.entries.values())
        entries0.sort(key=lambda entry: entry.index)

        entries = []
        for entry in entries0:
            structure = getStructureInfo(entry.item)
            if isinstance(entry.data, GroupFrequencies):
                data_format = 'GroupFrequencies'
            else:
                data_format = 'Other'

            entries.append((entry.index, entry.label, structure, data_format))

        return render(request, 'statmechTable.html',
                      {'section': section,
                       'subsection': subsection,
                       'databaseName': db.name,
                       'entries': entries})
    else:
        # No subsection was specified, so render an outline of the statmech
        # database components and sort them
        statmech_depository = [(label, depository) for label, depository in database.statmech.depository.items()]
        statmech_depository.sort()
        statmech_libraries = [(name, database.statmech.libraries[name]) for name in database.statmech.library_order]
        statmech_libraries.sort()
        statmech_groups = [name for name in database.statmech.groups.items()]
        statmech_groups.sort()
        return render(request, 'statmech.html', {'section': section, 'subsection': subsection, 'statmechDepository': statmech_depository, 'statmechLibraries': statmech_libraries, 'statmechGroups': statmech_groups})


def statmechEntry(request, section, subsection, index):
    """
    A view for showing an entry in a statmech database.
    """
    # Load the statmech database
    database.load('statmech', section)

    # Determine the entry we wish to view
    try:
        db = database.get_statmech_database(section, subsection)
    except ValueError:
        raise Http404

    index = int(index)
    if index != 0 and index != -1:
        for entry in db.entries.values():
            if entry.index == index:
                break
        else:
            raise Http404
    else:
        if index == 0:
            index = min(entry.index for entry in db.entries.values() if entry.index > 0)
        else:
            index = max(entry.index for entry in db.entries.values() if entry.index > 0)
        return HttpResponseRedirect(reverse('database:statmech-entry',
                                            kwargs={'section': section,
                                                    'subsection': subsection,
                                                    'index': index,
                                                    }))

    # Get the structure of the item we are viewing
    structure = getStructureInfo(entry.item)

    # Prepare the statmech data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, str):
        statmech = ['Link', db.entries[entry.data].index]
    else:
        statmech = entry.data

    reference_type = ''
    reference = entry.reference
    return render(request, 'statmechEntry.html',
                  {'section': section, 'subsection': subsection,
                   'databaseName': db.name, 'entry': entry,
                   'structure': structure, 'reference': reference,
                   'referenceType': reference_type, 'statmech': statmech})


def statmechData(request, adjlist):
    """
    Returns an entry with the statmech data for a given molecule
    when the adjlist is provided.  The statmech data is estimated by RMG.
    """

    # Load the statmech database if necessary
    database.load('statmech')

    adjlist = urllib.parse.unquote(adjlist)
    molecule = Molecule().from_adjacency_list(adjlist)
    species = Species(molecule=[molecule])
    species.generate_resonance_structures()
    # Get the statmech data for the molecule

    symmetry_number = species.get_symmetry_number()
    statmech_data_list = []
    source = 'Solute Descriptors'
    href = reverse('database:statmech-entry', kwargs={'section': 'libraries', 'subsection': source, 'index': 1})
    statmech_data_list.append((1, database.statmech.get_solvent_data(species.label), source, href))

    # Get the structure of the item we are viewing
    structure = getStructureInfo(molecule)

    return render(request, 'statmechData.html', {'molecule': molecule, 'structure': structure, 'statmechDataList': statmech_data_list, 'symmetryNumber': symmetry_number})

#################################################################################################################################################


def thermo(request, section='', subsection=''):
    """
    The RMG database homepage.
    """
    # Make sure section has an allowed value
    if section not in ['depository', 'libraries', 'groups', '']:
        raise Http404

    # Load the thermo database if necessary
    database.load('thermo', section)

    if subsection != '':

        # A subsection was specified, so render a table of the entries in
        # that part of the database

        # Determine which subsection we wish to view
        try:
            db = database.get_thermo_database(section, subsection)
        except ValueError:
            raise Http404

        # Sort entries by index
        entries0 = list(db.entries.values())
        entries0.sort(key=lambda entry: entry.index)

        entries = []
        for entry in entries0:

            structure = getStructureInfo(entry.item)

            if isinstance(entry.data, ThermoData):
                data_format = 'Group additivity'
            elif isinstance(entry.data, Wilhoit):
                data_format = 'Wilhoit'
            elif isinstance(entry.data, NASA):
                data_format = 'NASA'
            elif isinstance(entry.data, str):
                data_format = 'Link'
            elif isinstance(entry.item, (LogicNode, LogicOr, LogicAnd)):
                data_format = 'Logic'

            elif entry.data is None:
                data_format = 'None'
                entry.index = 0
            else:
                data_format = 'Other'

            entries.append((entry.index, entry.label, structure, data_format))

        return render(request, 'thermoTable.html', {'section': section, 'subsection': subsection, 'databaseName': db.name, 'entries': entries})

    else:
        # No subsection was specified, so render an outline of the thermo
        # database components
        thermo_depository = [(label, depository) for label, depository in database.thermo.depository.items()]
        thermo_depository.sort()
        thermo_libraries = [(label, database.thermo.libraries[label]) for label in database.thermo.library_order]
        # If they weren't already sorted in our preferred order, we'd call thermoLibraries.sort()
        thermo_groups = [(label, groups) for label, groups in database.thermo.groups.items()]
        thermo_groups.sort()
        return render(request, 'thermo.html', {'section': section, 'subsection': subsection, 'thermoDepository': thermo_depository, 'thermoLibraries': thermo_libraries, 'thermoGroups': thermo_groups})


def thermoEntry(request, section, subsection, index):
    """
    A view for showing an entry in a thermodynamics database.
    """
    from rmgpy.chemkin import write_thermo_entry
    from rmgpy.data.thermo import find_cp0_and_cpinf

    # Load the thermo database if necessary
    database.load('thermo', section)

    # Determine the entry we wish to view
    try:
        db = database.get_thermo_database(section, subsection)
    except ValueError:
        raise Http404
    index = int(index)
    if index != 0 and index != -1:
        for entry in db.entries.values():
            if entry.index == index:
                break
        else:
            raise Http404
    else:
        if index == 0:
            index = min(entry.index for entry in db.entries.values() if entry.index > 0)
        else:
            index = max(entry.index for entry in db.entries.values() if entry.index > 0)
        return HttpResponseRedirect(reverse('database:thermo-entry',
                                            kwargs={'section': section,
                                                    'subsection': subsection,
                                                    'index': index,
                                                    }))

    # Get the structure of the item we are viewing
    structure = getStructureInfo(entry.item)

    # Prepare the thermo data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, str):
        thermo = ['Link', db.entries[entry.data].index]
    else:
        thermo = entry.data

    # Get the thermo data for the molecule
    nasa_string = None
    if isinstance(entry.item, Molecule):
        species = Species(molecule=[entry.item])
        species.generate_resonance_structures()
        find_cp0_and_cpinf(species, thermo)
        nasa_string = ''
        try:
            if isinstance(thermo, NASA):
                nasa = thermo
            else:
                nasa = thermo.to_nasa(Tmin=100.0, Tmax=5000.0, Tint=1000.0)
            species.thermo = nasa
            nasa_string = write_thermo_entry(species)
        except:
            pass

    reference_type = ''
    reference = entry.reference
    return render(request, 'thermoEntry.html', {'section': section, 'subsection': subsection, 'databaseName': db.name, 'entry': entry, 'structure': structure, 'reference': reference, 'referenceType': reference_type, 'thermo': thermo, 'nasa_string': nasa_string})


def thermoData(request, adjlist):
    """
    Returns an image of the provided adjacency list `adjlist` for a molecule.
    Note that the newline character cannot be represented in a URL;
    semicolons should be used instead.
    """
    # Load the thermo database if necessary
    database.load('thermo')
    from rmgpy.chemkin import write_thermo_entry

    adjlist = urllib.parse.unquote(adjlist)
    molecule = Molecule().from_adjacency_list(adjlist)
    species = Species(molecule=[molecule])
    species.generate_resonance_structures()

    # Get the thermo data for the molecule
    symmetry_number = None
    thermo_data_list = []
    word_list = []
    ref_dict = {}

    for data, library, entry in database.thermo.get_all_thermo_data(species):
        # Make sure we calculate Cp0 and CpInf
        find_cp0_and_cpinf(species, data)
        # Round trip conversion via Wilhoit for proper fitting
        nasa = process_thermo_data(species, data)
        # Generate Chemkin style NASA polynomial
        species.thermo = nasa
        nasa_string = write_thermo_entry(species)

        if library is None:
            source = 'Group additivity'
            href = ''
            ref_dict = parseThermoComment(data.comment)
            symmetry_number = species.get_symmetry_number()
            entry = Entry(data=data)
            if data.comment is not None:
                word_list = data.comment.split()
                            
        elif library in list(database.thermo.depository.values()):
            source = 'Depository'
            href = reverse('database:thermo-entry', kwargs={'section': 'depository', 'subsection': library.label, 'index': entry.index})
        elif library in list(database.thermo.libraries.values()):
            source = library.name
            href = reverse('database:thermo-entry', kwargs={'section': 'libraries', 'subsection': library.label, 'index': entry.index})
        thermo_data_list.append((
            entry,
            data,
            source,
            href,
            nasa_string,
        ))

    # Get the structure of the item we are viewing
    structure = getStructureInfo(molecule)

    return render(request, 'thermoData.html', {'molecule': molecule, 'structure': structure, 'thermo_data_list': thermo_data_list, 'symmetry_number': symmetry_number, 'ref_dict': ref_dict, 'word_list': word_list, 'plotWidth': 500, 'plotHeight': 400 + 15 * len(thermo_data_list)})


def parseThermoComment(comment):
    """
    Takes a thermo comment (or any string) as input. Returns a dictionary whose keys 
    correspond to groups or libraries exactly as they appear in the string, and whose values 
    correspond to href links that direct to the specific library or group's database page.
    """
    
    ref_dict = {}

    # Search for library strings.
    # Example: Gas phase thermo for [C]=O from Thermo library: DFT_QCI_thermo + radical(CdCdJ2_triplet). Adsorption correction: + Thermo group additivity estimation: adsorptionPt111(C=*(=R))    
    library_split_string  = comment.split("Thermo library: ")
    gas_phase_substring = library_split_string[0].split() # Example: ['Gas', 'phase', 'thermo', 'for', '[C]=O', 'from']
    if len(library_split_string) > 1: # if a match was found for "Thermo library: "
        if library_split_string[0] != '': 
            try:
                gas_phase_species = gas_phase_substring[-2] # Example: '[C]=O'
            except IndexError:
                gas_phase_species = '' 
        else:
            gas_phase_species = ''
        library_substring = library_split_string[1].split() #Example: ['DFT_QCI_thermo', '+', 'radical(CdCdJ2_triplet).', 'Adsorption', 'correction:', '+', 'Thermo', 'group', 'additivity', 'estimation:', 'adsorptionPt111(C=*(=R))']
        library_source_full = library_substring[0] # Example: 'DFT_QCI_thermo'

        if library_source_full.endswith('.'): # if the library ends with a period, make sure we get the correct library so we can get its link properly
            library_source = library_source_full[::-1].replace('.','',1)[::-1] 
        else:
            library_source = library_source_full

        try:
            lib_index = database.thermo.libraries[library_source].entries[gas_phase_species].index
            ref_dict[library_source_full] = reverse('database:thermo-entry', kwargs={'section': 'libraries', 'subsection': library_source, 'index': lib_index})
        except KeyError:
            ref_dict[library_source_full] = reverse('database:thermo', kwargs={'section': 'libraries', 'subsection': library_source})

    # Search for group additivity substrings
    # Example: Gas phase thermo for [C]=O from Thermo library: DFT_QCI_thermo + radical(CdCdJ2_triplet). Adsorption correction: + Thermo group additivity estimation: adsorptionPt111(C=*(=R))    
    groups_substrings = [word for word in comment.split() if "missing" not in word and '(' and ')' in word] # Example: ['radical(CdCdJ2_triplet).', 'adsorptionPt111(C=*(=R))']
    for word in groups_substrings:  
        group_source_full = word  # Example: 'adsorptionPt111(C=*(=R))'
        group_name = word.split('(',1)[0] # Example: 'adsorptionPt111'
        word = word.split('(',1)[1] # Example: 'C=*(=R))'
        word = word[::-1].replace(')','',1)[::-1] # Example: 'C=*(=R)'
        if word.endswith('.'): # e.g. in the case of 'CdCdJ2_triplet.'
            word = word[::-1].replace('.','',1)[::-1] 
        try: 
            group_index = database.thermo.groups[group_name].entries[word].index
            ref_dict[group_source_full] = reverse('database:thermo-entry', kwargs={'section': 'groups', 'subsection': group_name, 'index': group_index})
        except KeyError:
            pass                            

    return ref_dict

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
        url = reverse('database:kinetics-entry', kwargs={'section': section, 'subsection': subsection, 'index': entry.index})
        html += '<li class="kineticsEntry">\n'
        html += '<div class="kineticsLabel">'
        if len(entry.children) > 0:
            html += '<img id="button_{0}" class="treeButton" src="{1}"/>'.format(entry.index, static('img/tree-collapse.png'))
        else:
            html += '<img class="treeButton" src="{0}"/>'.format(static('img/tree-blank.png'))
        html += '<a href="{0}">{1}. {2}</a>\n'.format(url, entry.index, entry.label)
        html += '<div class="kineticsData">\n'
        if entry.data is not None:
            for T in [300, 400, 500, 600, 800, 1000, 1500, 2000]:
                html += '<span class="kineticsDatum">{0:.2f}</span> '.format(math.log10(entry.data.get_rate_coefficient(T, P=1e5)))
        html += '</div>\n'
        # Recursively descend children (depth-first)
        if len(entry.children) > 0:
            html += '<ul id="children_{0}" class="kineticsSubTree">\n'.format(entry.index)
            html += getKineticsTreeHTML(database, section, subsection, entry.children)
            html += '</ul>\n'
        html += '</li>\n'
    return html


def getUntrainedReactions(family):
    """
    Return a depository containing unique reactions for which no
    training data exists.
    """
    # Load training depository
    for depository in family.depositories:
        if 'training' in depository.label:
            training = depository
            break
    else:
        raise Exception('Could not find training depository in {0} family.'.format(family.label))

    # Load trained reactions
    trained_reactions = []
    for entry in training.entries.values():
        for reaction in trained_reactions:
            if reaction.is_isomorphic(entry.item):
                break
        else:
            trained_reactions.append(entry.item)

    # Load untrained reactions
    untrained_reactions = []
    for depository in family.depositories:
        if 'training' not in depository.label:
            for entry in depository.entries.values():
                for reaction in trained_reactions:
                    if reaction.is_isomorphic(entry.item):
                        break
                else:
                    for reaction in untrained_reactions:
                        if reaction.is_isomorphic(entry.item):
                            break
                    else:
                        untrained_reactions.append(entry.item)

    # Sort reactions by reactant size
    untrained_reactions.sort(key=lambda reaction: sum([1 for r in reaction.reactants for a in r.molecule[0].atoms if a.is_non_hydrogen()]))

    # Build entries
    untrained = KineticsDepository(name='{0}/untrained'.format(family.label),
                                   label='{0}/untrained'.format(family.label))
    count = 1
    for reaction in untrained_reactions:
        untrained.entries['{0}'.format(count)] = Entry(
            item=reaction,
            index=count,
            label=getReactionUrl(reaction),
        )
        count += 1

    return untrained

###############################################################################


def queryNIST(entry, squib, entries, user):
    """
    Pulls NIST kinetics and reference information, given
    a unique entry squib (e.g. `1999SMI/GOL57-101:3`).
    """

    url = 'http://kinetics.nist.gov/kinetics/Detail?id={0}'.format(squib)
    cookiejar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))

    # Set units
    post = {'energyUnits': 'J',
            'evaluationTemperature': '300.0',
            'moleculeUnits': 'Mole',
            'pressureUnits': 'Pa',
            'referenceTemperature': '1.0',
            'temperatureUnits': 'K',
            'volumeUnits': 'cm',
            }
    request = opener.open('http://kinetics.nist.gov/kinetics/'
                          'SetUnitsBean.jsp', data=urllib.parse.urlencode(post))
    request.close()

    # Grab kinetics for a NIST entry from the full bibliographic page.
    full_url = ('http://kinetics.nist.gov/kinetics/'
                'Detail?id={0}:0'.format(squib.split(':')[0]))
    request = opener.open(full_url)
    soup = BeautifulSoup(request.read())
    request.close()

    # Find table on page corresponding to kinetics entries
    try:
        form = soup.findAll(name='form',
                             attrs={'name': 'KineticsResults'})[0]
    except:
        return 'No results found for {0}.'.format(squib)

    # Find row in table corresponding to squib
    for tr in form.findAll(name='tr'):
        tdlist = tr.findAll(name='td')
        if len(tdlist) == 17 and tr.findAll(name='input', value=squib):
            break
    else:
        return 'No results found for {0}.'.format(squib)

    # Assert entry is not a reference reaction
    try:
        if 'Reference reaction' in tr.findNext(name='tr').text:
            return 'Entry is a reference reaction.'
    except:
        pass

    # Check reaction order
    try:
        order = int(tdlist[16].text)
        if order != len(entry.item.reactants):
            return 'Reaction order does not match number of reactants.'
    except:
        return 'Invalid reaction order.'

    # Grab pre-exponential
    A = tdlist[8].text
    if '&nbsp;' in A:
        return 'Invalid pre-exponential.'
    if ';' in A:
        A = A.split(';')[1]
    if order == 1:
        entry.data.A = Quantity(float(A), 's^-1')
    elif order == 2:
        entry.data.A = Quantity(float(A) / 1.0e6, 'm^3/(mol*s)')
    else:
        return 'Unexpected reaction order encountered.'

    # Grab temperature exponent
    n = tdlist[10].text
    if n == '&nbsp;':
        n = 0.0
    entry.data.n = Quantity(float(n), '')

    # Grab activation energy
    Ea = tdlist[12].text
    if '&nbsp;' in Ea:
        Ea = 0.0
    elif ';' in Ea:
        Ea = Ea.split(';')[1]
    entry.data.Ea = Quantity(float(Ea) / 1.0e3, 'kJ/mol')

    # Grab reference and miscellaneous data from NIST entry page.
    request = opener.open(url)
    html = request.read().replace('<p>', '<BR><BR>').replace('<P>',
                                                             '<BR><BR>')
    soup = BeautifulSoup(html)
    request.close()

    # Grab reference
    try:
        type = soup.findAll('b', text='Reference type:')[0].parent
        type = type.nextSibling[13:].lower()
        if type == 'technical report' or type == 'journal article':
            type = 'journal'
        if type == 'book chapter':
            type = 'book'
    except:
        type = None
    if type not in ['journal', 'book']:
        entry.reference = None
    else:
        if type == 'journal':
            entry.reference = Article(authors=[])

            # Grab journal title
            try:
                journal = soup.findAll('b', text='Journal:')[0].parent
                entry.reference.journal = journal.nextSibling[13:]
            except:
                pass

            # Grab volume number
            try:
                volume = soup.findAll('b', text='Volume:')[0].parent
                entry.reference.volume = volume.nextSibling[13:]
            except:
                pass

            # Grab pages
            try:
                pages = soup.findAll('b', text='Page(s):')[0].parent
                pages = pages.nextSibling[13:]
                if not pages:
                    pages = re.match(r'\d+[^\d]+([^:]+)', squib).group(1)
            except:
                pass
            entry.reference.pages = pages.replace(' - ', '-')

        elif type == 'book':
            entry.reference = Book(authors=[])

            # Grab publisher
            try:
                pub = soup.findAll(text='Publisher address:')[0].parent
                entry.reference.publisher = pub.nextSibling[13:]
            except:
                pass

        # Grab authors
        try:
            authors = soup.findAll('b', text='Author(s):')[0].parent
            authors = authors.nextSibling[13:]
            for author in authors.split(';'):
                entry.reference.authors.append(author.strip())
        except:
            pass

        # Grab title
        try:
            title = soup.findAll('b', text='Title:')[0].parent.nextSibling
            entry.reference.title = title[13:]
            while True:
                title = title.nextSibling
                try:
                    if title.name == 'br':
                        break
                except:
                    pass
                try:
                    entry.reference.title += title.text
                except AttributeError:
                    entry.reference.title += title
        except:
            pass

        # Grab year
        try:
            year = soup.findAll('b', text='Year:')[0].parent
            entry.reference.year = year.nextSibling[13:]
        except:
            entry.reference.year = squib[0:4]

        # Set URL
        entry.reference.url = url

    # Grab reference type
    try:
        reftype = soup.findAll('b', text='Category:')[0].parent
        entry.reference_type = reftype.nextSibling[7:].lower()
    except:
        entry.reference_type = ''

    # Grab short description
    try:
        short = soup.findAll('b', text='Data type:')[0].parent
        entry.short_desc = short.nextSibling[13:].replace('  ', ' ')
    except:
        entry.short_desc = ''

    # Grab temperature range
    try:
        Trange = soup.findAll('b', text='Temperature:')[0]
        Trange = Trange.parent.nextSibling[13:].split()
        entry.data.Tmin = Quantity(int(Trange[0]), 'K')
        if '-' in Trange[1]:
            entry.data.Tmax = Quantity(int(Trange[2]), 'K')
    except:
        entry.data.Tmin = None
        entry.data.Tmax = None

    # Grab pressure range
    try:
        Prange = soup.findAll('b', text='Pressure:')[0]
        Prange = Prange.parent.nextSibling[12:].split()
        entry.data.Pmin = Quantity(float(Prange[0]), 'Pa')
        if '-' in Prange[1]:
            entry.data.Pmax = Quantity(float(Prange[2]), 'Pa')
    except:
        entry.data.Pmin = None
        entry.data.Pmax = None

    # Start long description with reference reaction where applicable
    long_desc = ''
    try:
        ref = soup.findAll('b', text='Reference reaction:')[0].parent
        long_desc += '\nReference Reaction: '
        ref = ref.nextSibling.nextSibling
        while True:
            try:
                long_desc += ref.text
            except:
                long_desc += ref
            ref = ref.nextSibling
            try:
                if ref.name == 'br':
                    break
            except:
                pass
    except:
        pass

    # Grab rest of long description
    try:
        rate = soup.findAll('b', text='Rate expression:')[0].parent
        long_desc1 = rate.nextSibling
        while True:
            try:
                if long_desc1.name == 'br':
                    break
            except:
                pass
            long_desc1 = long_desc1.nextSibling
        while True:
            try:
                if ((long_desc1.nextSibling.name == 'a'
                     and long_desc1.nextSibling.text == 'View') or long_desc1.nextSibling is None):
                    break
            except:
                pass
            try:
                if long_desc1.name == 'br':
                    long_desc += '\n'
                else:
                    long_desc += long_desc1.text
            except:
                long_desc += long_desc1.replace('\n', '')
            long_desc1 = long_desc1.nextSibling
        for line in long_desc.splitlines():
            if 'Data type:' not in line and 'Category:' not in line:
                entry.long_desc += line + '\n'
        swaps = [('&nbsp;&nbsp;\n', ' '),
                 ('&nbsp;', ' '),
                 ('  ', ' '),
                 ('Comments: ', '\n'),
                 ('\n ', '\n'),
                 ('&middot;', u'·')]
        for swap in swaps:
            entry.long_desc = entry.long_desc.replace(swap[0], swap[1])
        entry.long_desc = entry.long_desc.strip()
    except:
        pass

    # Grab uncertainty for pre-exponential
    try:
        error = rate.nextSibling
        text = ''
        while '[' not in text:
            error = error.nextSibling
            try:
                text = error.text
            except:
                text = error
        if '&plusmn;' in text:
            text = text.split('&plusmn;')[1].split(' ')[0]
            entry.data.A.uncertainty_type = '+|-'
            if text.isdigit():
                entry.data.A.uncertainty = float(text)
            elif 'x' in text:
                entry.data.A.uncertainty = float(text.split('x')[0] + 'e'
                                                 + error.nextSibling.text)
            if len(entry.item.reactants) == 2:
                entry.data.A.uncertainty /= 1.0e6
    except:
        pass
    for line in entry.long_desc.splitlines():
        if 'Uncertainty:' in line and entry.data.A.uncertainty == 0.0:
            entry.data.A.uncertainty = float(line.split(' ')[1])
            entry.data.A.uncertainty_type = '*|/'
    if entry.data.A.uncertainty_type == '+|-':
        if abs(entry.data.A.uncertainty) > abs(entry.data.A.value_si):
            u = entry.data.A.uncertainty
            entry.long_desc += ('\nNote: Invalid A value uncertainty '
                               '({0} {1})'.format(u, entry.data.A.units)
                               + ' found and ignored')
            entry.data.A.uncertainty = 0.0

    # Grab uncertainty for temperature exponent
    for sup in soup.findAll('sup'):
        if '(' in sup.text and ')' in sup.text and '&plusmn;' in sup.text:
            try:
                error = sup.text.split('&plusmn;')[1].split(')')[0]
                entry.data.n.uncertainty = float(error)
                entry.data.n.uncertainty_type = '+|-'
            except:
                pass
            break
    if entry.data.n.uncertainty_type == '+|-':
        if abs(entry.data.n.uncertainty) > abs(entry.data.n.value_si):
            u = entry.data.n.uncertainty
            entry.long_desc += ('\nNote: Invalid n value uncertainty '
                               '({0}) found and ignored'.format(u))
            entry.data.n.uncertainty = 0.0

    # Grab uncertainty and better value for activation energy
    for sup in soup.findAll('sup'):
        if 'J/mole]/RT' in sup.text:
            entry.data.Ea.value_si = -float(sup.text.split(' ')[0])
            try:
                error = sup.text.split('&plusmn;')[1]
                entry.data.Ea.uncertainty = float(error.split(' ')[0])
                entry.data.Ea.uncertainty_type = '+|-'
            except:
                pass
            break
    if entry.data.Ea.uncertainty_type == '+|-':
        if abs(entry.data.Ea.uncertainty) > abs(entry.data.Ea.value_si):
            u = entry.data.Ea.uncertainty
            entry.long_desc += ('\nNote: Invalid Ea value uncertainty '
                               '({0} J/mol) found and ignored'.format(u))
            entry.data.Ea.uncertainty = 0.0

    return entry


###############################################################################


def kinetics(request, section='', subsection=''):
    """
    The RMG database homepage.
    """
    # Make sure section has an allowed value
    if section not in ['libraries', 'families', '']:
        raise Http404

    # Load the kinetics database, if necessary
    database.load('kinetics', section)

    # Determine which subsection we wish to view
    db = None
    try:
        db = database.get_kinetics_database(section, subsection)
    except ValueError:
        pass

    if db is not None:

        # A subsection was specified, so render a table of the entries in
        # that part of the database

        is_group_database = False

        # Sort entries by index
        if db.top is not None and len(db.top) > 0:
            # If there is a tree in this database, only consider the entries
            # that are in the tree
            entries0 = getDatabaseTreeAsList(db, db.top)
            tree = '<ul class="kineticsTree">\n{0}\n</ul>\n'.format(getKineticsTreeHTML(db, section, subsection, db.top))
        else:
            # If there is not a tree, consider all entries
            entries0 = list(db.entries.values())
            if any(isinstance(item, list) for item in entries0):
                # if the entries are lists
                entries0 = reduce(lambda x, y: x+y, entries0)
            # Sort the entries by index and label
            entries0.sort(key=lambda entry: (entry.index, entry.label))
            tree = ''

        entries = []

        for entry0 in entries0:
            if isinstance(entry0.data, str):
                data_format = 'Link'
            else:
                data_format = entry0.data.__class__.__name__

            entry = {
                'index': entry0.index,
                'label': entry0.label,
                'dataFormat': data_format,
            }
            if isinstance(db, KineticsGroups):
                is_group_database = True
                entry['structure'] = getStructureInfo(entry0.item)
                entry['parent'] = entry0.parent
                entry['children'] = entry0.children
            elif 'rules' in subsection:
                if isinstance(entry0.item, list):
                    # if the reactants are not group objects, then this rate rule came from
                    # the averaging step, and we don't want to show all of the averaged nodes
                    # in the web view.  We only want to show nodes with direct values or
                    # training rates that became rate rules.
                    continue
                else:
                    entry['reactants'] = ' + '.join([getStructureInfo(reactant) for reactant in entry0.item.reactants])
                    entry['products'] = ' + '.join([getStructureInfo(reactant) for reactant in entry0.item.products])
                    entry['arrow'] = '&hArr;' if entry0.item.reversible else '&rarr;'
            else:
                entry['reactants'] = ' + '.join([getStructureInfo(reactant) for reactant in entry0.item.reactants])
                entry['products'] = ' + '.join([getStructureInfo(reactant) for reactant in entry0.item.products])
                entry['arrow'] = '&hArr;' if entry0.item.reversible else '&rarr;'

            entries.append(entry)

        return render(request, 'kineticsTable.html', {'section': section, 'subsection': subsection, 'databaseName': db.name, 'databaseDesc': db.long_desc, 'entries': entries, 'tree': tree, 'isGroupDatabase': is_group_database})

    else:
        # No subsection was specified, so render an outline of the kinetics
        # database components
        kinetics_libraries = [(label, library) for label, library in database.kinetics.libraries.items() if subsection in label]
        kinetics_libraries.sort()
        
        # If this is a subsection, but not the main kinetics page,
        # we don't need to iterate through the entire database, as this takes a long time to load.
        try:
            families_to_process = [database.kinetics.families[subsection]]
        except KeyError: # if main kinetics page, or some other error
            families_to_process = database.kinetics.families.values()

        for family in families_to_process:
            for i in range(0, len(family.depositories)):
                if 'untrained' in family.depositories[i].name:
                    family.depositories.pop(i)
            family.depositories.append(getUntrainedReactions(family))
        kinetics_families = [(label, family) for label, family in database.kinetics.families.items() if subsection in label]
        kinetics_families.sort()
        return render(request, 'kinetics.html', {'section': section, 'subsection': subsection, 'kineticsLibraries': kinetics_libraries, 'kineticsFamilies': kinetics_families})


def kineticsUntrained(request, family):
    database.load('kinetics', 'families')
    entries0 = list(getUntrainedReactions(database.kinetics.families[family]).entries.values())
    entries0.sort(key=lambda entry: (entry.index, entry.label))

    entries = []
    for entry0 in entries0:
        entry = {
                'index': entry0.index,
                'url': entry0.label,
            }

        entry['reactants'] = ' + '.join([getStructureInfo(reactant) for reactant in entry0.item.reactants])
        entry['products'] = ' + '.join([getStructureInfo(reactant) for reactant in entry0.item.products])
        entry['arrow'] = '&hArr;' if entry0.item.reversible else '&rarr;'

        entries.append(entry)
    return render(request, 'kineticsTable.html', {'section': 'families', 'subsection': family, 'databaseName': '{0}/untrained'.format(family), 'entries': entries, 'tree': None, 'isGroupDatabase': False})


def getReactionUrl(reaction, family=None, estimator=None, resonance=True):
    """
    Get the URL (for kinetics data) of a reaction.

    Returns '' if the reaction contains functional Groups or LogicNodes instead
    of real Species or Molecules.
    """
    kwargs = dict()
    for index, reactant in enumerate(reaction.reactants):
        if isinstance(reactant, Entry):
            reactant = reactant.item
        if isinstance(reactant, Group) or isinstance(reactant, LogicNode):
            return ''
        mol = reactant if isinstance(reactant, Molecule) else reactant.molecule[0]
        kwargs['reactant{0:d}'.format(index+1)] = moleculeToAdjlist(mol)
    for index, product in enumerate(reaction.products):
        mol = product if isinstance(product, Molecule) else product.molecule[0]
        kwargs['product{0:d}'.format(index+1)] = moleculeToAdjlist(mol)

    kwargs['resonance'] = resonance

    if family:
        if estimator:
            kwargs['family'] = family
            kwargs['estimator'] = estimator.replace(' ', '_')
            reaction_url = reverse('database:kinetics-group', kwargs=kwargs)
        else:
            reaction_url = ''
    else:
        reaction_url = reverse('database:kinetics-data', kwargs=kwargs)
    return reaction_url


@login_required
def kineticsEntryNew(request, family, type):
    """
    A view for creating a new entry in a kinetics family depository.
    """
    from rmgweb.database.forms import KineticsEntryEditForm
    # Load the kinetics database, if necessary
    database.load('kinetics', 'families')

    subsection = '{0}/{1}'.format(family, type)
    try:
        db = database.get_kinetics_database('families', subsection)
    except ValueError:
        raise Http404

    entries = list(db.entries.values())
    if any(isinstance(item, list) for item in entries):
        # if the entries are lists
        entries = reduce(lambda x, y: x+y, entries)
    entry = None
    if request.method == 'POST':
        form = KineticsEntryEditForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            new_entry = form.cleaned_data['entry']

            # Set new entry index
            indices = [entry.index for entry in db.entries.values()]
            new_entry.index = max(indices or [0]) + 1

            # Confirm entry does not already exist in depository
            for entry in entries:
                if ((type == 'training' and new_entry.item.is_isomorphic(entry.item))
                   or (type == 'NIST' and new_entry.label == entry.label)):
                    kwargs = {'section': 'families',
                              'subsection': subsection,
                              'index': entry.index,
                              }
                    forward_url = reverse('database:kinetics-entry', kwargs=kwargs)
                    if type == 'training':
                        message = """
                        This reaction is already in the {0} training set.<br>
                        View or edit it at <a href="{1}">{1}</a>.
                        """.format(family, forward_url)
                        title = '- Reaction already in {0}.'.format(subsection)
                    else:
                        message = """
                        This entry is already in {0}.<br>
                        View or edit it at <a href="{1}">{1}</a>.
                        """.format(subsection, forward_url)
                        title = '- Entry already in {0}.'.format(subsection)
                    return render(request, 'simple.html',
                                  {'title': title, 'body': message})

            if type == 'NIST':
                squib = new_entry.label
                new_entry.data = Arrhenius()
                new_entry = queryNIST(new_entry, new_entry.label, entries, request.user)
                if not isinstance(new_entry, Entry):
                    url = 'http://nist.kinetics.gov/kinetics/Detail?id={0}'.format(squib)
                    message = 'Error in grabbing kinetics from <a href="{0}">NIST</a>.<br>{1}'.format(url, new_entry)
                    return render(request, 'simple.html',
                                  {'title': 'Error in grabbing kinetics for {0}.'.format(squib),
                                   'body': message,
                                   })
                msg = 'Imported from NIST database at {0}'.format(new_entry.reference.url)
            else:
                msg = form.cleaned_data['change']

            # Format the new entry as a string
            entry_buffer = io.StringIO(u'')
            try:
                rmgpy.data.kinetics.save_entry(entry_buffer, new_entry)
            except Exception as e:
                entry_buffer.write("ENTRY WAS NOT PARSED CORRECTLY.\n")
                entry_buffer.write(str(e))
                pass
            entry_string = entry_buffer.getvalue()
            entry_buffer.close()

            # Build the redirect URL
            kwargs = {'section': 'families',
                      'subsection': subsection,
                      'index': new_entry.index,
                      }
            forward_url = reverse('database:kinetics-entry', kwargs=kwargs)

            if False:
                # Just return the text.
                return HttpResponse(entry_string, content_type="text/plain")
            if True:
                # save it
                db.entries[index] = new_entry
                path = os.path.join(rmgweb.settings.DATABASE_PATH, 'kinetics', 'families', family, '{0}.py'.format(type))
                db.save(path)
                commit_author = '{0.first_name} {0.last_name} <{0.email}>'.format(request.user)
                commit_message = 'New Entry: {family}/{type}/{index}\n\n{msg}'.format(family=family,
                                                                                      type=type,
                                                                                      index=new_entry.index,
                                                                                      msg=msg)
                commit_message += '\n\nSubmitted through the RMG website.'
                commit_result = subprocess.check_output(['git', 'commit', '-m', commit_message,
                                                         '--author', commit_author, path],
                                                         cwd=rmgweb.settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                subprocess.check_output(['git', 'push'], cwd=rmgweb.settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                message = """
                New entry saved succesfully:<br>
                <pre>{0}</pre><br>
                See result at <a href="{1}">{1}</a>.
                """.format(commit_result, forward_url)
                return render(request, 'simple.html',
                              {'title': '', 'body': message})
    else:  # not POST
        form = KineticsEntryEditForm()

    return render(request, 'kineticsEntryEdit.html',
                  {'section': 'families',
                   'subsection': subsection,
                   'databaseName': family,
                   'entry': entry,
                   'form': form,
                   })


@login_required
def kineticsEntryEdit(request, section, subsection, index):
    """
    A view for editing an entry in a kinetics database.
    """
    from rmgweb.database.forms import KineticsEntryEditForm
    # Load the kinetics database, if necessary
    database.load('kinetics', section)

    # Determine the entry we wish to view
    try:
        db = database.get_kinetics_database(section, subsection)
    except ValueError:
        raise Http404

    entries = list(db.entries.values())
    if any(isinstance(item, list) for item in entries):
        # if the entries are lists
        entries = reduce(lambda x, y: x+y, entries)
    index = int(index)
    for entry in entries:
        if entry.index == index:
            break
    else:
        raise Http404

    if request.method == 'POST':
        form = KineticsEntryEditForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            new_entry = form.cleaned_data['entry']
            new_entry.index = index

            # Get the entry as a entry_string
            entry_buffer = io.StringIO(u'')
            try:
                rmgpy.data.kinetics.save_entry(entry_buffer, new_entry)
            except Exception as e:
                entry_buffer.write("ENTRY WAS NOT PARSED CORRECTLY.\n")
                entry_buffer.write(str(e))
                pass
            entry_string = entry_buffer.getvalue()
            entry_buffer.close()

            if False:
                # Just return the text.
                return HttpResponse(entry_string, content_type="text/plain")
            if False:
                # Render it as if it were saved.
                return render(request, 'kineticsEntry.html',
                              {'section': section,
                               'subsection': subsection,
                               'databaseName': db.name,
                               'entry': new_entry,
                               'reference': entry.reference,
                               'kinetics': entry.data,
                               })
            if True:
                # save it
                db.entries[index] = new_entry
                path = os.path.join(rmgweb.settings.DATABASE_PATH, 'kinetics', section, subsection + '.py')
                db.save(path)
                commit_author = "{0.first_name} {0.last_name} <{0.email}>".format(request.user)
                commit_message = "{1}:{2} {3}\n\nChange to kinetics/{0}/{1} entry {2} submitted through RMG website:\n{3}\n{4}".format(section, subsection, index, form.cleaned_data['change'], commit_author)
                commit_result = subprocess.check_output(['git', 'commit', '-m', commit_message, '--author',
                                                         commit_author, path],
                                                         cwd=rmgweb.settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                subprocess.check_output(['git', 'push'], cwd=rmgweb.settings.DATABASE_PATH, stderr=subprocess.STDOUT)

                # return HttpResponse(commit_result, content_type="text/plain")

                kwargs = {'section': section,
                          'subsection': subsection,
                          'index': index}
                forward_url = reverse('database:kinetics-entry', kwargs=kwargs)
                message = """
                Changes saved succesfully:<br>
                <pre>{0}</pre><br>
                See result at <a href="{1}">{1}</a>.
                """.format(commit_result, forward_url)
                return render(request, 'simple.html',
                              {'title': 'Change saved successfully.',
                               'body': message,
                               })

            # redirect
            return HttpResponseRedirect(forward_url)

    else:  # not POST
        # Get the entry as a entry_string
        entry_buffer = io.StringIO(u'')
        try:
            rmgpy.data.kinetics.save_entry(entry_buffer, entry)
        except Exception as e:
            entry_buffer.write("ENTRY WAS NOT PARSED CORRECTLY.\n")
            entry_buffer.write(str(e))
            pass
        entry_string = entry_buffer.getvalue()
        entry_buffer.close()

        # entry_string = entry.item.reactants[0].to_adjacency_list()
        # remove leading 'entry('
        entry_string = re.sub('^entry\(\n', '', entry_string)
        # remove the 'index = 23,' line
        entry_string = re.sub('\s*index = \d+,\n', '', entry_string)

        form = KineticsEntryEditForm(initial={'entry': entry_string})

    return render(request, 'kineticsEntryEdit.html',
                  {'section': section,
                   'subsection': subsection,
                   'databaseName': db.name,
                   'entry': entry,
                   'form': form,
                   })


@login_required
def thermoEntryNew(request, section, subsection, adjlist):
    """
    A view for creating a new thermodynamics entry into any database section.
    """
    from rmgweb.database.forms import ThermoEntryEditForm
    # Load the thermo database, if necessary
    database.load('thermo')

    adjlist = urllib.parse.unquote(adjlist)
    molecule = Molecule().from_adjacency_list(adjlist)

    try:
        db = database.get_thermo_database(section, subsection)
    except ValueError:
        raise Http404

    entries = list(db.entries.values())
    if any(isinstance(item, list) for item in entries):
        # if the entries are lists
        entries = reduce(lambda x, y: x + y, entries)
    entry = None
    if request.method == 'POST':
        form = ThermoEntryEditForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            new_entry = form.cleaned_data['entry']

            # Set new entry index
            indices = [entry.index for entry in db.entries.values()]
            new_entry.index = max(indices or [0]) + 1

            # Do not need to confirm entry already exists- should allow the user to store multiple
            # thermo entries in to the depository or into separate libraries for the same molecule if the data exists.

            msg = form.cleaned_data['change']

            # Format the new entry as a string
            entry_buffer = io.StringIO(u'')
            try:
                rmgpy.data.thermo.save_entry(entry_buffer, new_entry)
            except Exception as e:
                entry_buffer.write("ENTRY WAS NOT PARSED CORRECTLY.\n")
                entry_buffer.write(str(e))
                pass
            entry_string = entry_buffer.getvalue()
            entry_buffer.close()

            # Build the redirect URL
            kwargs = {'section': section,
                      'subsection': subsection,
                      'index': new_entry.index,
                      }
            forward_url = reverse('database:thermo-entry', kwargs=kwargs)

            if False:
                # Just return the text.
                return HttpResponse(entry_string, content_type="text/plain")
            if True:
                # save it
                db.entries[index] = new_entry
                path = os.path.join(rmgweb.settings.DATABASE_PATH, 'thermo', section, subsection + '.py')
                db.save(path)
                commit_author = '{0.first_name} {0.last_name} <{0.email}>'.format(request.user)
                commit_message = 'New Entry: {section}/{subsection}/{index}\n\n{msg}'.format(section=section,
                                                                                             subsection=subsection,
                                                                                             index=new_entry.index,
                                                                                             msg=msg)
                commit_message += '\n\nSubmitted through the RMG website.'
                commit_result = subprocess.check_output(['git', 'commit', '-m', commit_message,
                                                         '--author', commit_author, path],
                                                         cwd=rmgweb.settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                subprocess.check_output(['git', 'push'], cwd=rmgweb.settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                message = """
                New entry saved succesfully:<br>
                <pre>{0}</pre><br>
                See result at <a href="{1}">{1}</a>.
                """.format(commit_result, forward_url)
                return render(request, 'simple.html',
                              {'title': '', 'body': message})
    else:  # not POST
        entry_string = """
label = "{label}",
molecule = "\"\"
{adjlist}
"\"\",\n
thermo = ThermoData(
    Tdata = ([],'K'),
    Cpdata = ([],'cal/(mol*K)'),
    H298 = (,'kcal/mol'),
    S298 = (,'cal/(mol*K)'),
),\n
short_desc = u"\"\" "\"\",
long_desc =
    u"\"\"

    "\"\",
        """.format(label=molecule.to_smiles(), adjlist=molecule.to_adjacency_list())

        form = ThermoEntryEditForm(initial={'entry': entry_string})

    return render(request, 'thermoEntryEdit.html',
                  {'section': section,
                   'subsection': subsection,
                   'databaseName': db.name,
                   'entry': entry,
                   'form': form,
                   })


@login_required
def thermoEntryEdit(request, section, subsection, index):
    """
    A view for editing an entry in a thermo database.
    """
    from rmgweb.database.forms import ThermoEntryEditForm
    # Load the kinetics database, if necessary
    database.load('thermo', section)

    # Determine the entry we wish to view
    try:
        db = database.get_thermo_database(section, subsection)
    except ValueError:
        raise Http404

    entries = list(db.entries.values())
    if any(isinstance(item, list) for item in entries):
        # if the entries are lists
        entries = reduce(lambda x, y: x + y, entries)
    index = int(index)
    for entry in entries:
        if entry.index == index:
            break
    else:
        raise Http404

    if request.method == 'POST':
        form = ThermoEntryEditForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            new_entry = form.cleaned_data['entry']
            new_entry.index = index

            # Get the entry as a entry_string
            entry_buffer = io.StringIO(u'')
            try:
                rmgpy.data.thermo.save_entry(entry_buffer, new_entry)
            except Exception as e:
                entry_buffer.write("ENTRY WAS NOT PARSED CORRECTLY.\n")
                entry_buffer.write(str(e))
                pass
            entry_string = entry_buffer.getvalue()
            entry_buffer.close()

            if False:
                # Just return the text.
                return HttpResponse(entry_string, content_type="text/plain")
            if False:
                # Render it as if it were saved.
                return render(request, 'thermoEntry.html',
                              {'section': section,
                               'subsection': subsection,
                               'databaseName': db.name,
                               'entry': new_entry,
                               'reference': entry.reference,
                               'kinetics': entry.data,
                               })
            if True:
                # save it
                db.entries[index] = new_entry
                path = os.path.join(rmgweb.settings.DATABASE_PATH, 'thermo', section, subsection + '.py')
                db.save(path)
                commit_author = "{0.first_name} {0.last_name} <{0.email}>".format(request.user)
                commit_message = "{1}:{2} {3}\n\nChange to thermo/{0}/{1} entry {2} submitted through RMG website:\n{3}\n{4}".format(section, subsection, index, form.cleaned_data['change'], commit_author)
                commit_result = subprocess.check_output(['git', 'commit', '-m', commit_message,
                                                         '--author', commit_author, path],
                                                         cwd=rmgweb.settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                subprocess.check_output(['git', 'push'], cwd=rmgweb.settings.DATABASE_PATH, stderr=subprocess.STDOUT)

                # return HttpResponse(commit_result, content_type="text/plain")

                kwargs = {'section': section,
                          'subsection': subsection,
                          'index': index}
                forward_url = reverse('database:thermo-entry', kwargs=kwargs)
                message = """
                Changes saved succesfully:<br>
                <pre>{0}</pre><br>
                See result at <a href="{1}">{1}</a>.
                """.format(commit_result, forward_url)
                return render(request, 'simple.html',
                              {'title': 'Change saved successfully.',
                               'body': message,
                               })

            # redirect
            return HttpResponseRedirect(forward_url)

    else:  # not POST
        # Get the entry as a entry_string
        entry_buffer = io.StringIO(u'')
        try:
            rmgpy.data.thermo.save_entry(entry_buffer, entry)
        except Exception as e:
            entry_buffer.write("ENTRY WAS NOT PARSED CORRECTLY.\n")
            entry_buffer.write(str(e))
            pass
        entry_string = entry_buffer.getvalue()
        entry_buffer.close()

        # entry_string = entry.item.reactants[0].to_adjacency_list()
        # remove leading 'entry('
        entry_string = re.sub('^entry\(\n', '', entry_string)
        # remove the 'index = 23,' line
        entry_string = re.sub('\s*index = \d+,\n', '', entry_string)

        form = ThermoEntryEditForm(initial={'entry': entry_string})

    return render(request, 'thermoEntryEdit.html',
                  {'section': section,
                   'subsection': subsection,
                   'databaseName': db.name,
                   'entry': entry,
                   'form': form,
                   })


def kineticsEntry(request, section, subsection, index):
    """
    A view for showing an entry in a kinetics database.
    """

    # Load the kinetics database, if necessary
    database.load('kinetics', section)

    # Determine the entry we wish to view
    try:
        db = database.get_kinetics_database(section, subsection)
    except ValueError:
        raise Http404

    entries = list(db.entries.values())
    if any(isinstance(item, list) for item in entries):
        # if the entries are lists
        entries = reduce(lambda x, y: x + y, entries)

    index = int(index)
    if index != 0 and index != -1:
        for entry in entries:
            if entry.index == index:
                break
        else:
            raise Http404
    else:
        if index == 0:
            index = min(entry.index for entry in entries if entry.index > 0)
        else:
            index = max(entry.index for entry in entries if entry.index > 0)
        return HttpResponseRedirect(reverse('database:kinetics-entry',
                                            kwargs={'section': section,
                                                    'subsection': subsection,
                                                    'index': index,
                                                    }))

    reference = entry.reference
    reference_type = ''

    reactant_num = 0
    degeneracy = 1
    if isinstance(db, KineticsGroups):
        reactant_num = db.reactant_num
    else:
        reactant_num = len(entry.item.reactants)
        degeneracy = entry.item.degeneracy

    if isinstance(db, KineticsGroups):
        structure = getStructureInfo(entry.item)
        return render(request, 'kineticsEntry.html',
                      {'section': section,
                       'subsection': subsection,
                       'databaseName': db.name,
                       'entry': entry,
                       'structure': structure,
                       'reference': reference,
                       'referenceType': reference_type,
                       })
    else:
        reactants = ' + '.join([getStructureInfo(reactant) for reactant in entry.item.reactants])
        products = ' + '.join([getStructureInfo(reactant) for reactant in entry.item.products])
        arrow = '&hArr;' if entry.item.reversible else '&rarr;'

        # Searching for other instances of the reaction only valid for real reactions, not groups
        # If a Group or LogicNode shows up in the reaction, getReactionUrl will return ''
        reaction_url = getReactionUrl(entry.item)

        return render(request, 'kineticsEntry.html',
                      {'section': section,
                       'subsection': subsection,
                       'databaseName': db.name,
                       'entry': entry,
                       'reactants': reactants,
                       'arrow': arrow,
                       'products': products,
                       'reference': reference,
                       'referenceType': reference_type,
                       'reactionUrl': reaction_url,
                       })


def kineticsGroupEstimateEntry(request, family, estimator, reactant1, product1, reactant2='', reactant3='', product2='', product3='', resonance=True):
    """
    View a kinetics group estimate as an entry.
    """
    # Load the kinetics database if necessary
    database.load('kinetics', 'families')
    # Also load the thermo database so we can generate reverse kinetics if necessary
    database.load('thermo')

    # we need 'database' to reference the top level object that we pass to generateReactions
    # check the family exists
    try:
        database.get_kinetics_database('families', family+'/groups')
    except ValueError:
        raise Http404

    reactant_list = []
    reactant_list.append(moleculeFromURL(reactant1))
    if reactant2 != '':
        reactant_list.append(moleculeFromURL(reactant2))
    if reactant3 != '':
        reactant_list.append(moleculeFromURL(reactant3))

    product_list = []
    product_list.append(moleculeFromURL(product1))
    if product2 != '':
        product_list.append(moleculeFromURL(product2))
    if product3 != '':
        product_list.append(moleculeFromURL(product3))

    # Search for the corresponding reaction(s)
    reaction_list = generateReactions(database, reactant_list, product_list, only_families=[family], resonance=resonance)

    kinetics_data_list = []

    # Only keep template reactions frm the selected estimation method in the forward direction
    reaction_list = [reaction for reaction in reaction_list if (isinstance(reaction, TemplateReaction)
                                                                and reaction.estimator == estimator.replace('_', ' ')
                                                                and reactionHasReactants(reaction, reactant_list))]

    # Select the first reaction for initial processing
    reaction0 = reaction_list[0]

    # Generate the thermo data for the species involved
    for reactant in reaction0.reactants:
        generateSpeciesThermo(reactant, database)
    for product in reaction0.products:
        generateSpeciesThermo(product, database)

    reactants = ' + '.join([getStructureInfo(reactant) for reactant in reaction0.reactants])
    arrow = '&hArr;' if reaction0.reversible else '&rarr;'
    products = ' + '.join([getStructureInfo(reactant) for reactant in reaction0.products])

    source = '%s (RMG-Py %s)' % (reaction0.family, reaction0.estimator)

    entry = None
    entry_list = []
    if len(reaction_list) == 1:
        if isinstance(reaction0.kinetics, (ArrheniusEP, ArrheniusBM)):
            reaction0.kinetics = reaction0.kinetics.to_arrhenius(reaction0.get_enthalpy_of_reaction(298))

        entry = Entry(
            data=reaction0.kinetics,
            short_desc="Estimated by RMG-Py %s" % (reaction0.estimator),
            long_desc=reaction0.kinetics.comment,
        )

        if estimator == 'group_additivity':
            reference = rmgpy.data.reference.Reference(
                url=request.build_absolute_uri(
                    reverse('database:kinetics', kwargs={'section': 'families', 'subsection': family + '/groups'})),
            )
        else:
            reference = rmgpy.data.reference.Reference(
                url=request.build_absolute_uri(
                    reverse('database:kinetics', kwargs={'section': 'families', 'subsection': family + '/rules'})),
            )
        reference_type = ''
    else:
        for i, reaction in enumerate(reaction_list):
            assert reaction.is_isomorphic(reaction0, either_direction=False), "Multiple group estimates must be isomorphic."
            # Replace reactants and products with the same object instances as reaction0
            reaction.reactants = reaction0.reactants
            reaction.products = reaction0.products

            # If the kinetics are ArrheniusEP and ArrheniusBM, replace them with Arrhenius
            if isinstance(reaction.kinetics, (ArrheniusEP, ArrheniusBM)):
                reaction.kinetics = reaction.kinetics.to_arrhenius(reaction.get_enthalpy_of_reaction(298))

            entry0 = Entry(
                data=reaction.kinetics,
                short_desc="Estimated by RMG-Py %s" % (reaction.estimator),
                long_desc=reaction.kinetics.comment,
            )
            entry0.result = i + 1

            if estimator == 'group_additivity':
                reference = rmgpy.data.reference.Reference(
                    url=request.build_absolute_uri(
                        reverse('database:kinetics', kwargs={'section': 'families', 'subsection': family + '/groups'})),
                )
            else:
                reference = rmgpy.data.reference.Reference(
                    url=request.build_absolute_uri(
                        reverse('database:kinetics', kwargs={'section': 'families', 'subsection': family + '/rules'})),
                )
            reference_type = ''

            entry_list.append((entry0, reaction.template, reference))

    reaction_url = getReactionUrl(reaction0, resonance=resonance)

    assert not (entry and entry_list), 'Either `entry` or `entry_list` should have a value, not both.'

    return render(request, 'kineticsEntry.html',
                  {'section': 'families',
                   'subsection': family,
                   'databaseName': family,
                   'reactants': reactants,
                   'arrow': arrow,
                   'products': products,
                   'reference': reference,
                   'referenceType': reference_type,
                   'entry': entry,
                   'entry_list': entry_list,
                   'forward': True,
                   'reactionUrl': reaction_url,
                   'reaction': reaction0,
                   'plotWidth': 500,
                   'plotHeight': 400 + 15 * len(entry_list),
                   })


def kineticsJavaEntry(request, entry, reactants_fig, products_fig, kineticsParameters, kineticsModel):
    section = ''
    subsection = ''
    database_name = 'RMG-Java Database'
    reference = ''
    reference_type = ''
    arrow = '&hArr;'
    return render(request, 'kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database_name, 'entry': entry, 'reactants': reactants_fig, 'arrow': arrow, 'products': products_fig, 'reference': reference, 'referenceType': reference_type, 'kinetics': entry.data})


def kineticsSearch(request):
    """
    A view of a form for specifying a set of reactants to search the database
    for reactions. Redirects to kineticsResults to view the results of the search.
    """
    # Load the kinetics database if necessary
    database.load('kinetics')

    if request.method == 'POST':
        form = KineticsSearchForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            kwargs = {}
            # Save reactants and products as kwargs without quoting because reverse() automatically quotes urls
            kwargs['reactant1'] = form.cleaned_data['reactant1']

            reactant2 = form.cleaned_data['reactant2']
            if reactant2 != '':
                kwargs['reactant2'] = reactant2

            product1 = form.cleaned_data['product1']
            if product1 != '':
                kwargs['product1'] = product1

            product2 = form.cleaned_data['product2']
            if product2 != '':
                kwargs['product2'] = product2

            kwargs['resonance'] = form.cleaned_data['resonance']

            return HttpResponseRedirect(reverse('database:kinetics-results', kwargs=kwargs))
    else:
        form = KineticsSearchForm()

    return render(request, 'kineticsSearch.html', {'form': form})


def kineticsResults(request, reactant1, reactant2='', reactant3='', product1='', product2='', product3='', resonance=True):
    """
    A view used to present a list of unique reactions that result from a
    valid kinetics search.
    """
    # Load the kinetics database if necessary
    database.load('kinetics')

    reactant_list = []
    reactant_list.append(moleculeFromURL(reactant1))
    if reactant2 != '':
        reactant_list.append(moleculeFromURL(reactant2))
    if reactant3 != '':
        reactant_list.append(moleculeFromURL(reactant3))

    if product1 != '' or product2 != '' or product3 != '':
        product_list = []
        if product1 != '':
            product_list.append(moleculeFromURL(product1))
        if product2 != '':
            product_list.append(moleculeFromURL(product2))
        if product3 != '':
            product_list.append(moleculeFromURL(product3))
    else:
        product_list = None

    # Search for the corresponding reaction(s)
    reaction_list = generateReactions(database, reactant_list, product_list, resonance=resonance)

    # Remove duplicates from the list and count the number of results
    unique_reaction_list = []
    unique_reaction_count = []
    for reaction in reaction_list:
        for i, rxn in enumerate(unique_reaction_list):
            if reaction.is_isomorphic(rxn):
                unique_reaction_count[i] += 1
                break
        else:
            unique_reaction_list.append(reaction)
            unique_reaction_count.append(1)

    reaction_data_list = []
    for reaction, count in zip(unique_reaction_list, unique_reaction_count):
        forward = reactionHasReactants(reaction, reactant_list)
        if not forward:
            reaction = Reaction(reactants=reaction.products,
                                products=reaction.reactants)
        reactants = ' + '.join([getStructureInfo(reactant) for reactant in reaction.reactants])
        arrow = '&hArr;' if reaction.reversible else '&rarr;'
        products = ' + '.join([getStructureInfo(product) for product in reaction.products])
        reaction_url = getReactionUrl(reaction, resonance=resonance)
        reaction_data_list.append([reactants, arrow, products, count, reaction_url])

    return render(request, 'kineticsResults.html', {'reactionDataList': reaction_data_list})


def kineticsData(request, reactant1, reactant2='', reactant3='', product1='', product2='', product3='', resonance=True):
    """
    A view used to present a list of reactions and the associated kinetics
    for each.
    """
    # Load the kinetics database if necessary
    database.load('kinetics')
    # Also load the thermo database so we can generate reverse kinetics if necessary
    database.load('thermo')

    reactant_list = []
    reactant_list.append(moleculeFromURL(reactant1))
    if reactant2 != '':
        reactant_list.append(moleculeFromURL(reactant2))
    if reactant3 != '':
        reactant_list.append(moleculeFromURL(reactant3))

    if product1 != '' or product2 != '' or product3 != '':
        product_list = []
        if product1 != '':
            product_list.append(moleculeFromURL(product1))
        if product2 != '':
            product_list.append(moleculeFromURL(product2))
        if product3 != '':
            product_list.append(moleculeFromURL(product3))

        reverse_reaction = Reaction(reactants=product_list, products=reactant_list)
        reverse_reaction_url = getReactionUrl(reverse_reaction, resonance=resonance)
    else:
        product_list = None

    # Search for the corresponding reaction(s)
    reaction_list = generateReactions(database, reactant_list, product_list, resonance=resonance)

    kinetics_data_list = []
    family = ''

    # Determine number of template matches
    num_template_rxns_forward = 0
    num_template_rxns_reverse = 0
    for reaction in reaction_list:
        if isinstance(reaction, TemplateReaction) and reaction.estimator == 'rate rules':
            if reactionHasReactants(reaction, reactant_list):
                num_template_rxns_forward += 1
            else:
                num_template_rxns_reverse += 1

    count_template_rxns_forward = 0
    count_template_rxns_reverse = 0

    # Go through database and group additivity kinetics entries
    for reaction in reaction_list:
        # Generate the thermo data for the species involved
        for reactant in reaction.reactants:
            generateSpeciesThermo(reactant, database)
        for product in reaction.products:
            generateSpeciesThermo(product, database)

        # If the kinetics are ArrheniusEP and ArrheniusBM, replace them with Arrhenius
        if isinstance(reaction.kinetics, (ArrheniusEP, ArrheniusBM)):
            reaction.kinetics = reaction.kinetics.to_arrhenius(reaction.get_enthalpy_of_reaction(298))

        is_forward = reactionHasReactants(reaction, reactant_list)

        reactants = ' + '.join([getStructureInfo(reactant) for reactant in reaction.reactants])
        arrow = '&hArr;' if reaction.reversible else '&rarr;'
        products = ' + '.join([getStructureInfo(reactant) for reactant in reaction.products])
        if isinstance(reaction, TemplateReaction):
            counter = ''
            if reaction.estimator == 'rate rules':
                if is_forward:
                    count_template_rxns_forward += 1
                    if num_template_rxns_forward > 1:
                        counter = ', forward template {0} of {1}'.format(count_template_rxns_forward, num_template_rxns_forward)
                else:
                    count_template_rxns_reverse += 1
                    if num_template_rxns_reverse > 1:
                        counter = ', reverse template {0} of {1}'.format(count_template_rxns_reverse, num_template_rxns_reverse)

            source = '{0} (RMG-Py {1}{2})'.format(reaction.family, reaction.estimator, counter)

            href = getReactionUrl(reaction, family=reaction.family, estimator=reaction.estimator, resonance=resonance)
            entry = Entry(data=reaction.kinetics)
            family = reaction.family
        elif isinstance(reaction, DepositoryReaction):
            if 'untrained' in reaction.depository.name:
                continue
            source = '%s' % (reaction.depository.name)
            href = reverse('database:kinetics-entry', kwargs={'section': 'families', 'subsection': reaction.depository.label, 'index': reaction.entry.index})
            entry = reaction.entry
        elif isinstance(reaction, LibraryReaction):
            source = reaction.library.name
            href = reverse('database:kinetics-entry', kwargs={'section': 'libraries', 'subsection': reaction.library.label, 'index': reaction.entry.index})
            entry = reaction.entry

        forward_kinetics = reaction.kinetics

        entry.result = len(kinetics_data_list) + 1

        if is_forward:
            kinetics_data_list.append([reactants, arrow, products, entry, forward_kinetics, source, href, is_forward])
        else:
            try:
                reverse_kinetics = reaction.generate_reverse_rate_coefficient()
            except ReactionError:
                # The method does not support `generate_reverse_rate_coefficient`
                reverse_kinetics = None
            else:
                reverse_kinetics.Tmin = forward_kinetics.Tmin
                reverse_kinetics.Tmax = forward_kinetics.Tmax
                reverse_kinetics.Pmin = forward_kinetics.Pmin
                reverse_kinetics.Pmax = forward_kinetics.Pmax
            finally:
                kinetics_data_list.append([products, arrow, reactants, entry, reverse_kinetics, source, href, is_forward])

    # Construct new entry form from group-additive result
    # Need to get group-additive reaction from generateReaction with only_families
    # +--> otherwise, adjacency list doesn't store reaction template properly
    if family:
        additive_list = generateReactions(database, reactant_list, product_list, only_families=family, resonance=resonance)
        additive_list = [rxn for rxn in additive_list if isinstance(rxn, TemplateReaction)]
        reaction = additive_list[0]
        new_entry = io.StringIO(u'')
        try:
            if reactionHasReactants(reaction, reactant_list):
                rmgpy.data.kinetics.save_entry(new_entry, Entry(label=str(reaction), item=Reaction(reactants=reaction.reactants, products=reaction.products)))
            else:
                rmgpy.data.kinetics.save_entry(new_entry, Entry(label=str(reaction), item=Reaction(reactants=reaction.products, products=reaction.reactants)))
        except Exception as e:
            new_entry.write("ENTRY WAS NOT PARSED CORRECTLY.\n")
            new_entry.write(str(e))
            pass
        entry_string = new_entry.getvalue()
        entry_string = re.sub('^entry\(\n', '', entry_string)  # remove leading entry(
        entry_string = re.sub('\s*index = -?\d+,\n', '', entry_string)  # remove the 'index = 23,' (or -1)line
        new_entry_form = KineticsEntryEditForm(initial={'entry': entry_string})
    else:
        new_entry_form = None

    rate_form = RateEvaluationForm()
    eval = []
    if request.method == 'POST':
        rate_form = RateEvaluationForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()
        if rate_form.is_valid():
            temperature = Quantity(rate_form.cleaned_data['temperature'], str(rate_form.cleaned_data['temperature_units'])).value_si
            pressure = Quantity(rate_form.cleaned_data['pressure'], str(rate_form.cleaned_data['pressure_units'])).value_si
            eval = [temperature, pressure]

    # Generate InChIs here so we can catch errors
    reactant_inchis = []
    for reactant in reactant_list:
        try:
            reactant_inchis.append(reactant.inchi)
        except ValueError:
            reactant_inchis.append('')

    product_inchis = []
    for product in product_list:
        try:
            product_inchis.append(product.inchi)
        except ValueError:
            product_inchis.append('')

    return render(request, 'kineticsData.html',
                  {'kineticsDataList': kinetics_data_list,
                   'plotWidth': 500,
                   'plotHeight': 400 + 15 * len(kinetics_data_list),
                   'reactantList': reactant_list,
                   'productList': product_list,
                   'reactantInChIs': reactant_inchis,
                   'productInChIs': product_inchis,
                   'reverseReactionURL': reverse_reaction_url,
                   'form': rate_form,
                   'eval': eval,
                   'new_entry_form': new_entry_form,
                   'subsection': family
                   })


def moleculeSearch(request):
    """
    Creates webpage form to display molecule drawing for a specified
    adjacency list or other molecule identifier. Also provides interface
    for initiating thermochemistry or transport search.
    """
    form = MoleculeSearchForm()
    structure_markup = ''
    old_adjlist = ''
    molecule = Molecule()
    smiles = ''
    inchi = ''

    if request.method == 'POST':
        posted = MoleculeSearchForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()

        adjlist = None

        if posted.is_valid():
            adjlist = posted.cleaned_data['species']
            if adjlist != '':
                molecule.from_adjacency_list(adjlist)
                structure_markup = getStructureInfo(molecule)
                adjlist = molecule.to_adjacency_list()  # obtain full adjlist, in case hydrogens were non-explicit

        try:
            smiles = molecule.to_smiles()
        except ValueError:
            pass

        try:
            inchi = molecule.to_inchi()
        except ValueError:
            pass

        form = MoleculeSearchForm(initial, error_class=DivErrorList)

        if adjlist is not None:
            if 'thermo' in request.POST:
                return HttpResponseRedirect(reverse('database:thermo-data', kwargs={'adjlist': adjlist}))

            if 'transport' in request.POST:
                return HttpResponseRedirect(reverse('database:transport-data', kwargs={'adjlist': adjlist}))

            if 'resonance' in request.POST:
                return HttpResponseRedirect(reverse('database:resonance', kwargs={'adjlist': adjlist}))

            if 'reset' in request.POST:
                form = MoleculeSearchForm()
                structure_markup = ''
                molecule = Molecule()

            try:
                old_adjlist = molecule.to_adjacency_list(remove_h=True, old_style=True)
                print(old_adjlist)
            except Exception:
                pass

    return render(request, 'moleculeSearch.html',
                  {'structure_markup': structure_markup,
                   'molecule': molecule,
                   'smiles': smiles,
                   'inchi': inchi,
                   'form': form,
                   'oldAdjlist': old_adjlist,
                   })


def solvationSearch(request):
    """
    Creates webpage form to display solvation data upon choosing a solvent and a solute.
    """
    from rmgweb.database.forms import SolvationSearchForm
    form = SolvationSearchForm()
    structure_markup = ''
    molecule = Molecule()
    if request.method == 'POST':
        posted = SolvationSearchForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()

        form = SolvationSearchForm(initial, error_class=DivErrorList)
        if posted.is_valid():
            adjlist = posted.cleaned_data['adjlist']
            if adjlist != '':
                molecule.from_adjacency_list(adjlist)
                structure_markup = getStructureInfo(molecule)
                solute_adjlist = molecule.to_adjacency_list()  # obtain full adjlist, in case hydrogens were non-explicit
                solvent = posted.cleaned_data['solvent']
                solvent_temp = posted.cleaned_data['solvent_temp']
                temp = posted.cleaned_data['temp']
                if solvent == '':
                    solvent = 'None'
                if solvent_temp == '':
                    solvent_temp = 'None'

            if 'solvation' in request.POST:
                return HttpResponseRedirect(reverse('database:solvation-data', kwargs={'solute_adjlist': solute_adjlist, 'solvent': solvent,
                                                                                       'solvent_temp': solvent_temp, 'temp': temp}))

            if 'reset' in request.POST:
                form = SolvationSearchForm()
                structure_markup = ''
                molecule = Molecule()

    return render(request, 'solvationSearch.html', {'structure_markup': structure_markup, 'molecule': molecule, 'form': form})


def solvationSolventSearch(request):
    """
    Creates webpage form to display solvent data upon choosing a solvent species.
    """
    from rmgweb.database.forms import SolventSearchForm
    form = SolventSearchForm()
    structure_markup = ''
    molecule = Molecule()
    if request.method == 'POST':
        posted = SolventSearchForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()

        form = SolventSearchForm(initial, error_class=DivErrorList)
        if posted.is_valid():
            adjlist = posted.cleaned_data['adjlist']
            if adjlist != '':
                molecule.from_adjacency_list(adjlist)
                structure_markup = getStructureInfo(molecule)
                solvent_adjlist = molecule.to_adjacency_list()  # obtain full adjlist, in case hydrogens were non-explicit

            if 'solventSearch' in request.POST:
                return HttpResponseRedirect(reverse('database:solvation-solventData', kwargs={'solvent_adjlist': solvent_adjlist}))

            if 'reset' in request.POST:
                form = SolventSearchForm()
                structure_markup = ''
                molecule = Molecule()

    return render(request, 'solvationSolventSearch.html', {'structure_markup': structure_markup, 'molecule': molecule, 'form': form})


def groupDraw(request):
    """
    Creates webpage form to display group chemgraph upon entering adjacency list.
    """
    from rmgweb.database.forms import GroupDrawForm
    form = GroupDrawForm()
    structure_markup = ''
    group = Group()
    if request.method == 'POST':
        posted = GroupDrawForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()

        if posted.is_valid():
            adjlist = posted.cleaned_data['group']
            if adjlist != '':
                group.from_adjacency_list(adjlist)
                structure_markup = groupToInfo(group)
                adjlist = group.to_adjacency_list()  # obtain full adjlist, in case hydrogens were non-explicit

        form = GroupDrawForm(initial, error_class=DivErrorList)

        if 'reset' in request.POST:
            form = GroupDrawForm()
            structure_markup = ''
            group = Group()

    return render(request, 'groupDraw.html', {'structure_markup': structure_markup, 'group': group, 'form': form})


def EniSearch(request):
    """
    Creates webpage form to display detergent and deposit structures upon entering smiles as well as returns binding constants
    between the detergent and deposit
    """
    from rmgweb.database.tools import getAbrahamAB
    if request.method == 'POST':
        form = EniSearchForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            detergent_adjlist = form.cleaned_data['detergent']
            deposit_adjlist = form.cleaned_data['deposit']

            detergent = Molecule()
            detergent.from_adjacency_list(detergent_adjlist)
            detergent_smiles = detergent.to_smiles()
            detergent_structure = getStructureInfo(detergent)

            deposit = Molecule()
            deposit.from_adjacency_list(deposit_adjlist)
            deposit_smiles = deposit.to_smiles()
            deposit_structure = getStructureInfo(deposit)

            detergentA, detergentB = getAbrahamAB(detergent_smiles)
            depositA, depositB = getAbrahamAB(deposit_smiles)

            # Estimating the binding strength assuming the the detergent to be the donor and dirt to be acceptor
            logK_AB = 7.354 * detergentA * depositB
            # Estimating the binding strength assuming the the detergent to be the acceptor and dirt to be donor
            logK_BA = 7.354 * detergentB * depositA

    else:
        detergentA = 0
        detergentB = 0
        depositA = 0
        depositB = 0
        logK_AB = 0
        logK_BA = 0
        form = EniSearchForm()

    return render(request, 'EniSearch.html', {'detergentA': detergentA, 'detergentB': detergentB, 'depositA': depositA, 'depositB': depositB, 'logKAB': logK_AB, 'logKBA': logK_BA, 'form': form})


def moleculeEntry(request, adjlist):
    """
    Returns an html page which includes the image of the molecule
    and its corresponding adjacency list/SMILES/InChI, as well
    as molecular weight info and a button to retrieve thermo data.

    Basically works as an equivalent of the molecule search function.
    """
    adjlist = urllib.parse.unquote(adjlist)
    try:
        molecule = Molecule().from_adjacency_list(adjlist)
    except:
        return HttpResponseBadRequest('<h1>Bad Request (400)</h1><p>Invalid adjacency list.</p>')
    structure = getStructureInfo(molecule)
    
    mol_weight = molecule.get_molecular_weight()

    old_adjlist = ''
    try:
        old_adjlist = molecule.to_adjacency_list(remove_h=True, old_style=True)
    except:
        pass
    
    smiles = ''
    try:
        smiles = molecule.to_smiles()
    except ValueError:
        pass
    
    inchi = ''
    try:
        inchi = molecule.to_inchi()
    except ValueError:
        pass

    return render(request, 'moleculeEntry.html', 
                  {'structure': structure,
                   'smiles': smiles,
                   'adjlist': adjlist,
                   'mol_weight': mol_weight,
                   'old_adjlist': old_adjlist})


def groupEntry(request, adjlist):
    """
    Returns an html page which includes the image of the group.

    Basically works as an equivalent of the group search function.
    """
    adjlist = urllib.parse.unquote(adjlist)
    try:
        group = Group().from_adjacency_list(adjlist)
    except:
        return HttpResponseBadRequest('<h1>Bad Request (400)</h1><p>Invalid adjacency list.</p>')
    structure = getStructureInfo(group)

    return render(request, 'groupEntry.html', {'structure': structure, 'group': group})


def json_to_adjlist(request):
    """
    Interprets ChemDoodle JSON and returns an RMG adjacency list.
    """
    adjlist = ''
    if request.is_ajax() and request.method == 'POST':
        cd_json_str = request.POST.get('data')
        cd_json = json.loads(cd_json_str)

        try:
            atoms = []
            # Parse atoms in json dictionary
            for a in cd_json['a']:
                atoms.append(Atom(
                    element=str(a['l']) if 'l' in a else 'C',
                    charge=a['c'] if 'c' in a else 0,
                    radical_electrons=a['r'] if 'r' in a else 0,
                    lone_pairs=a['p'] if 'p' in a else 0,
                ))
            # Initialize molecule with atoms
            mol = Molecule(atoms=atoms)
            # Parse bonds in json dictionary
            for b in cd_json['b']:
                mol.add_bond(Bond(
                    atom1=atoms[b['b']],
                    atom2=atoms[b['e']],
                    order=b['o'] if 'o' in b else 1,
                ))
            # Hydrogens are implicit, so we need to add hydrogens
            Saturator.saturate(mol.atoms)
            mol.update()
            # Generate adjacency list
            adjlist = mol.to_adjacency_list()
        except AtomTypeError:
            adjlist = 'Invalid Molecule'
        except:
            adjlist = 'Unable to convert molecule drawing to adjacency list.'

    return HttpResponse(adjlist)


def generateResonanceStructure(request, adjlist):
    """
    Creates webpage that display the representative and non-representative resonance structure
    of give molecule structure.
    """
    # Convert adjlist to real adjacency list
    adjlist = urllib.parse.unquote(adjlist)

    # Obtain the molecule structure
    molecule = Molecule().from_adjacency_list(adjlist)
    features = analyze_molecule(molecule)

    # Generate unfiltered resonance structure for the molecule
    res_list_expoct = generate_resonance_structures(molecule, filter_structures=False)

    # Generate representative structure of expanded-octet
    repr_expoct = filter_structures(res_list_expoct, mark_unreactive=False, allow_expanded_octet=True, features=features)

    # Generate representative structure of octet
    repr_oct = filter_structures(res_list_expoct, mark_unreactive=False, allow_expanded_octet=False, features=features)

    output = []
    for item in res_list_expoct:
        # (item, repr, oct, origin)
        content = []
        if (item in repr_oct) and (item in repr_expoct):
            content = [getStructureInfo(item), 'repr_both']
        elif item in repr_oct:
            content = [getStructureInfo(item), 'repr_oct']
        elif item in repr_expoct:
            content = [getStructureInfo(item), 'repr_expoct']
        else:
            content = [getStructureInfo(item), 'unre']

        if molecule.is_isomorphic(item):
            content[1] = content[1] + ' origin'

        output.append(tuple(content))

    return render(request, 'resonance.html', {'structure': output, })
