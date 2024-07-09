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
            return render(request, 'chemkinUpload.html', {'form': form, 'path': path})

    # Otherwise create the form
    else:
        form = UploadChemkinForm(instance=chemkin)

    return render(request, 'chemkinUpload.html', {'form': form, 'path': path})



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
            return render(request, 'modelCompare.html', {'form': form, 'path': path})

    # Otherwise create the form
    else:
        form = ModelCompareForm(instance=diff)

    return render(request, 'modelCompare.html', {'form': form, 'path': path})


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
        form = ModelCompareForm(request.POST, request.FILES, instance=model)
        if form.is_valid():
            form.save()
            model.merge()
            path = 'media/rmg/tools/compare/'
            # [os.path.join(model.path,'chem.inp'), os.path.join(model.path,'species_dictionary.txt'), os.path.join(model.path,'merging_log.txt')]
            return render(request, 'mergeModels.html', {'form': form, 'path': path})
    else:
        form = ModelCompareForm(instance=model)

    return render(request, 'mergeModels.html', {'form': form, 'path': path})


def generateFlux(request):
    """
    Allows user to upload a set of RMG condition files and/or chemkin species concentraiton output
    to generate a flux diagram video.
    """

    from rmgpy.tools.fluxdiagram import create_flux_diagram

    flux = FluxDiagram()
    path = ''
    flux.deleteDir()

    if request.method == 'POST':
        flux.createDir()
        form = FluxDiagramForm(request.POST, request.FILES, instance=flux)
        if form.is_valid():
            form.save()
            arguments = {}
            arguments["chem_output"] = ''
            if 'chem_output' in request.FILES:
                arguments["chem_output"] = os.path.join(flux.path, 'chemkin_output.out')
            arguments['java'] = form.cleaned_data['java']
            arguments['max_nodes'] = form.cleaned_data['max_nodes']
            arguments['max_edges'] = form.cleaned_data['max_edges']
            arguments['time_step'] = form.cleaned_data['time_step']
            arguments['concentration_tol'] = form.cleaned_data['concentration_tol']
            arguments['species_rate_tol'] = form.cleaned_data['species_rate_tol']
            error_message = flux.createOutput(arguments)
            # Look at number of subdirectories to determine where the flux diagram videos are
            if not error_message:
                subdirs = [name for name in os.listdir(os.path.join(flux.path, 'flux'))
                           if os.path.isdir(os.path.join(flux.path, 'flux', name))]
                return render(request, 'fluxDiagram.html', {'form': form, 'path': subdirs, 'error_message': error_message})
            else:
                return render(request, 'fluxDiagram.html', {'form': form, 'path': path, 'error_message': error_message})

    else:
        form = FluxDiagramForm(instance=flux)

    return render(request, 'fluxDiagram.html', {'form': form, 'path': path, 'error_message': ''})


def runPopulateReactions(request):
    """
    Allows user to upload chemkin and RMG dictionary files to generate a nice looking html output.
    """
    populate_reactions = PopulateReactions()
    output_path = ''
    chemkin_path = ''
    populate_reactions.deleteDir()

    if request.method == 'POST':
        populate_reactions.createDir()
        form = PopulateReactionsForm(request.POST, request.FILES, instance=populate_reactions)
        if form.is_valid():
            form.save()
            # Generate the output HTML file
            error_message = populate_reactions.createOutput()
            # Go back to the network's main page
            if not error_message:
                output_path = 'media/rmg/tools/populateReactions/output.html'
                chemkin_path = 'media/rmg/tools/populateReactions/chemkin/chem.inp'
            return render(request, 'populateReactionsUpload.html', {'form': form, 'output': output_path, 'chemkin': chemkin_path,
                                                                    'error_message': error_message})

    # Otherwise create the form
    else:
        form = PopulateReactionsForm(instance=populate_reactions)

    return render(request, 'populateReactionsUpload.html', {'form': form, 'output': output_path, 'chemkin': chemkin_path})


