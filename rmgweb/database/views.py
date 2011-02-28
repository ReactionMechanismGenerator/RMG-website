import os.path
import re

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404
import settings

from rmgpy.chem.molecule import Molecule
from rmgpy.chem.pattern import MoleculePattern
from rmgpy.chem.thermo import *
from rmgpy.data.thermo import ThermoDatabase

################################################################################

thermoDatabase = ThermoDatabase()
thermoDatabase.load(path=os.path.join(settings.DATABASE_PATH, 'thermo'))

def getThermoDatabase(section, subsection):
    """
    Return the component of the thermodynamics database corresponding to the
    given `section` and `subsection`. If either of these is invalid, a
    :class:`ValueError` is raised.
    """
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
        structure = '<img src="/adjlist/%s"/>' % adjlist
    elif isinstance(item, MoleculePattern):
        # We can't draw MoleculePattern objects, so just print the adjacency list
        structure = '<pre>%s</pre>' % item.toAdjacencyList()
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

            entries.append((entry.index,entry.label,structure,dataFormat))

        return render_to_response('thermoTable.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entries': entries}, context_instance=RequestContext(request))

    else:
        # No subsection was specified, so render an outline of the thermo
        # database components
        return render_to_response('thermo.html', {'section': section, 'subsection': subsection, 'thermoDatabase': thermoDatabase}, context_instance=RequestContext(request))

def thermoEntry(request, section, subsection, index):
    """
    A view for showing an entry in a thermodynamics database.
    """
    # Determine the entry we wish to view
    try:
        database = getThermoDatabase(section, subsection)
    except ValueError:
        raise Http404
    index = int(index)
    for label, entry in database.entries.iteritems():
        if entry.index == index:
            break
    else:
        raise Http404

    # Get the structure of the item we are viewing
    structure = getStructureMarkup(entry.item)

    # Prepare the thermo data for passing to the template
    # This includes all string formatting, since we can't do that in the template
    if isinstance(entry.data, ThermoGAModel):
        # Thermo data is in group additivity format
        dataFormat = 'Group additivity'
        thermoData = ['%.2f' % (entry.data.H298 / 1000.), '%.2f' % (entry.data.S298)]
        thermoData.append('%g' % (entry.data.Tmin))
        thermoData.append('%g' % (entry.data.Tmax))
        for T, Cp in zip(entry.data.Tdata, entry.data.Cpdata):
            thermoData.append(('%g' % T, '%.2f' % Cp))
    elif isinstance(entry.data, WilhoitModel):
        # Thermo data is in Wilhoit polynomial format
        dataFormat = 'Wilhoit'
        thermoData = [
            '%.2f' % (entry.data.cp0),
            '%.2f' % (entry.data.cpInf),
            '%s' % getLaTeXScientificNotation(entry.data.a0),
            '%s' % getLaTeXScientificNotation(entry.data.a1),
            '%s' % getLaTeXScientificNotation(entry.data.a2),
            '%s' % getLaTeXScientificNotation(entry.data.a3),
            '%.2f' % (entry.data.H0 / 1000.),
            '%.2f' % (entry.data.S0),
            '%.2f' % (entry.data.B),
            '%g' % (entry.data.Tmin),
            '%g' % (entry.data.Tmax),
        ]
    elif isinstance(entry.data, NASAModel):
        # Thermo data is in NASA polynomial format
        dataFormat = 'NASA'
        thermoData = []
        for poly in entry.data.polynomials:
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
    
    return render_to_response('thermoEntry.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entry': entry, 'structure': structure, 'dataFormat': dataFormat, 'thermoData': thermoData}, context_instance=RequestContext(request))
