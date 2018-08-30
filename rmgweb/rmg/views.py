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

import os

from django.forms.models import BaseInlineFormSet, inlineformset_factory
from django.shortcuts import render
from django.template import RequestContext

from rmgweb.rmg.models import *
from rmgweb.rmg.forms import *

################################################################################

def index(request):
    """
    The RMG simulation homepage.
    """
    return render(request, 'rmg.html')

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
            path = 'media/rmg/tools/chemkin/output.html'
            # Generate the output HTML file
            chemkin.createOutput()
            # Go back to the network's main page
            return render(request, 'chemkinUpload.html', {'form': form, 'path':path})


    # Otherwise create the form
    else:
        form = UploadChemkinForm(instance=chemkin)
        
    return render(request, 'chemkinUpload.html', {'form': form,'path':path})

def convertAdjlists(request):
    """
    Allows user to upload a dictionary txt file and convert it back into old style adjacency lists in the form of a txt file.
    """
    conversion = AdjlistConversion()
    path = ''
    conversion.deleteDir()
    
    if request.method == 'POST':
        conversion.createDir()
        form = UploadDictionaryForm(request.POST, request.FILES, instance=conversion)
        if form.is_valid():
            form.save()
            path = 'media/rmg/tools/adjlistConversion/RMG_Dictionary.txt'
            # Generate the output HTML file
            conversion.createOutput()
            # Go back to the network's main page
            return render(request, 'dictionaryUpload.html', {'form': form, 'path':path})

    # Otherwise create the form
    else:
        form = UploadDictionaryForm(instance=conversion)
        
    return render(request, 'dictionaryUpload.html', {'form': form,'path':path})

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
            return render(request, 'modelCompare.html', {'form': form, 'path':path})


    # Otherwise create the form
    else:
        form = ModelCompareForm(instance=diff)

    return render(request, 'modelCompare.html', {'form': form,'path':path})


def mergeModels(request):
    """
    Merge 2 RMG models with their chemkin and species dictionaries.  
    Produces a merged chemkin file and species dictionary.
    """
    model = Diff()
    path = ''
    model.deleteDir()
    
    if request.method == 'POST':
        model.createDir()
        form = ModelCompareForm(request.POST, request.FILES, instance = model)
        if form.is_valid():
            form.save()
            model.merge()
            path = 'media/rmg/tools/compare'
            #[os.path.join(model.path,'chem.inp'), os.path.join(model.path,'species_dictionary.txt'), os.path.join(model.path,'merging_log.txt')]
            return render(request, 'mergeModels.html', {'form': form, 'path':path})
    else:
        form = ModelCompareForm(instance=model)

    return render(request, 'mergeModels.html', {'form': form,'path':path})



def generateFlux(request):
    """
    Allows user to upload a set of RMG condition files and/or chemkin species concentraiton output
    to generate a flux diagram video.
    """

    from rmgpy.tools.fluxdiagram import createFluxDiagram
        
    flux = FluxDiagram()
    path = ''
    flux.deleteDir()

    if request.method == 'POST':
        flux.createDir()
        form = FluxDiagramForm(request.POST, request.FILES,instance=flux)
        if form.is_valid():
            form.save()
            input = os.path.join(flux.path,'input.py')
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
       
            createFluxDiagram(input, chemkin, dict, savePath=flux.path, java=java, settings=settings, chemkinOutput=chemkinOutput)
            # Look at number of subdirectories to determine where the flux diagram videos are
            subdirs = [name for name in os.listdir(flux.path) if os.path.isdir(os.path.join(flux.path, name))]
            subdirs.remove('species')
            return render(request, 'fluxDiagram.html', {'form': form, 'path':subdirs})

    else:
        form = FluxDiagramForm(instance=flux)

    return render(request, 'fluxDiagram.html', {'form': form,'path':path})


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
            return render(request, 'populateReactionsUpload.html', {'form': form, 'output': outputPath, 'chemkin': chemkinPath})


    # Otherwise create the form
    else:
        form = PopulateReactionsForm(instance=populateReactions)
        
    return render(request, 'populateReactionsUpload.html', {'form': form, 'output': outputPath, 'chemkin': chemkinPath})



