import os.path
import re

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404
import settings

from rmgpy.chem.molecule import Molecule
from rmgpy.chem.thermo import *
from rmgpy.data.thermo import ThermoDatabase

################################################################################

thermoDatabase = ThermoDatabase()
thermoDatabase.load(path=os.path.join(settings.DATABASE_PATH, 'thermo'))

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
        if section == 'depository':
            try:
                database = thermoDatabase.depository[subsection]
            except KeyError:
                raise Http404
        elif section == 'libraries':
            libraries = [library for library in thermoDatabase.libraries if library.label == subsection]
            if len(libraries) != 1: raise Http404
            database = libraries[0]
        elif section == 'groups':
            try:
                database = thermoDatabase.groups[subsection]
            except KeyError:
                raise Http404

        # Sort entries by index
        entries0 = database.library.values()
        entries0.sort(key=lambda entry: entry.index)

        entries = []
        for entry in entries0:

            if isinstance(entry.item, Molecule):
                # We can draw Molecule objects, so use that instead of an adjacency list
                adjlist = entry.item.toAdjacencyList(removeH=True)
                adjlist = adjlist.replace('\n', ';')
                adjlist = re.sub('\s+', '%20', adjlist)
                structure = '<img src="/adjlist/%s"/>' % adjlist
            else:
                # We can't draw MoleculePattern objects, so just print the adjacency list
                structure = '<pre>%s</pre>' % entry.item.toAdjacencyList(removeH=True)

            if isinstance(entry.data, ThermoGAModel): dataFormat = 'Group additivity'
            elif isinstance(entry.data, WilhoitModel): dataFormat = 'Wilhoit'
            elif isinstance(entry.data, NASAModel): dataFormat = 'NASA'

            entries.append((entry.index,entry.label,structure,dataFormat))

        return render_to_response('thermoTable.html', {'section': section, 'subsection': subsection, 'databaseName': database.name, 'entries': entries}, context_instance=RequestContext(request))

    else:
        # No subsection was specified, so render an outline of the thermo
        # database components
        return render_to_response('thermo.html', {'section': section, 'subsection': subsection, 'thermoDatabase': thermoDatabase}, context_instance=RequestContext(request))
