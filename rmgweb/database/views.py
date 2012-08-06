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

import os
import os.path
import re
import socket
import StringIO # cStringIO is faster, but can't do Unicode
import copy
import time
import subprocess

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
import settings


from rmgpy.molecule.molecule import Molecule
from rmgpy.molecule.group import Group
from rmgpy.thermo import *
from rmgpy.kinetics import *
from rmgpy.reaction import Reaction

import rmgpy
from rmgpy.data.base import Entry, LogicNode
from rmgpy.data.thermo import ThermoDatabase
from rmgpy.data.kinetics import *
from rmgpy.data.rmg import RMGDatabase

from forms import *
from tools import *
from rmgweb.main.tools import *

#from rmgweb.main.tools import moleculeToURL, moleculeFromURL

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
        thermoLibraries = [(label, database.thermo.libraries[label]) for label in database.thermo.libraryOrder]
        #If they weren't already sorted in our preferred order, we'd call thermoLibraries.sort()
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
    if index != 0 and index != -1:
        for entry in database.entries.values():
            if entry.index == index:
                break
        else:
            raise Http404
    else:
        if index == 0:
            index = min(entry.index for entry in database.entries.values() if entry.index > 0)
        else:
            index = max(entry.index for entry in database.entries.values() if entry.index > 0)
        return HttpResponseRedirect(reverse(thermoEntry,
                                            kwargs={'section': section,
                                                    'subsection': subsection,
                                                    'index': index,
                                                    }))

    # Get the structure of the item we are viewing
    structure = getStructureMarkup(entry.item)

    # Prepare the thermo data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, str):
        thermo = ['Link', database.entries[entry.data].index]
    else:
        thermo = entry.data
    
    referenceType = ''
    reference = entry.reference
    return render_to_response('thermoEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'structure': structure, 'reference': reference, 'referenceType': referenceType, 'thermo': thermo}, context_instance=RequestContext(request))

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
    from tools import database

    adjlist = str(adjlist.replace(';', '\n'))
    molecule = Molecule().fromAdjacencyList(adjlist)
    species = Species(molecule=[molecule])
    species.generateResonanceIsomers()
    
    # Get the thermo data for the molecule
    thermoDataList = []
    for data, library, entry in database.thermo.getAllThermoData(species):
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
            entry.data,
            source,
            href,
        ))
    
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
    trainedReactions = []
    for entry in training.entries.values():
        for reaction in trainedReactions:
            if reaction.isIsomorphic(entry.item):
                break
        else:
            trainedReactions.append(entry.item)
    
    # Load untrained reactions
    untrainedReactions = []
    for depository in family.depositories:
        if 'training' not in depository.label:
            for entry in depository.entries.values():
                for reaction in trainedReactions:
                    if reaction.isIsomorphic(entry.item):
                        break
                else:
                    for reaction in untrainedReactions:
                        if reaction.isIsomorphic(entry.item):
                            break
                    else:
                        untrainedReactions.append(entry.item)
    
    # Sort reactions by reactant size
    untrainedReactions.sort(key=lambda reaction: sum([1 for r in reaction.reactants for a in r.atoms if a.isNonHydrogen()]))
    
    # Build entries
    untrained = KineticsDepository(name='{0}/untrained'.format(family.label),
                                   label='{0}/untrained'.format(family.label))
    count = 1
    for reaction in untrainedReactions:
        untrained.entries['{0}'.format(count)] = Entry(
            item = reaction,
            index = count,
            label = getReactionUrl(reaction),
        )
        count += 1
    
    return untrained

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
            elif isinstance(entry0.data, MultiKinetics): dataFormat = 'MultiKinetics'
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
            elif 'rules' in subsection:
                entry['reactants'] = ' + '.join([getStructureMarkup(reactant) for reactant in entry0.item.reactants])
                entry['products'] = ' + '.join([getStructureMarkup(reactant) for reactant in entry0.item.products])
                entry['arrow'] = '&hArr;' if entry0.item.reversible else '&rarr;'
            else:
                entry['reactants'] = ' + '.join([moleculeToInfo(reactant) for reactant in entry0.item.reactants])
                entry['products'] = ' + '.join([moleculeToInfo(reactant) for reactant in entry0.item.products])
                entry['arrow'] = '&hArr;' if entry0.item.reversible else '&rarr;'
            
            entries.append(entry)
            
        return render_to_response('kineticsTable.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entries': entries, 'tree': tree, 'isGroupDatabase': isGroupDatabase}, context_instance=RequestContext(request))

    else:
        # No subsection was specified, so render an outline of the kinetics
        # database components
        kineticsLibraries = [(label, library) for label, library in rmgDatabase.kinetics.libraries.iteritems() if subsection in label]
        kineticsLibraries.sort()
        for family in rmgDatabase.kinetics.families.itervalues():
            for i in range(0,len(family.depositories)):
                if 'untrained' in family.depositories[i].name:
                    family.depositories.pop(i)
            family.depositories.append(getUntrainedReactions(family))
        kineticsFamilies = [(label, family) for label, family in rmgDatabase.kinetics.families.iteritems() if subsection in label]
        kineticsFamilies.sort()
        return render_to_response('kinetics.html', {'section': section, 'subsection': subsection, 'kineticsLibraries': kineticsLibraries, 'kineticsFamilies': kineticsFamilies}, context_instance=RequestContext(request))

