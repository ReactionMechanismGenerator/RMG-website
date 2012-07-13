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

from rmgpy.molecule.molecule import Molecule
from rmgpy.molecule.group import Group
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

def compareModels(request):
    """
    Allows user to compare 2 RMG models with their chemkin and species dictionaries and generate
    a pretty HTML diff file.
    """
    diff = Diff()
    path = ''
    diff.deleteDir()

    if request.method == 'POST':
        diff.createDir()
        form = ModelCompareForm(request.POST, request.FILES, instance=diff)
        if form.is_valid():
            form.save()
            path = 'media/rmg/tools/compare/diff.html'
            # Generate the output HTML file
            diff.createOutput()
            return render_to_response('modelCompare.html', {'form': form, 'path':path}, context_instance=RequestContext(request))


    # Otherwise create the form
    else:
        form = ModelCompareForm(instance=diff)

    return render_to_response('modelCompare.html', {'form': form,'path':path}, context_instance=RequestContext(request))

def generateFlux(request):
    """
    Allows user to upload a set of RMG condition files and/or chemkin species concentraiton output
    to generate a flux diagram video.
    """

    from generateFluxDiagram import createFluxDiagram
        
    flux = FluxDiagram()
    path = ''
    flux.deleteDir()

    if request.method == 'POST':
        flux.createDir()
        form = FluxDiagramForm(request.POST, request.FILES,instance=flux)
        if form.is_valid():
            form.save()
            input = os.path.join(flux.path,'input.py')
            print input
            chemkin = os.path.join(flux.path,'chem.inp')
            dict = os.path.join(flux.path,'species_dictionary.txt')
            chemkinOutput = ''
            if 'ChemkinOutput' in request.FILES:
                chemkinOutput = os.path.join(flux.path,'chemkin_output.out')
            java = form.cleaned_data['Java']
            settings = {}
            settings['maximumNodeCount'] = form.cleaned_data['MaxNodes']  
            settings['maximumEdgeCount'] = form.cleaned_data['MaxEdges']
            settings['timeStep'] = form.cleaned_data['TimeStep']
            settings['concentrationTolerance'] = form.cleaned_data['ConcentrationTolerance']
            settings['speciesRateTolerance'] = form.cleaned_data['SpeciesRateTolerance']
       
            createFluxDiagram(flux.path, input, chemkin, dict, java, settings, chemkinOutput)
            # Look at number of subdirectories to determine where the flux diagram videos are
            subdirs = [name for name in os.listdir(flux.path) if os.path.isdir(os.path.join(flux.path, name))]
            print subdirs
            subdirs.remove('species')
            print subdirs
            return render_to_response('fluxDiagram.html', {'form': form, 'path':subdirs}, context_instance=RequestContext(request))

    else:
        form = FluxDiagramForm(instance=flux)

    return render_to_response('fluxDiagram.html', {'form': form,'path':path}, context_instance=RequestContext(request))


def runPopulateReactions(request):
    """
    Allows user to upload chemkin and RMG dictionary files to generate a nice looking html output.
    """
    populateReactions = PopulateReactions()
    outputPath = ''
    chemkinPath = ''
    populateReactions.deleteDir()
    
    if request.method == 'POST':
        populateReactions.createDir()
        form = PopulateReactionsForm(request.POST, request.FILES, instance=populateReactions)
        if form.is_valid():
            form.save()
            outputPath = 'media/rmg/tools/populateReactions/output.html'
            chemkinPath = 'media/rmg/tools/populateReactions/chemkin/chem.inp'
            # Generate the output HTML file
            populateReactions.createOutput()
            # Go back to the network's main page
            return render_to_response('populateReactionsUpload.html', {'form': form, 'output': outputPath, 'chemkin': chemkinPath}, context_instance=RequestContext(request))


    # Otherwise create the form
    else:
        form = PopulateReactionsForm(instance=populateReactions)
        
    return render_to_response('populateReactionsUpload.html', {'form': form, 'output': outputPath, 'chemkin': chemkinPath}, context_instance=RequestContext(request))


