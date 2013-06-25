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

import cookielib
import copy
import os
import re
import shutil
import socket
import StringIO # cStringIO is faster, but can't do Unicode
import subprocess
import sys
import time
import urllib
import urllib2

from BeautifulSoup import BeautifulSoup
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
import settings

import exportOldDatabase

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

def export(request, type):
    """
    Export the RMG database to the old RMG-Java format.
    """

    # Build archive filenames from git hash and compression type
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                  cwd=settings.DATABASE_PATH)[:7]
    base = 'RMG_database_{0}'.format(sha)
    file_zip = '{0}.zip'.format(base)
    file_tar = '{0}.tar.gz'.format(base)
    if type == 'zip':
        file = file_zip
    elif type == 'tar.gz':
        file = file_tar

    # Set output path
    path = os.path.join(settings.PROJECT_PATH, '..', 'database', 'export')
    output = os.path.join(path, 'RMG_database')

    # Assert archives do not already exist
    if not os.path.exists(os.path.join(path, file)):

        # Export old database
        exportOldDatabase.export(settings.DATABASE_PATH,
                                 output,
                                 loadDatabase())

        # Compress database to zip
        cmd_zip = ['zip', '-r', base, 'RMG_database']
        result_zip = subprocess.check_output(cmd_zip, cwd=path)

        # Compress database to tar.gz
        cmd_tar = ['tar', '-czf', file_tar, 'RMG_database']
        result_tar = subprocess.check_output(cmd_tar, cwd=path)

        # Make compressed databases group-writable
        os.chmod(os.path.join(path, file_zip), 0664)
        os.chmod(os.path.join(path, file_tar), 0664)

        # Remove exported database
        shutil.rmtree(output)

    # Redirect to requested compressed database
    return HttpResponseRedirect('export/{0}'.format(file))

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
            elif isinstance(entry.data, NASA): dataFormat = 'NASA'
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

    entry = getCommit(entry)

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
            #data = convertThermoData(data, molecule, NASA)
            symmetryNumber = molecule.symmetryNumber
            entry = Entry(data=data)
        elif library in database.thermo.depository.values():
            source = 'Depository'
            href = reverse(thermoEntry, kwargs={'section': 'depository', 'subsection': library.label, 'index': entry.index})
        elif library in database.thermo.libraries.values():
            source = library.name
            href = reverse(thermoEntry, kwargs={'section': 'libraries', 'subsection': library.label, 'index': entry.index})
        thermoDataList.append((
            entry,
            data,
            source,
            href,
        ))
    
    # Get the structure of the item we are viewing
    structure = getStructureMarkup(molecule)

    return render_to_response('thermoData.html', {'molecule': molecule, 'structure': structure, 'thermoDataList': thermoDataList, 'symmetryNumber': symmetryNumber, 'plotWidth': 500, 'plotHeight': 400 + 15 * len(thermoDataList)}, context_instance=RequestContext(request))

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


def getCommit(entry):

    path = rmgpy.settings['database.directory']

    entry.sha = []
    for date, author, event, desc in entry.history:
        cmd = ['git', 'log', '--reverse', '--format=%H',
               '--since="{0}"'.format(date), '-S', date]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=path)
        sha = ''
        for i in range(0, 10):
            time.sleep(0.01)
            sha = p.stdout.readline()
            if sha:
                break
        p.kill()
        entry.sha.append(sha)

    return entry


###############################################################################