def kineticsUntrained(request, family):
    rmgDatabase = loadDatabase('kinetics', 'families')
    entries0 = getUntrainedReactions(rmgDatabase.kinetics.families[family]).entries.values()
    entries0.sort(key=lambda entry: (entry.index, entry.label))
    
    entries = []
    for entry0 in entries0:
        entry = {
                'index': entry0.index,
                'url': entry0.label,
            }
        
        entry['reactants'] = ' + '.join([moleculeToInfo(reactant) for reactant in entry0.item.reactants])
        entry['products'] = ' + '.join([moleculeToInfo(reactant) for reactant in entry0.item.products])
        entry['arrow'] = '&hArr;' if entry0.item.reversible else '&rarr;'
        
        entries.append(entry)
    return render_to_response('kineticsTable.html', {'section': 'families', 'subsection': family, 'databaseName': '{0}/untrained'.format(family), 'entries': entries, 'tree': None, 'isGroupDatabase': False}, context_instance=RequestContext(request))

def getReactionUrl(reaction, family=None):
    """
    Get the URL (for kinetics data) of a reaction.
    
    Returns '' if the reaction contains functional Groups or LogicNodes instead
    of real Species or Molecules."""
    kwargs = dict()
    for index, reactant in enumerate(reaction.reactants):
        if isinstance(reactant, Group) or isinstance(reactant, LogicNode):
            return ''
        
        mol = reactant if isinstance(reactant,Molecule) else reactant.molecule[0]
        kwargs['reactant{0:d}'.format(index+1)] = moleculeToURL(mol)
    for index, product in enumerate(reaction.products):
        mol = product if isinstance(product,Molecule) else product.molecule[0]
        kwargs['product{0:d}'.format(index+1)] = moleculeToURL(mol)
    if family:
        kwargs['family']=family
        reactionUrl = reverse(kineticsGroupEstimateEntry, kwargs=kwargs)
    else:
        reactionUrl = reverse(kineticsData, kwargs=kwargs)
    return reactionUrl
    

