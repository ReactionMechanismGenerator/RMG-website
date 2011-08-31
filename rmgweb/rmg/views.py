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
from rmgweb.rmg.models import *
from rmgweb.rmg.forms import *

from rmgpy.molecule import Molecule
from rmgpy.group import Group
from rmgpy.thermo import *
from rmgpy.kinetics import *

from rmgpy.data.base import Entry
from rmgpy.data.thermo import ThermoDatabase
from rmgpy.data.kinetics import *
from rmgpy.data.rmg import RMGDatabase

from rmgweb.main.tools import *
from rmgweb.database.views import loadDatabase

################################################################################


def index(request):
    """
    The RMG simulation homepage.
    """
    return render_to_response('rmg.html', context_instance=RequestContext(request))

def convertChemkin(request):
    """
    Allows user to upload chemkin and RMG dictionary files to generate a nice looking html output.
    """
    chemkin = Chemkin()
    path = ''
    chemkin.deleteDir()
    
    if request.method == 'POST':
        chemkin.createDir()
        form = UploadChemkinForm(request.POST, request.FILES, instance=chemkin)
        if form.is_valid():
            form.save()
            path = 'media/rmg/tools/output.html'
            # Generate the output HTML file
            chemkin.createOutput()
            # Go back to the network's main page
            return render_to_response('chemkinUpload.html', {'form': form, 'path':path}, context_instance=RequestContext(request))


    # Otherwise create the form
    else:
        form = UploadChemkinForm(instance=chemkin)
        
    return render_to_response('chemkinUpload.html', {'form': form,'path':path}, context_instance=RequestContext(request))