def input(request):
    ThermoLibraryFormset = inlineformset_factory(Input, ThermoLibrary, ThermoLibraryForm, 
                                                 BaseInlineFormSet, extra=1, can_delete=True)
    ReactionLibraryFormset = inlineformset_factory(Input, ReactionLibrary, ReactionLibraryForm, 
                                                   BaseInlineFormSet, extra=1, can_delete=True)
    ReactorSpeciesFormset = inlineformset_factory(Input, ReactorSpecies, ReactorSpeciesForm, 
                                                  BaseInlineFormSet, extra = 1, can_delete=True)
    ReactorFormset = inlineformset_factory(Input, Reactor, ReactorForm, 
                                           BaseInlineFormSet, extra = 1, can_delete=True)

    Input.objects.all().delete()
    input = Input()
    input.deleteDir()
    
    uploadform = UploadInputForm(instance=input)
    form = InputForm(instance=input)
    thermolibformset = ThermoLibraryFormset(instance=input)
    reactionlibformset = ReactionLibraryFormset(instance=input)
    reactorspecformset = ReactorSpeciesFormset(instance=input)
    reactorformset = ReactorFormset(instance=input)
    upload_error = ''
    input_error = ''    
    
    if request.method == 'POST':
        input.createDir()
        
        # Load an input file into the form by uploading it
        if "upload" in request.POST:
            uploadform = UploadInputForm(request.POST, request.FILES, instance=input)
            if uploadform.is_valid():
                uploadform.save()
                initial_thermo_libraries, initial_reaction_libraries, initial_reactor_systems, initial_species, initial = input.loadForm(input.loadpath)
                
                # Make the formsets the lengths of the initial data
                if initial_thermo_libraries:
                    ThermoLibraryFormset = inlineformset_factory(Input, ThermoLibrary, ThermoLibraryForm, BaseInlineFormSet, 
                                                                 extra=len(initial_thermo_libraries), can_delete=True)
                if initial_reaction_libraries:
                    ReactionLibraryFormset = inlineformset_factory(Input, ReactionLibrary, ReactionLibraryForm, BaseInlineFormSet, 
                                                               extra=len(initial_reaction_libraries), can_delete=True)
                ReactorSpeciesFormset = inlineformset_factory(Input, ReactorSpecies, ReactorSpeciesForm, BaseInlineFormSet, 
                                                              extra=len(initial_species), can_delete=True)
                ReactorFormset = inlineformset_factory(Input, Reactor, ReactorForm, BaseInlineFormSet, 
                                                       extra = len(initial_reactor_systems), can_delete=True)
                thermolibformset = ThermoLibraryFormset()
                reactionlibformset = ReactionLibraryFormset()
                reactorspecformset = ReactorSpeciesFormset()
                reactorformset = ReactorFormset()
                
                # Load the initial data into the forms
                form = InputForm(initial = initial)
                for subform, data in zip(thermolibformset.forms, initial_thermo_libraries):
                    subform.initial = data
                for subform, data in zip(reactionlibformset.forms, initial_reaction_libraries):
                    subform.initial = data
                for subform, data in zip(reactorspecformset.forms, initial_species):
                    subform.initial = data
                for subform, data in zip(reactorformset.forms, initial_reactor_systems):
                    subform.initial = data
                
            else:
                upload_error = 'Your input file was invalid.  Please try again.'
                
        if "submit" in request.POST:      
            uploadform = UploadInputForm(request.POST, instance=input)
            form = InputForm(request.POST, instance = input)
            thermolibformset = ThermoLibraryFormset(request.POST, instance=input)
            reactionlibformset = ReactionLibraryFormset(request.POST, instance=input)
            reactorspecformset = ReactorSpeciesFormset(request.POST, instance=input)
            reactorformset = ReactorFormset(request.POST, instance=input)
                
            if (form.is_valid() and thermolibformset.is_valid() and reactionlibformset.is_valid()
                and reactorspecformset.is_valid() and reactorformset.is_valid()):
                form.save()
                thermolibformset.save()
                reactionlibformset.save()
                reactorspecformset.save()
                reactorformset.save()
                posted = Input.objects.all()[0]
                input.saveForm(posted, form)            
                path = 'media/rmg/tools/input/input.py'            
                return render(request, 'inputResult.html', {'path': path})
            
            else:
                # Will need more useful error messages later.
                input_error = 'Your form was invalid.  Please edit the form and try again.'
       
    return render(request, 'input.html',
                  {'uploadform': uploadform,
                   'form': form,
                   'thermolibformset':thermolibformset,
                   'reactionlibformset': reactionlibformset,
                   'reactorspecformset':reactorspecformset,
                   'reactorformset': reactorformset,
                   'upload_error': upload_error,
                   'input_error': input_error,
                   })
    
    
    