@login_required
def kineticsEntryNewTraining(request, family):
    """
    A view for creating a new entry in a kinetics family training depository.
    """
    # Load the kinetics database, if necessary
    loadDatabase('kinetics', 'families')
    try:
        database = getKineticsDatabase('families', family+'/training')
    except ValueError:
        raise Http404
    
    entry = None
    if request.method == 'POST':
        form = KineticsEntryEditForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            new_entry = form.cleaned_data['entry']
            
            # determine index for new entry (1 higher than highest)
            max_index = max(database.entries.keys() or [0])
            index = max_index + 1
            
            # check it's not already there
            for entry in database.entries.values():
                if entry.item.isIsomorphic(new_entry.item):
                    kwargs = { 'section': 'families',
                       'subsection': family+'/training',
                       'index': entry.index,
                      }
                    forward_url = reverse(kineticsEntry, kwargs=kwargs)
                    message = """
                    This reaction is already in the {0} training set.
                    View or edit it at <a href="{1}">{1}</a>.
                    """.format(family, forward_url)
                    return render_to_response('simple.html', { 
                        'title': 'Reaction already in training set.',
                        'body': message,
                        },
                        context_instance=RequestContext(request))
            new_entry.index = index
            new_history = (time.strftime('%Y-%m-%d'),
                         "{0.first_name} {0.last_name} <{0.email}>".format(request.user),
                         'action',
                         "New entry. "+form.cleaned_data['change']
                            )
            new_entry.history = [new_history]
            
            # Get the entry as a entry_string
            entry_buffer = StringIO.StringIO(u'')
            rmgpy.data.kinetics.saveEntry(entry_buffer, new_entry)
            entry_string = entry_buffer.getvalue()
            entry_buffer.close()
            
            # redirect when done
            kwargs = { 'section': 'families',
                       'subsection': family+'/training',
                       'index': index,
                      }
            forward_url = reverse(kineticsEntry, kwargs=kwargs)
            
            if False:
                # Just return the text.
                return HttpResponse(entry_string, mimetype="text/plain")
            if True:
                # save it
                database.entries[index] = new_entry
                path = os.path.join(settings.DATABASE_PATH, 'kinetics', 'families', family, 'training.py' )
                database.save(path)
                commit_author = "{0.first_name} {0.last_name} <{0.email}>".format(request.user)
                commit_message = "New {family}/training/{index} reaction: {msg}\n\nNew kinetics/families/{family}/training entry number {index} submitted through RMG website:\n{msg}\n{author}".format(family=family, index=index, msg=form.cleaned_data['change'], author=commit_author)
                commit_result = subprocess.check_output(['git', 'commit',
                    '-m', commit_message,
                    '--author', commit_author,
                    path
                    ], cwd=settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                
                
                message = """
                New training reaction saved succesfully:<br>
                <pre>{0}</pre><br>
                See result at <a href="{1}">{1}</a>.
                """.format(commit_result, forward_url)
                return render_to_response('simple.html', { 
                    'title': 'New rate saved successfully.',
                    'body': message,
                    },
                    context_instance=RequestContext(request))
    
    else: # not POST
        form = KineticsEntryEditForm()
        
    return render_to_response('kineticsEntryEdit.html', {'section': 'families',
                                                        'subsection': family+'/training',
                                                        'databaseName': family,
                                                        'entry': entry,
                                                        'form': form,
                                                        },
                                  context_instance=RequestContext(request))
    
@login_required
def kineticsEntryEdit(request, section, subsection, index):
    """
    A view for editing an entry in a kinetics database.
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
    
    if request.method == 'POST':
        form = KineticsEntryEditForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            new_entry = form.cleaned_data['entry']
            new_entry.index = index
            new_entry.history = copy.copy(entry.history)
            new_history = (time.strftime('%Y-%m-%d'),
                         "{0.first_name} {0.last_name} <{0.email}>".format(request.user),
                         'action',
                         form.cleaned_data['change']
                            )
            new_entry.history.append(new_history)
            
            # Get the entry as a entry_string
            entry_buffer = StringIO.StringIO(u'')
            rmgpy.data.kinetics.saveEntry(entry_buffer, new_entry)
            entry_string = entry_buffer.getvalue()
            entry_buffer.close()
            
            if False:
                # Just return the text.
                return HttpResponse(entry_string, mimetype="text/plain")
            if False:
                # Render it as if it were saved.
                return render_to_response('kineticsEntry.html', {'section': section,
                                                         'subsection': subsection,
                                                         'databaseName': database.name,
                                                         'entry': new_entry,
                                                         'reference': entry.reference,
                                                         'kinetics': entry.data,
                                                         },
                              context_instance=RequestContext(request))
            if True:
                # save it
                database.entries[index] = new_entry
                path = os.path.join(settings.DATABASE_PATH, 'kinetics', section, subsection + '.py' )
                database.save(path)
                commit_author = "{0.first_name} {0.last_name} <{0.email}>".format(request.user)
                commit_message = "{1}:{2} {3}\n\nChange to kinetics/{0}/{1} entry {2} submitted through RMG website:\n{3}\n{4}".format(section,subsection,index, form.cleaned_data['change'], commit_author)
                commit_result = subprocess.check_output(['git', 'commit',
                    '-m', commit_message,
                    '--author', commit_author,
                    path
                    ], cwd=settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                
                
                #return HttpResponse(commit_result, mimetype="text/plain")
                
                kwargs = { 'section': section,
                       'subsection': subsection,
                       'index': index,
                      }
                forward_url = reverse(kineticsEntry, kwargs=kwargs)
                message = """
                Changes saved succesfully:<br>
                <pre>{0}</pre><br>
                See result at <a href="{1}">{1}</a>.
                """.format(commit_result, forward_url)
                return render_to_response('simple.html', { 
                    'title': 'Change saved successfully.',
                    'body': message,
                    },
                    context_instance=RequestContext(request))
            
            # redirect
            return HttpResponseRedirect(forward_url)
    
    else: # not POST
        # Get the entry as a entry_string
        entry_buffer = StringIO.StringIO(u'')
        rmgpy.data.kinetics.saveEntry(entry_buffer, entry)
        entry_string = entry_buffer.getvalue()
        entry_buffer.close()
        
        #entry_string = entry.item.reactants[0].toAdjacencyList()
        # remove leading 'entry('
        entry_string = re.sub('^entry\(\n','',entry_string)
        # remove the 'index = 23,' line
        entry_string = re.sub('\s*index = \d+,\n','',entry_string)
        # remove the history and everything after it (including the final ')' )
        entry_string = re.sub('\s+history = \[.*','',entry_string, flags=re.DOTALL)
        
        form = KineticsEntryEditForm(initial={'entry':entry_string })
    
    return render_to_response('kineticsEntryEdit.html', {'section': section,
                                                        'subsection': subsection,
                                                        'databaseName': database.name,
                                                        'entry': entry,
                                                        'form': form,
                                                        },
                                  context_instance=RequestContext(request))

def gitHistory(request,dbtype='',section='',subsection=''):
    """
    A view for seeing the history of the given part of the database.
    dbtype = thermo / kinetics
    section = libraries / families
    subsection = 'Glarborg/C3', etc.
    """
    
    path = os.path.join(settings.DATABASE_PATH, dbtype, section, subsection + '*' )
    history_result = subprocess.check_output(['git', 'log',
                '--', os.path.split(path)[0],
                ], cwd=settings.DATABASE_PATH, stderr=subprocess.STDOUT)

    history = []
    re_commit = re.compile('commit ([a-f0-9]{40})')
    re_author = re.compile('Author: (.*) \<(\w+\@[^> ]+)\>')
    re_date = re.compile('Date:\s+(.*)')
    re_message = re.compile('    (.*)$')
    for line in history_result.split('\n'):
        # print line
        m = re_commit.match(line)
        if m:
            commit = {}
            commit['hash'] = m.group(1)
            commit['message'] = ''
            history.append(commit)
            continue
        m = re_author.match(line)
        if m:
            commit['author_name'] = m.group(1)
            commit['author_email'] = m.group(2)
            commit['author_name_email'] = "{0} <{1}>".format(m.group(1),m.group(2))
            continue
        m = re_date.match(line)
        if m:
            commit['date'] = m.group(1)
            continue
        m = re_message.match(line)
        if m:
            commit['message'] += m.group(1) + '\n'
            continue
            
    return render_to_response('history.html', { 'dbtype': dbtype,
                                                'section': section,
                                                'subsection': subsection,
                                                'history': history,
                                                }, context_instance=RequestContext(request))


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
    if index != 0 and index != -1:
        for entry in database.entries.values():
            if entry.index == index:
                break
        else:
            raise Http404
    else:
        if index == 0:
            index = min(entry.index for entry in database.entries.values() if entry.index > 0)
        else:
            index = max(entry.index for entry in database.entries.values() if entry.index > 0)
        return HttpResponseRedirect(reverse(kineticsEntry,
                                            kwargs={'section': section,
                                                    'subsection': subsection,
                                                    'index': index,
                                                    }))

    reference = entry.reference
    referenceType = ''

    numReactants = 0; degeneracy = 1
    if isinstance(database, KineticsGroups):
        numReactants = database.numReactants
    else:
        numReactants = len(entry.item.reactants)
        degeneracy = entry.item.degeneracy
    
    if isinstance(database, KineticsGroups):
        structure = getStructureMarkup(entry.item)
        return render_to_response('kineticsEntry.html', {'section': section,
                                                         'subsection': subsection,
                                                         'databaseName': database.name,
                                                         'entry': entry,
                                                         'structure': structure,
                                                         'reference': reference,
                                                         'referenceType': referenceType,
                                                         'kinetics': entry.data,
                                                         },
                                  context_instance=RequestContext(request))
    else:
        if 'rules' in subsection:
            reactants = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.reactants])
            products = ' + '.join([getStructureMarkup(reactant) for reactant in entry.item.products])
            arrow = '&hArr;' if entry.item.reversible else '&rarr;'
        else:
            reactants = ' + '.join([moleculeToInfo(reactant) for reactant in entry.item.reactants])
            products = ' + '.join([moleculeToInfo(reactant) for reactant in entry.item.products])
            arrow = '&hArr;' if entry.item.reversible else '&rarr;'

        # Searching for other instances of the reaction only valid for real reactions, not groups
        # If a Group or LogicNode shows up in the reaction, getReactionUrl will return ''
        reactionUrl = getReactionUrl(entry.item)

        
        return render_to_response('kineticsEntry.html', {'section': section,
                                                        'subsection': subsection,
                                                        'databaseName': database.name,
                                                        'entry': entry,
                                                        'reactants': reactants,
                                                        'arrow': arrow,
                                                        'products': products,
                                                        'reference': reference,
                                                        'referenceType': referenceType,
                                                        'kinetics': entry.data,
                                                        'reactionUrl': reactionUrl },
                                  context_instance=RequestContext(request))


def kineticsGroupEstimateEntry(request, family, reactant1, product1, reactant2='', reactant3='', product2='', product3=''):
    """
    View a kinetics group estimate as an entry.
    """
    # Load the kinetics database if necessary
    loadDatabase('kinetics','families')
    # Also load the thermo database so we can generate reverse kinetics if necessary
    loadDatabase('thermo')
    
    # we need 'database' to reference the top level object that we pass to generateReactions
    from tools import database
    
    # check the family exists
    try:
        getKineticsDatabase('families', family+'/groups')
    except ValueError:
        raise Http404

    reactantList = []
    reactantList.append(moleculeFromURL(reactant1))
    if reactant2 != '':
        reactantList.append(moleculeFromURL(reactant2))
    if reactant3 != '':
        reactantList.append(moleculeFromURL(reactant3))

    productList = []
    productList.append(moleculeFromURL(product1))
    if product2 != '':
        productList.append(moleculeFromURL(product2))
    if product3 != '':
        productList.append(moleculeFromURL(product3))    
    
    # Search for the corresponding reaction(s)
    reactionList, empty_list = generateReactions(database, reactantList, productList, only_families=[family])
    
    kineticsDataList = []
    
    # discard all the rates from depositories and rules
    reactionList = [reaction for reaction in reactionList if isinstance(reaction, TemplateReaction)]
    
    # if there are still two, only keep the forward direction
    if len(reactionList)==2:
        reactionList = [reaction for reaction in reactionList if reactionHasReactants(reaction, reactantList)]
    
    assert len(reactionList)==1, "Was expecting one group estimate rate, not {0}".format(len(reactionList))
    reaction = reactionList[0]
    
    # Generate the thermo data for the species involved
    for reactant in reaction.reactants:
        generateSpeciesThermo(reactant, database)
    for product in reaction.products:
        generateSpeciesThermo(product, database)
    
    # If the kinetics are ArrheniusEP, replace them with Arrhenius
    if isinstance(reaction.kinetics, ArrheniusEP):
        reaction.kinetics = reaction.kinetics.toArrhenius(reaction.getEnthalpyOfReaction(298))
    
    reactants = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.reactants])
    arrow = '&hArr;' if reaction.reversible else '&rarr;'
    products = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.products])
    assert isinstance(reaction, TemplateReaction), "Expected group additive kinetics to be a TemplateReaction"
    
    source = '%s (RMG-Py Group additivity)' % (reaction.family.name)
    entry = Entry(
                  item=reaction,
                  data=reaction.kinetics,
                  longDesc=reaction.kinetics.comment,
                  shortDesc="Estimated by RMG-Py Group Additivity",
                  )
                  
    # Get the entry as a entry_string, to populate the New Entry form
    # first, replace the kinetics with a fitted arrhenius form with no comment
    entry.data = reaction.kinetics.toArrhenius()
    entry.data.comment = ''
    entry_buffer = StringIO.StringIO(u'')
    rmgpy.data.kinetics.saveEntry(entry_buffer, entry)
    entry_string = entry_buffer.getvalue()
    entry_buffer.close()
    # replace the kinetics with the original ones
    entry.data = reaction.kinetics
    entry_string = re.sub('^entry\(\n','',entry_string) # remove leading entry(
    entry_string = re.sub('\s*index = -?\d+,\n','',entry_string) # remove the 'index = 23,' (or -1)line
    entry_string = re.sub('\s+history = \[.*','',entry_string, flags=re.DOTALL) # remove the history and everything after it (including the final ')' )
    new_entry_form = KineticsEntryEditForm(initial={'entry':entry_string })

    forwardKinetics = reaction.kinetics
    reverseKinetics = reaction.generateReverseRateCoefficient()
    
    forward = reactionHasReactants(reaction, reactantList) # boolean: true if template reaction in forward direction
    
    reactants = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.reactants])
    products = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.products])
    reference = rmgpy.data.reference.Reference(
                    url=request.build_absolute_uri(reverse(kinetics,kwargs={'section':'families','subsection':family+'/groups'})),
                )
    referenceType = ''
    entry.index=-1

    reactionUrl = getReactionUrl(reaction)

    return render_to_response('kineticsEntry.html', {'section': 'families',
                                                    'subsection': family,
                                                    'databaseName': family,
                                                    'entry': entry,
                                                    'reactants': reactants,
                                                    'arrow': arrow,
                                                    'products': products,
                                                    'reference': reference,
                                                    'referenceType': referenceType,
                                                    'kinetics': reaction.kinetics,
                                                    'reactionUrl': reactionUrl,
                                                    'reaction': reaction,
                                                    'new_entry_form': new_entry_form},
                              context_instance=RequestContext(request))
    

def kineticsJavaEntry(request, entry, reactants_fig, products_fig, kineticsParameters, kineticsModel):
    section = ''
    subsection = ''
    databaseName = 'RMG-Java Database'
    reference = ''
    referenceType = ''
    arrow = '&hArr;'
    return render_to_response('kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': databaseName, 'entry': entry, 'reactants': reactants_fig, 'arrow': arrow, 'products': products_fig, 'reference': reference, 'referenceType': referenceType, 'kinetics': entry.data}, context_instance=RequestContext(request))

def kineticsSearch(request):
    """
    A view of a form for specifying a set of reactants to search the database
    for reactions. Redirects to kineticsResults to view the results of the search.
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

            return HttpResponseRedirect(reverse(kineticsResults, kwargs=kwargs))
    else:
        form = KineticsSearchForm()

    return render_to_response('kineticsSearch.html', {'form': form}, context_instance=RequestContext(request))

def kineticsResults(request, reactant1, reactant2='', reactant3='', product1='', product2='', product3=''):
    """
    A view used to present a list of unique reactions that result from a
    valid kinetics search.
    """
    
    # Load the kinetics database if necessary
    loadDatabase('kinetics')
    from tools import database # the global one with both thermo and kinetics
    
    reactantList = []
    reactantList.append(moleculeFromURL(reactant1))
    if reactant2 != '':
        reactantList.append(moleculeFromURL(reactant2))
    if reactant3 != '':
        reactantList.append(moleculeFromURL(reactant3))

    if product1 != '' or product2 != '' or product3 != '':
        productList = []
        if product1 != '':
            productList.append(moleculeFromURL(product1))
        if product2 != '':
            productList.append(moleculeFromURL(product2))
        if product3 != '':
            productList.append(moleculeFromURL(product3))
    else:
        productList = None
    
    # Search for the corresponding reaction(s)
    reactionList, rmgJavaReactionList = generateReactions(database, reactantList, productList)
    reactionList.extend(rmgJavaReactionList)
        
    # Remove duplicates from the list and count the number of results
    uniqueReactionList = []
    uniqueReactionCount = []
    for reaction in reactionList:
        for i, rxn in enumerate(uniqueReactionList):
            if reaction.isIsomorphic(rxn):
                uniqueReactionCount[i] += 1
                break
        else:
            uniqueReactionList.append(reaction)
            uniqueReactionCount.append(1)
    
    reactionDataList = []
    for reaction, count in zip(uniqueReactionList, uniqueReactionCount):
        reactants = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.reactants])
        arrow = '&hArr;' if reaction.reversible else '&rarr;'
        products = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.products])
        reactionUrl = getReactionUrl(reaction)
        
        forward = reactionHasReactants(reaction, reactantList)
        if forward:
            reactionDataList.append([reactants, arrow, products, count, reactionUrl])
        else:
            reactionDataList.append([products, arrow, reactants, count, reactionUrl])
        
    return render_to_response('kineticsResults.html', {'reactionDataList': reactionDataList}, context_instance=RequestContext(request))