def input(request):
    ThermoLibraryFormset = inlineformset_factory(Input, ThermoLibrary, ThermoLibraryForm,
                                                 BaseInlineFormSet, extra=1, can_delete=True)
    ReactionLibraryFormset = inlineformset_factory(Input, ReactionLibrary, ReactionLibraryForm,
                                                   BaseInlineFormSet, extra=1, can_delete=True)
    ReactorSpeciesFormset = inlineformset_factory(Input, ReactorSpecies, ReactorSpeciesForm,
                                                  BaseInlineFormSet, extra=1, can_delete=True)
    ReactorFormset = inlineformset_factory(Input, Reactor, ReactorForm,
                                           BaseInlineFormSet, extra=1, can_delete=True)

    Input.objects.all().delete()
    input = Input()
    input.deleteDir()

    upload_form = UploadInputForm(instance=input)
    form = InputForm(instance=input)
    thermolib_formset = ThermoLibraryFormset(instance=input)
    reactionlib_formset = ReactionLibraryFormset(instance=input)
    reactorspec_formset = ReactorSpeciesFormset(instance=input)
    reactor_formset = ReactorFormset(instance=input)
    upload_error = ''
    input_error = ''

    if request.method == 'POST':
        input.createDir()

        # Load an input file into the form by uploading it
        if "upload" in request.POST:
            upload_form = UploadInputForm(request.POST, request.FILES, instance=input)
            if upload_form.is_valid():
                upload_form.save()
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
                                                       extra=len(initial_reactor_systems), can_delete=True)
                thermolib_formset = ThermoLibraryFormset()
                reactionlib_formset = ReactionLibraryFormset()
                reactorspec_formset = ReactorSpeciesFormset()
                reactor_formset = ReactorFormset()

                # Load the initial data into the forms
                form = InputForm(initial=initial)
                for subform, data in zip(thermolib_formset.forms, initial_thermo_libraries):
                    subform.initial = data
                for subform, data in zip(reactionlib_formset.forms, initial_reaction_libraries):
                    subform.initial = data
                for subform, data in zip(reactorspec_formset.forms, initial_species):
                    subform.initial = data
                for subform, data in zip(reactor_formset.forms, initial_reactor_systems):
                    subform.initial = data

            else:
                upload_error = 'Your input file was invalid.  Please try again.'

        if "submit" in request.POST:
            upload_form = UploadInputForm(request.POST, instance=input)
            form = InputForm(request.POST, instance=input)
            thermolib_formset = ThermoLibraryFormset(request.POST, instance=input)
            reactionlib_formset = ReactionLibraryFormset(request.POST, instance=input)
            reactorspec_formset = ReactorSpeciesFormset(request.POST, instance=input)
            reactor_formset = ReactorFormset(request.POST, instance=input)

            if (form.is_valid() and thermolib_formset.is_valid() and reactionlib_formset.is_valid()
               and reactorspec_formset.is_valid() and reactor_formset.is_valid()):
                form.save()
                thermolib_formset.save()
                reactionlib_formset.save()
                reactorspec_formset.save()
                reactor_formset.save()
                posted = Input.objects.all()[0]
                input.saveForm(posted, form)
                path = 'media/rmg/tools/input/input.py'
                return render(request, 'inputResult.html', {'path': path})

            else:
                # Will need more useful error messages later.
                input_error = 'Your form was invalid.  Please edit the form and try again.'

    return render(request, 'input.html',
                  {'uploadform': upload_form,
                   'form': form,
                   'thermolibformset': thermolib_formset,
                   'reactionlibformset': reactionlib_formset,
                   'reactorspecformset': reactorspec_formset,
                   'reactorformset': reactor_formset,
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
        rate_form = RateEvaluationForm(request.POST)
        eval = []
        kinetics_data_list = []

        if rate_form.is_valid():
            temperature = Quantity(rate_form.cleaned_data['temperature'], str(rate_form.cleaned_data['temperature_units'])).value_si
            pressure = Quantity(rate_form.cleaned_data['pressure'], str(rate_form.cleaned_data['pressure_units'])).value_si
            eval = [temperature, pressure]
            kinetics_data_list = chemkin.getKinetics()

        if form.is_valid():
            form.save()
            kinetics_data_list = chemkin.getKinetics()

        return render(request, 'plotKineticsData.html',
                      {'kineticsDataList': kinetics_data_list,
                       'plotWidth': 500,
                       'plotHeight': 400 + 15 * len(kinetics_data_list),
                       'form': rate_form,
                       'eval': eval,
                       })

    # Otherwise create the form
    else:

        chemkin = Chemkin()
        chemkin.deleteDir()
        form = UploadChemkinForm(instance=chemkin)

    return render(request, 'plotKinetics.html', {'form': form})


def evaluateNASA(request):
    """
    Creates webpage form form entering a chemkin format NASA Polynomial and quickly
    obtaining it's enthalpy and Cp values.
    """
    from rmgpy.chemkin import read_thermo_entry
    form = NASAForm()
    thermo = None
    thermo_data = None
    if request.method == 'POST':
        posted = NASAForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()

        if posted.is_valid():
            nasa = posted.cleaned_data['nasa']
            if nasa != '':
                species, thermo, formula = read_thermo_entry(nasa)
                try:
                    thermo_data = thermo.to_thermo_data()
                except:
                    # if we cannot convert the thermo to thermo data, we will not be able to display the
                    # H298, S298, and Cp values, but that's ok.
                    pass

        form = NASAForm(initial, error_class=DivErrorList)

    return render(request, 'NASA.html', {'form': form, 'thermo': thermo, 'thermoData': thermo_data})