def plotKinetics(request):
    """
    Allows user to upload chemkin files to generate a plot of reaction kinetics.
    """
    from rmgpy.quantity import Quantity
    from rmgweb.database.forms import RateEvaluationForm
            
    
    if request.method == 'POST':
        chemkin = Chemkin()           
        chemkin.createDir()
        form = UploadChemkinForm(request.POST, request.FILES, instance=chemkin)   
        rateForm = RateEvaluationForm(request.POST)
        eval = []
        
        
        if rateForm.is_valid():
            temperature = Quantity(rateForm.cleaned_data['temperature'], str(rateForm.cleaned_data['temperature_units'])).value_si
            pressure = Quantity(rateForm.cleaned_data['pressure'], str(rateForm.cleaned_data['pressure_units'])).value_si
            eval = [temperature, pressure]
            kineticsDataList = chemkin.getKinetics() 
                
        if form.is_valid():            
            form.save()
            kineticsDataList = chemkin.getKinetics()
        
                
            
        return render(request, 'plotKineticsData.html',
                      {'kineticsDataList': kineticsDataList,
                       'plotWidth': 500,
                       'plotHeight': 400 + 15 * len(kineticsDataList),
                       'form': rateForm,
                       'eval': eval,
                       })

    # Otherwise create the form
    else:
        
    
        chemkin = Chemkin()
        chemkin.deleteDir()
        form = UploadChemkinForm(instance=chemkin)
        
    return render(request, 'plotKinetics.html', {'form': form})


def javaKineticsLibrary(request):
    """
    Allows user to upload chemkin files to generate a plot of reaction kinetics.
    """

    eval = False
    
    if request.method == 'POST':
        chemkin = Chemkin()           
        chemkin.createDir()
        form = UploadChemkinForm(request.POST, request.FILES, instance=chemkin)   
        if form.is_valid():            
            form.save()
            chemkin.createJavaKineticsLibrary()
            eval = True
        
                
            
        return render(request, 'javaKineticsLibrary.html',
                      {'form': form, 'eval': eval})

    # Otherwise create the form
    else:
        
    
        chemkin = Chemkin()
        chemkin.deleteDir()
        form = UploadChemkinForm(instance=chemkin)
        
    return render(request, 'javaKineticsLibrary.html', {'form': form})


def evaluateNASA(request):
    """
    Creates webpage form form entering a chemkin format NASA Polynomial and quickly
    obtaining it's enthalpy and Cp values.
    """
    from rmgpy.chemkin import readThermoEntry
    form = NASAForm()
    thermo = None
    thermoData = None
    if request.method == 'POST':
        posted = NASAForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()

        if posted.is_valid():
                NASA = posted.cleaned_data['NASA']     
                if NASA != '':           
                    species, thermo, formula = readThermoEntry(str(NASA))
                    try:
                        thermoData = thermo.toThermoData()
                    except:
                        # if we cannot convert the thermo to thermo data, we will not be able to display the
                        # H298, S298, and Cp values, but that's ok.
                        pass
        
        form = NASAForm(initial, error_class=DivErrorList)
    
    return render(request, 'NASA.html', {'form': form, 'thermo':thermo, 'thermoData':thermoData})