def kineticsData(request, reactant1, reactant2='', reactant3='', product1='', product2='', product3=''):
    """
    A view used to present a list of reactions and the associated kinetics
    for each.
    """
    
    # Load the kinetics database if necessary
    loadDatabase('kinetics')
    # Also load the thermo database so we can generate reverse kinetics if necessary
    loadDatabase('thermo')
    from tools import database # the global one with both thermo and kinetics

    reactantList = []
    reactantList.append(moleculeFromURL(reactant1))
    if reactant2 != '':
        reactantList.append(moleculeFromURL(reactant2))
    if reactant3 != '':
        reactantList.append(moleculeFromURL(reactant3))

    if product1 != '' or product2 != '' or product3 != '':
        productList = []
        if product1 != '':
            productList.append(moleculeFromURL(product1))
        if product2 != '':
            productList.append(moleculeFromURL(product2))
        if product3 != '':
            productList.append(moleculeFromURL(product3))
            
        reverseReaction = Reaction(reactants = productList, products = reactantList)
        reverseReactionURL = getReactionUrl(reverseReaction)
    else:
        productList = None

    # Search for the corresponding reaction(s)
    reactionList, rmgJavaReactionList = generateReactions(database, reactantList, productList)
    reactionList.extend(rmgJavaReactionList)
    
    kineticsDataList = []
    
    # Go through database and group additivity kinetics entries
    for reaction in reactionList:
        # Generate the thermo data for the species involved
        for reactant in reaction.reactants:
            generateSpeciesThermo(reactant, database)
        for product in reaction.products:
            generateSpeciesThermo(product, database)
            
        # If the kinetics are ArrheniusEP, replace them with Arrhenius
        if isinstance(reaction.kinetics, ArrheniusEP):
            reaction.kinetics = reaction.kinetics.toArrhenius(reaction.getEnthalpyOfReaction(298))

        #reactants = [getStructureMarkup(reactant) for reactant in reaction.reactants]
        reactants = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.reactants])
        arrow = '&hArr;' if reaction.reversible else '&rarr;'
        products = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.products])
        if isinstance(reaction, TemplateReaction):
            source = '%s (RMG-Py Group additivity)' % (reaction.family.name)
            href = getReactionUrl(reaction, family=reaction.family.name)
            entry = Entry(data=reaction.kinetics)
            family = reaction.family.name
        elif reaction in rmgJavaReactionList:
            source = 'RMG-Java'
            href = ''
            entry = reaction.entry
        elif isinstance(reaction, DepositoryReaction):
            if 'untrained' in reaction.depository.name:
                continue
            source = '%s' % (reaction.depository.name)
            href = reverse(kineticsEntry, kwargs={'section': 'families', 'subsection': reaction.depository.label, 'index': reaction.entry.index})
            entry = reaction.entry
        elif isinstance(reaction, LibraryReaction):
            source = reaction.library.name
            href = reverse(kineticsEntry, kwargs={'section': 'libraries', 'subsection': reaction.library.label, 'index': reaction.entry.index})
            entry = reaction.entry
        
        forwardKinetics = reaction.kinetics
        
        is_forward = reactionHasReactants(reaction, reactantList)
        entry.result = len(kineticsDataList) + 1

        if is_forward:
            kineticsDataList.append([reactants, arrow, products, entry, forwardKinetics, source, href, is_forward])
        else:
            if isinstance(forwardKinetics, Arrhenius) or isinstance(forwardKinetics, KineticsData):
                reverseKinetics = reaction.generateReverseRateCoefficient()
                reverseKinetics.Tmin = forwardKinetics.Tmin
                reverseKinetics.Tmax = forwardKinetics.Tmax
                reverseKinetics.Pmin = forwardKinetics.Pmin
                reverseKinetics.Pmax = forwardKinetics.Pmax
            else:
                reverseKinetics = None
            kineticsDataList.append([products, arrow, reactants, entry, reverseKinetics, source, href, is_forward])

    # Construct new entry form from group-additive result
    # Need to get group-additive reaction from generateReaction with only_families
    # +--> otherwise, adjacency list doesn't store reaction template properly
    additiveList, empty_list = generateReactions(database, reactantList, productList, only_families=family)
    additiveList = [reaction for reaction in additiveList if isinstance(reaction, TemplateReaction)]
    if len(additiveList)==2:
        additiveList = [reaction for reaction in additiveList if reactionHasReactants(reaction, reactantList)]

    new_entry = StringIO.StringIO(u'')
    rmgpy.data.kinetics.saveEntry(new_entry, Entry(item=additiveList[0]))
    entry_string = new_entry.getvalue()
    entry_string = re.sub('^entry\(\n','',entry_string) # remove leading entry(
    entry_string = re.sub('\s*index = -?\d+,\n','',entry_string) # remove the 'index = 23,' (or -1)line
    entry_string = re.sub('\s+history = \[.*','',entry_string, flags=re.DOTALL) # remove the history and everything after it (including the final ')' )
    new_entry_form = KineticsEntryEditForm(initial={'entry':entry_string })

    form = TemperatureForm()
    temperature = ''
    if request.method == 'POST':
        form = TemperatureForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()
        if form.is_valid():
                temperature = form.cleaned_data['temperature']

    return render_to_response('kineticsData.html', {'kineticsDataList': kineticsDataList,
                                                    'plotWidth': 500,
                                                    'plotHeight': 400 + 15 * len(kineticsDataList),
                                                    'reactantList': reactantList,
                                                    'productList': productList,
                                                    'reverseReactionURL':reverseReactionURL,
                                                    'form':form,
                                                    'temperature':temperature,
                                                    'new_entry_form':new_entry_form,
                                                    'subsection':family
                                                    },
                                             context_instance=RequestContext(request))