def queryNIST(entry, squib, entries, user):
    """
    Pulls NIST kinetics and reference information, given
    a unique entry squib (e.g. `1999SMI/GOL57-101:3`).
    """

    url = 'http://kinetics.nist.gov/kinetics/Detail?id={0}'.format(squib)
    cookiejar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))

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
                          'SetUnitsBean.jsp', data=urllib.urlencode(post))
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

    # Set entry history
    user_string = '{0.first_name} {0.last_name} <{0.email}>'.format(user)
    desc = 'Imported from NIST database at {0}'.format(url)
    entry.history = [(time.asctime(), user_string, 'action', desc)]

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
        entry.referenceType = reftype.nextSibling[7:].lower()
    except:
        entry.referenceType = ''

    # Grab short description
    try:
        short = soup.findAll('b', text='Data type:')[0].parent
        entry.shortDesc = short.nextSibling[13:].replace('  ', ' ')
    except:
        entry.shortDesc = ''

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
    longDesc = ''
    try:
        ref = soup.findAll('b', text='Reference reaction:')[0].parent
        longDesc += '\nReference Reaction: '
        ref = ref.nextSibling.nextSibling
        while True:
            try:
                longDesc += ref.text
            except:
                longDesc += ref
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
        long = rate.nextSibling
        while True:
            try:
                if long.name == 'br':
                    break
            except:
                pass
            long = long.nextSibling
        while True:
            try:
                if ((long.nextSibling.name == 'a' and
                     long.nextSibling.text == 'View') or
                    long.nextSibling is None):
                        break
            except:
                pass
            try:
                if long.name == 'br':
                    longDesc += '\n'
                else:
                    longDesc += long.text
            except:
                longDesc += long.replace('\n', '')
            long = long.nextSibling
        for line in longDesc.splitlines():
            if 'Data type:' not in line and 'Category:' not in line:
                entry.longDesc += line + '\n'
        swaps = [('&nbsp;&nbsp;\n', ' '),
                 ('&nbsp;', ' '),
                 ('  ', ' '),
                 ('Comments: ', '\n'),
                 ('\n ', '\n'),
                 ('&middot;', u'·')]
        for swap in swaps:
            entry.longDesc = entry.longDesc.replace(swap[0], swap[1])
        entry.longDesc = entry.longDesc.strip()
    except:
        pass

    # Grab uncertainty for pre-exponential
    try:
        error = rate.nextSibling
        text = ''
        while not '[' in text:
            error = error.nextSibling
            try:
                text = error.text
            except:
                text = error
        if '&plusmn;' in text:
            text = text.split('&plusmn;')[1].split(' ')[0]
            entry.data.A.uncertaintyType = '+|-'
            if text.isdigit():
                entry.data.A.uncertainty = float(text)
            elif 'x' in text:
                entry.data.A.uncertainty = float(text.split('x')[0] + 'e' +
                                                 error.nextSibling.text)
            if len(entry.item.reactants) == 2:
                entry.data.A.uncertainty /= 1.0e6
    except:
        pass
    for line in entry.longDesc.splitlines():
        if 'Uncertainty:' in line and entry.data.A.uncertainty == 0.0:
            entry.data.A.uncertainty = float(line.split(' ')[1])
            entry.data.A.uncertaintyType = '*|/'
    if entry.data.A.uncertaintyType is '+|-':
        if abs(entry.data.A.uncertainty) > abs(entry.data.A.value_si):
            u = entry.data.A.uncertainty
            entry.longDesc += ('\nNote: Invalid A value uncertainty '
                               '({0} {1})'.format(u, entry.data.A.units) +
                               ' found and ignored')
            entry.data.A.uncertainty = 0.0

    # Grab uncertainty for temperature exponent
    for sup in soup.findAll('sup'):
        if '(' in sup.text and ')' in sup.text and '&plusmn;' in sup.text:
            try:
                error = item.text.split('&plusmn;')[1].split(')')[0]
                entry.data.n.uncertainty = float(error)
                entry.data.n.uncertaintyType = '+|-'
            except:
                pass
            break
    if entry.data.n.uncertaintyType is '+|-':
        if abs(entry.data.n.uncertainty) > abs(entry.data.n.value_si):
            u = entry.data.n.uncertainty
            entry.longDesc += ('\nNote: Invalid n value uncertainty '
                               '({0}) found and ignored'.format(u))
            entry.data.n.uncertainty = 0.0

    # Grab uncertainty and better value for activation energy
    for sup in soup.findAll('sup'):
        if 'J/mole]/RT' in sup.text:
            entry.data.Ea.value_si = -float(sup.text.split(' ')[0])
            try:
                error = sup.text.split('&plusmn;')[1]
                entry.data.Ea.uncertainty = float(error.split(' ')[0])
                entry.data.Ea.uncertaintyType = '+|-'
            except:
                pass
            break
    if entry.data.Ea.uncertaintyType is '+|-':
        if abs(entry.data.Ea.uncertainty) > abs(entry.data.Ea.value_si):
            u = entry.data.Ea.uncertainty
            entry.longDesc += ('\nNote: Invalid Ea value uncertainty '
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
            if any(isinstance(item, list) for item in entries0):
                # if the entries are lists
                entries0 = reduce(lambda x,y: x+y, entries0)
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
            elif isinstance(entry0.data, MultiPDepArrhenius): dataFormat = 'MultiPDepArrhenius'
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

def getReactionUrl(reaction, family=None, estimator=None):
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
        if estimator:
            kwargs['family'] = family
            kwargs['estimator'] = estimator.replace(' ','_')
            reactionUrl = reverse(kineticsGroupEstimateEntry, kwargs=kwargs)
        else:
            reactionUrl = ''
    else:
        reactionUrl = reverse(kineticsData, kwargs=kwargs)
    return reactionUrl
    

@login_required
def kineticsEntryNew(request, family, type):
    """
    A view for creating a new entry in a kinetics family depository.
    """
    # Load the kinetics database, if necessary
    loadDatabase('kinetics', 'families')

    subsection = '{0}/{1}'.format(family, type)
    try:
        database = getKineticsDatabase('families', subsection)
    except ValueError:
        raise Http404
    
    entries = database.entries.values()
    if any(isinstance(item, list) for item in entries):
        # if the entries are lists
        entries = reduce(lambda x,y: x+y, entries)
    entry = None
    if request.method == 'POST':
        form = KineticsEntryEditForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            new_entry = form.cleaned_data['entry']

            # Set new entry index
            indices = [entry.index for entry in database.entries.values()]
            new_entry.index = max(indices or [0]) + 1

            # Confirm entry does not already exist in depository
            for entry in entries:
                if ((type == 'training' and new_entry.item.isIsomorphic(entry.item)) or
                    (type == 'NIST' and new_entry.label == entry.label)):
                        kwargs = {'section': 'families',
                                  'subsection': subsection,
                                  'index': entry.index,
                                  }
                        forward_url = reverse(kineticsEntry, kwargs=kwargs)
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
                        return render_to_response('simple.html',
                                                  {'title': title,
                                                   'body': message,
                                                   },
                                                  context_instance=RequestContext(request))

            if type == 'NIST':
                squib = new_entry.label
                new_entry.data = Arrhenius()
                new_entry = queryNIST(new_entry, new_entry.label, entries, request.user)
                if not isinstance(new_entry, Entry):
                    url = 'http://nist.kinetics.gov/kinetics/Detail?id={0}'.format(squib)
                    message = 'Error in grabbing kinetics from <a href="{0}">NIST</a>.<br>{1}'.format(url, new_entry)
                    return render_to_response('simple.html',
                                              {'title': 'Error in grabbing kinetics for {0}.'.format(squib),
                                               'body': message,
                                               },
                                              context_instance=RequestContext(request))
                msg = 'Imported from NIST database at {0}'.format(new_entry.reference.url)
            else:
                msg = form.cleaned_data['change']
                new_entry.history = [(time.asctime(),
                                      '{0.first_name} {0.last_name} <{0.email}>'.format(request.user),
                                      'action',
                                      'New entry. {0}'.format(form.cleaned_data['change']))]

            # Format the new entry as a string
            entry_buffer = StringIO.StringIO(u'')
            rmgpy.data.kinetics.saveEntry(entry_buffer, new_entry)
            entry_string = entry_buffer.getvalue()
            entry_buffer.close()
            
            # Build the redirect URL
            kwargs = {'section': 'families',
                      'subsection': subsection,
                      'index': new_entry.index,
                      }
            forward_url = reverse(kineticsEntry, kwargs=kwargs)
            
            if False:
                # Just return the text.
                return HttpResponse(entry_string, mimetype="text/plain")
            if True:
                # save it
                database.entries[index] = new_entry
                path = os.path.join(settings.DATABASE_PATH, 'kinetics', 'families', family, '{0}.py'.format(type))
                database.save(path)
                commit_author = '{0.first_name} {0.last_name} <{0.email}>'.format(request.user)
                commit_message = 'New Entry: {family}/{type}/{index}\n\n{msg}'.format(family=family,
                                                                                      type=type,
                                                                                      index=new_entry.index,
                                                                                      msg=msg)
                commit_message += '\n\nSubmitted through the RMG website.'
                commit_result = subprocess.check_output(['git', 'commit',
                    '-m', commit_message,
                    '--author', commit_author,
                    path
                    ], cwd=settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                subprocess.check_output(['git', 'push'], cwd=settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                message = """
                New entry saved succesfully:<br>
                <pre>{0}</pre><br>
                See result at <a href="{1}">{1}</a>.
                """.format(commit_result, forward_url)
                return render_to_response('simple.html', { 
                    'title': '',
                    'body': message,
                    },
                    context_instance=RequestContext(request))
    else: # not POST
        form = KineticsEntryEditForm()

    return render_to_response('kineticsEntryEdit.html', {'section': 'families',
                                                        'subsection': subsection,
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
    
    entries = database.entries.values()
    if any(isinstance(item, list) for item in entries):
        # if the entries are lists
        entries = reduce(lambda x,y: x+y, entries)
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
            new_entry.history = copy.copy(entry.history)
            new_history = (time.asctime(),
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
                subprocess.check_output(['git', 'push'], cwd=settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                
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

@login_required
def thermoEntryNew(request, section, subsection, adjlist):
    """
    A view for creating a new thermodynamics entry into any database section.
    """
    # Load the thermo database, if necessary
    loadDatabase('thermo')
    
    adjlist = str(adjlist.replace(';', '\n'))
    molecule = Molecule().fromAdjacencyList(adjlist)

    try:
        database = getThermoDatabase(section, subsection)
    except ValueError:
        raise Http404
    
    entries = database.entries.values()
    if any(isinstance(item, list) for item in entries):
        # if the entries are lists
        entries = reduce(lambda x,y: x+y, entries)
    entry = None
    if request.method == 'POST':
        form = ThermoEntryEditForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            new_entry = form.cleaned_data['entry']

            # Set new entry index
            indices = [entry.index for entry in database.entries.values()]
            new_entry.index = max(indices or [0]) + 1

            # Do not need to confirm entry already exists- should allow the user to store multiple 
            # thermo entries in to the depository or into separate libraries for the same molecule if the data exists.

            msg = form.cleaned_data['change']
            new_entry.history = [(time.asctime(),
                                      '{0.first_name} {0.last_name} <{0.email}>'.format(request.user),
                                      'action',
                                      'New entry. {0}'.format(form.cleaned_data['change']))]

            # Format the new entry as a string
            entry_buffer = StringIO.StringIO(u'')
            rmgpy.data.thermo.saveEntry(entry_buffer, new_entry)
            entry_string = entry_buffer.getvalue()
            entry_buffer.close()
            
            # Build the redirect URL
            kwargs = {'section': section,
                      'subsection': subsection,
                      'index': new_entry.index,
                      }
            forward_url = reverse(thermoEntry, kwargs=kwargs)
            
            if False:
                # Just return the text.
                return HttpResponse(entry_string, mimetype="text/plain")
            if True:
                # save it
                database.entries[index] = new_entry
                path = os.path.join(settings.DATABASE_PATH, 'thermo', section, subsection + '.py')
                database.save(path)
                commit_author = '{0.first_name} {0.last_name} <{0.email}>'.format(request.user)
                commit_message = 'New Entry: {section}/{subsection}/{index}\n\n{msg}'.format(section=section,
                                                                                      subsection=subsection,
                                                                                      index=new_entry.index,
                                                                                      msg=msg)
                commit_message += '\n\nSubmitted through the RMG website.'
                commit_result = subprocess.check_output(['git', 'commit',
                    '-m', commit_message,
                    '--author', commit_author,
                    path
                    ], cwd=settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                subprocess.check_output(['git', 'push'], cwd=settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                message = """
                New entry saved succesfully:<br>
                <pre>{0}</pre><br>
                See result at <a href="{1}">{1}</a>.
                """.format(commit_result, forward_url)
                return render_to_response('simple.html', { 
                    'title': '',
                    'body': message,
                    },
                    context_instance=RequestContext(request))
    else: # not POST
        entry_string ="""
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
shortDesc = u"\"\" "\"\",
longDesc = 
    u"\"\"
    
    "\"\",
        """.format(label=molecule.toSMILES(),adjlist=molecule.toAdjacencyList())

        form = ThermoEntryEditForm(initial={'entry':entry_string })

    return render_to_response('thermoEntryEdit.html', {'section': section,
                                                        'subsection': subsection,
                                                        'databaseName': database.name,
                                                        'entry': entry,
                                                        'form': form,
                                                        },
                                  context_instance=RequestContext(request))
    

@login_required
def thermoEntryEdit(request, section, subsection, index):
    """
    A view for editing an entry in a thermo database.
    """

    # Load the kinetics database, if necessary
    loadDatabase('thermo', section)

    # Determine the entry we wish to view
    try:
        database = getThermoDatabase(section, subsection)
    except ValueError:
        raise Http404
    
    entries = database.entries.values()
    if any(isinstance(item, list) for item in entries):
        # if the entries are lists
        entries = reduce(lambda x,y: x+y, entries)
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
            new_entry.history = copy.copy(entry.history)
            new_history = (time.asctime(),
                         "{0.first_name} {0.last_name} <{0.email}>".format(request.user),
                         'action',
                         form.cleaned_data['change']
                            )
            new_entry.history.append(new_history)
            
            # Get the entry as a entry_string
            entry_buffer = StringIO.StringIO(u'')
            rmgpy.data.thermo.saveEntry(entry_buffer, new_entry)
            entry_string = entry_buffer.getvalue()
            entry_buffer.close()
            
            if False:
                # Just return the text.
                return HttpResponse(entry_string, mimetype="text/plain")
            if False:
                # Render it as if it were saved.
                return render_to_response('thermoEntry.html', {'section': section,
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
                path = os.path.join(settings.DATABASE_PATH, 'thermo', section, subsection + '.py' )
                database.save(path)
                commit_author = "{0.first_name} {0.last_name} <{0.email}>".format(request.user)
                commit_message = "{1}:{2} {3}\n\nChange to thermo/{0}/{1} entry {2} submitted through RMG website:\n{3}\n{4}".format(section,subsection,index, form.cleaned_data['change'], commit_author)
                commit_result = subprocess.check_output(['git', 'commit',
                    '-m', commit_message,
                    '--author', commit_author,
                    path
                    ], cwd=settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                subprocess.check_output(['git', 'push'], cwd=settings.DATABASE_PATH, stderr=subprocess.STDOUT)
                
                #return HttpResponse(commit_result, mimetype="text/plain")
                
                kwargs = { 'section': section,
                       'subsection': subsection,
                       'index': index,
                      }
                forward_url = reverse(thermoEntry, kwargs=kwargs)
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
        rmgpy.data.thermo.saveEntry(entry_buffer, entry)
        entry_string = entry_buffer.getvalue()
        entry_buffer.close()
        
        #entry_string = entry.item.reactants[0].toAdjacencyList()
        # remove leading 'entry('
        entry_string = re.sub('^entry\(\n','',entry_string)
        # remove the 'index = 23,' line
        entry_string = re.sub('\s*index = \d+,\n','',entry_string)
        # remove the history and everything after it (including the final ')' )
        entry_string = re.sub('\s+history = \[.*','',entry_string, flags=re.DOTALL)
        
        form = ThermoEntryEditForm(initial={'entry':entry_string })
    
    return render_to_response('thermoEntryEdit.html', {'section': section,
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
    
    entries = database.entries.values()
    if any(isinstance(item, list) for item in entries):
        # if the entries are lists
        entries = reduce(lambda x,y: x+y, entries)
                
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
        return HttpResponseRedirect(reverse(kineticsEntry,
                                            kwargs={'section': section,
                                                    'subsection': subsection,
                                                    'index': index,
                                                    }))

    entry = getCommit(entry)

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


def kineticsGroupEstimateEntry(request, family, estimator, reactant1, product1, reactant2='', reactant3='', product2='', product3=''):
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
    
    # retain only the rates from the selected estimation method
    reactionList = [reaction for reaction in reactionList if reaction.estimator == estimator.replace('_',' ')]
    
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
    assert isinstance(reaction, TemplateReaction), "Expected group estimated kinetics to be a TemplateReaction"
    
    source = '%s (RMG-Py %s)' % (reaction.family.name, reaction.estimator)
    
    if reaction.kinetics:
        entry = Entry(
                      item=reaction,
                      data=reaction.kinetics,
                      longDesc=reaction.kinetics.comment,
                      shortDesc="Estimated by RMG-Py %s" % (reaction.estimator),
                      )
    else:
        entry = Entry(
                      item=reaction,
                      data=reaction.kinetics,
                      shortDesc="Estimated by RMG-Py %s" % (reaction.estimator),
                      )
                  
    # Get the entry as an entry_string, to populate the New Entry form
    if reaction.kinetics is None:
        pass
    elif isinstance(reaction.kinetics, Arrhenius):
        entry.data = reaction.kinetics
    elif isinstance(reaction.kinetics, KineticsData):
        entry.data = reaction.kinetics.toArrhenius()
    else:
        raise Exception('Unexpected group kinetics type encountered: {0}'.format(reaction.kinetics.__class__.__name__))
    
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
    
    forward = reactionHasReactants(reaction, reactantList) # boolean: true if template reaction in forward direction
    
    reactants = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.reactants])
    products = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.products])
    
    if estimator == 'group_additivity':
        reference = rmgpy.data.reference.Reference(
                    url=request.build_absolute_uri(reverse(kinetics,kwargs={'section':'families','subsection':family+'/groups'})),
                    )
    else:
        reference = rmgpy.data.reference.Reference(
                    url=request.build_absolute_uri(reverse(kinetics,kwargs={'section':'families','subsection':family+'/rules'})),
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
    family = ''
    
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
            source = '%s (RMG-Py %s)' % (reaction.family.name, reaction.estimator)
            
            href = getReactionUrl(reaction, family=reaction.family.name, estimator=reaction.estimator)
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
    if family:
        additiveList, empty_list = generateReactions(database, reactantList, productList, only_families=family)
        additiveList = [rxn for rxn in additiveList if isinstance(rxn, TemplateReaction)]
        reaction = additiveList[0]
        new_entry = StringIO.StringIO(u'')
        if reactionHasReactants(reaction, reactantList):
            rmgpy.data.kinetics.saveEntry(new_entry, Entry(item=Reaction(reactants=reaction.reactants, products=reaction.products)))
        else:
            rmgpy.data.kinetics.saveEntry(new_entry, Entry(item=Reaction(reactants=reaction.products, products=reaction.reactants)))
        
        entry_string = new_entry.getvalue()
        entry_string = re.sub('^entry\(\n','',entry_string) # remove leading entry(
        entry_string = re.sub('\s*index = -?\d+,\n','',entry_string) # remove the 'index = 23,' (or -1)line
        entry_string = re.sub('\s+history = \[.*','',entry_string, flags=re.DOTALL) # remove the history and everything after it (including the final ')' )
        new_entry_form = KineticsEntryEditForm(initial={'entry':entry_string })
    else:
        new_entry_form = None

    rateForm = RateEvaluationForm()
    eval = []
    if request.method == 'POST':
        rateForm = RateEvaluationForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()
        if rateForm.is_valid():
            temperature = Quantity(rateForm.cleaned_data['temperature'], str(rateForm.cleaned_data['temperature_units'])).value_si
            pressure = Quantity(rateForm.cleaned_data['pressure'], str(rateForm.cleaned_data['pressure_units'])).value_si
            eval = [temperature, pressure]

    return render_to_response('kineticsData.html', {'kineticsDataList': kineticsDataList,
                                                    'plotWidth': 500,
                                                    'plotHeight': 400 + 15 * len(kineticsDataList),
                                                    'reactantList': reactantList,
                                                    'productList': productList,
                                                    'reverseReactionURL':reverseReactionURL,
                                                    'form':rateForm,
                                                    'eval':eval,
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
