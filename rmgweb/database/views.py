import os.path

from django.shortcuts import render_to_response
from django.template import RequestContext
import settings

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
    return render_to_response('thermo.html', {'section': section, 'subsection': subsection, 'thermoDatabase': thermoDatabase}, context_instance=RequestContext(request))