def moleculeSearch(request):
    """
    Creates webpage form to display molecule chemgraph upon entering adjacency list, smiles, or inchi, as well as searches for thermochemistry data.
    """
    form = MoleculeSearchForm()
    structure_markup = ''
    molecule = Molecule()
    if request.method == 'POST':
        posted = MoleculeSearchForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()

        if posted.is_valid():
                adjlist = posted.cleaned_data['species']
                if adjlist != '':
                    molecule.fromAdjacencyList(adjlist)
                    structure_markup = getStructureMarkup(molecule)
        
        form = MoleculeSearchForm(initial, error_class=DivErrorList)
        
        if 'thermo' in request.POST:
            return HttpResponseRedirect(reverse(thermoData, kwargs={'adjlist': adjlist}))
        
        if 'reset' in request.POST:
            form = MoleculeSearchForm()
            structure_markup = ''
            molecule = Molecule()
    
    return render_to_response('moleculeSearch.html', {'structure_markup':structure_markup,'molecule':molecule,'form': form}, context_instance=RequestContext(request))

def EniSearch(request):
    """
    Creates webpage form to display detergent and deposit structures upon entering smiles as well as returns binding constants
    between the detergent and deposit
    """
    from tools import getAbrahamAB
    if request.method == 'POST':
        form = EniSearchForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            detergent_adjlist = form.cleaned_data['detergent']
            deposit_adjlist = form.cleaned_data['deposit']

            detergent = Molecule()
            detergent.fromAdjacencyList(detergent_adjlist)
            detergent_smiles = detergent.toSMILES()
            detergent_structure = getStructureMarkup(detergent)

            deposit = Molecule()
            deposit.fromAdjacencyList(deposit_adjlist)
            deposit_smiles = deposit.toSMILES()
            deposit_structure = getStructureMarkup(deposit)
            
            detergentA, detergentB = getAbrahamAB(detergent_smiles)
            depositA, depositB = getAbrahamAB(deposit_smiles)
            
            # Estimating the binding strength assuming the the detergent to be the donor and dirt to be acceptor            
            logK_AB = 7.354*detergentA*depositB
            # Estimating the binding strength assuming the the detergent to be the acceptor and dirt to be donor
            logK_BA = 7.354*detergentB*depositA
    
    else:
        detergentA = 0
        detergentB = 0
        depositA = 0
        depositB = 0
        logK_AB = 0
        logK_BA = 0        
        form = EniSearchForm()            
            
    return render_to_response('EniSearch.html', {'detergentA': detergentA, 'detergentB': detergentB, 'depositA': depositA, 'depositB': depositB, 'logKAB': logK_AB, 'logKBA': logK_BA, 'form': form}, context_instance=RequestContext(request))


def moleculeEntry(request,adjlist):
    """
    Returns an html page which includes the image of the molecule
    and its corresponding adjacency list/SMILES/InChI, as well
    as molecular weight info and a button to retrieve thermo data.

    Basically works as an equivalent of the molecule search function.
    """

    adjlist = str(adjlist.replace(';', '\n'))
    molecule = Molecule().fromAdjacencyList(adjlist)
    structure = getStructureMarkup(molecule)

    return render_to_response('moleculeEntry.html',{'structure':structure,'molecule':molecule}, context_instance=RequestContext(request))
