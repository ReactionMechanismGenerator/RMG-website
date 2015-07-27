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
import time
import re

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from rmgpy.statmech import *

from rmgweb.main.tools import *
from models import *
from forms import *

################################################################################

def index(request):
    """
    The Pressure Dependent Networks homepage.
    """
    if request.user.is_authenticated():
        networks = Network.objects.filter(user=request.user)
    else:
        networks = []
    return render_to_response('pdep.html', {'networks': networks}, context_instance=RequestContext(request))

@login_required
def start(request):
    """
    A view called when a user wants to begin a new Pdep Network calculation. This
    view creates a new Network and redirects the user to the main page for that
    network.
    """
    # Create and save a new Network
    network = Network(title='Untitled Network', user=request.user)
    network.save()
    return HttpResponseRedirect(reverse(networkIndex,args=(network.pk,)))

def networkIndex(request, networkKey):
    """
    A view called when a user wants to see the main page for a Network object
    indicated by `networkKey`.
    """
    networkModel = get_object_or_404(Network, pk=networkKey)
    
    # Get file sizes of files in 
    filesize = {}; modificationTime = {}
    if networkModel.inputFileExists():
        filesize['inputFile'] = '{0:.1f}'.format(os.path.getsize(networkModel.getInputFilename()))
        modificationTime['inputFile'] = time.ctime(os.path.getmtime(networkModel.getInputFilename()))
    if networkModel.outputFileExists():
        filesize['outputFile'] = '{0:.1f}'.format(os.path.getsize(networkModel.getOutputFilename()))
        modificationTime['outputFile'] = time.ctime(os.path.getmtime(networkModel.getOutputFilename()))
    if networkModel.logFileExists():
        filesize['logFile'] = '{0:.1f}'.format(os.path.getsize(networkModel.getLogFilename()))
        modificationTime['logFile'] = time.ctime(os.path.getmtime(networkModel.getLogFilename()))
    if networkModel.surfaceFilePNGExists():
        filesize['surfaceFilePNG'] = '{0:.1f}'.format(os.path.getsize(networkModel.getSurfaceFilenamePNG()))
        modificationTime['surfaceFilePNG'] = time.ctime(os.path.getmtime(networkModel.getSurfaceFilenamePNG()))
    if networkModel.surfaceFilePDFExists():
        filesize['surfaceFilePDF'] = '{0:.1f}'.format(os.path.getsize(networkModel.getSurfaceFilenamePDF()))
        modificationTime['surfaceFilePDF'] = time.ctime(os.path.getmtime(networkModel.getSurfaceFilenamePDF()))
    if networkModel.surfaceFileSVGExists():
        filesize['surfaceFileSVG'] = '{0:.1f}'.format(os.path.getsize(networkModel.getSurfaceFilenameSVG()))
        modificationTime['surfaceFileSVG'] = time.ctime(os.path.getmtime(networkModel.getSurfaceFilenameSVG()))
    
    network = networkModel.load()
        
    # Get species information
    speciesList = []
    if network is not None:
        for spec in network.getAllSpecies():
            speciesType = []
            if spec in network.isomers:
                speciesType.append('isomer')
            print network.reactants
            if any([spec in reactants.species for reactants in network.reactants]):
                speciesType.append('reactant')
            if any([spec in products.species for products in network.products]):
                speciesType.append('product')
            if spec in network.bathGas:
                speciesType.append('bath gas')
            print repr(spec)
            collision = 'yes' if spec.transportData is not None else ''
            conformer = 'yes' if spec.conformer is not None else ''
            thermo = 'yes' if spec.conformer is not None or spec.thermo is not None else ''
            speciesList.append((spec.label, getStructureMarkup(spec), ', '.join(speciesType), collision, conformer, thermo))
    
    # Get path reaction information
    pathReactionList = []
    if network is not None:
        for rxn in network.pathReactions:
            reactants = ' + '.join([getStructureMarkup(reactant) for reactant in rxn.reactants])
            products = ' + '.join([getStructureMarkup(reactant) for reactant in rxn.products])
            arrow = '&hArr;' if rxn.reversible else '&rarr;'
            conformer = 'yes' if rxn.transitionState.conformer is not None else ''
            kinetics = 'yes' if rxn.kinetics is not None else ''
            pathReactionList.append((reactants, arrow, products, conformer, kinetics))
    
    # Get net reaction information
    netReactionList = []
    if network is not None:
        for rxn in network.netReactions:
            reactants = ' + '.join([getStructureMarkup(reactant) for reactant in rxn.reactants])
            products = ' + '.join([getStructureMarkup(reactant) for reactant in rxn.products])
            arrow = '&hArr;' if rxn.reversible else '&rarr;'
            kinetics = 'yes' if rxn.kinetics is not None else ''
            netReactionList.append((reactants, arrow, products, kinetics))
    
    return render_to_response(
        'networkIndex.html', 
        {
            'network': networkModel, 
            'networkKey': networkKey, 
            'speciesList': speciesList, 
            'pathReactionList': pathReactionList, 
            'netReactionList': netReactionList, 
            'filesize': filesize, 
            'modificationTime': modificationTime,
        }, 
        context_instance=RequestContext(request),
    )

def networkEditor(request, networkKey):
    """
    A view called when a user wants to add/edit Network input parameters by
    editing the input file in the broswer
    """
    network = get_object_or_404(Network, pk=networkKey)
    if request.method == 'POST':
        form = EditNetworkForm(request.POST, instance=network)
        if form.is_valid():
            # Save the inputText field contents to the input file
            network.saveInputText()
            # Save the form
            network = form.save()
            # Go back to the network's main page
            return HttpResponseRedirect(reverse(networkIndex,args=(network.pk,)))
    else:
        # Load the text from the input file into the inputText field
        network.loadInputText()
        # Create the form
        form = EditNetworkForm(instance=network)
    return render_to_response('networkEditor.html', {'network': network, 'networkKey': networkKey, 'form': form}, context_instance=RequestContext(request))

def networkUpload(request, networkKey):
    """
    A view called when a user wants to add/edit Network input parameters by
    uploading an input file.
    """
    network = get_object_or_404(Network, pk=networkKey)
    if request.method == 'POST':
        form = UploadNetworkForm(request.POST, request.FILES, instance=network)
        if form.is_valid():
            # Delete the current input file
            network.deleteInputFile()
            # Save the form
            network = form.save()
            # Load the text from the input file into the inputText field
            network.loadInputText()
            # Go back to the network's main page
            return HttpResponseRedirect(reverse(networkIndex,args=(network.pk,)))
    else:
        # Create the form
        form = UploadNetworkForm(instance=network)
    return render_to_response('networkUpload.html', {'network': network, 'networkKey': networkKey, 'form': form}, context_instance=RequestContext(request))

def networkDrawPNG(request, networkKey):
    """
    A view called when a user wants to draw the potential energy surface for
    a given Network in PNG format.
    """
    from rmgpy.cantherm.main import execute
    
    network = get_object_or_404(Network, pk=networkKey)
    
    # Run CanTherm to draw the PES
    execute(
        inputFile = network.getInputFilename(),
        drawFile = network.getSurfaceFilenamePNG(),
    )
    
    # Go back to the network's main page
    return HttpResponseRedirect(reverse(networkIndex,args=(network.pk,)))

def networkDrawPDF(request, networkKey):
    """
    A view called when a user wants to draw the potential energy surface for
    a given Network in PDF format.
    """
    
    network = get_object_or_404(Network, pk=networkKey)
    
    # Run CanTherm to draw the PES
    network.execute(
        outputFile = network.getOutputFilename(),
        drawFile = network.getSurfaceFilenamePDF(),
    )
    
    # Go back to the network's main page
    return HttpResponseRedirect(reverse(networkIndex,args=(network.pk,)))

def networkDrawSVG(request, networkKey):
    """
    A view called when a user wants to draw the potential energy surface for
    a given Network in SVG format.
    """
    from rmgpy.cantherm.main import execute
    
    network = get_object_or_404(Network, pk=networkKey)
    
    # Run CanTherm to draw the PES
    # For some reason SVG drawing seems to be much slower than the other formats
    execute(
        inputFile = network.getInputFilename(),
        drawFile = network.getSurfaceFilenameSVG(),
    )
    
    # Go back to the network's main page
    return HttpResponseRedirect(reverse(networkIndex,args=(network.pk,)))

def networkRun(request, networkKey):
    """
    A view called when a user wants to run CanTherm on the pdep input file for a
    given Network.
    """
    
    network = get_object_or_404(Network, pk=networkKey)
    
    # Run CanTherm! This may take some time...
    network.execute(
        outputFile = network.getOutputFilename(),
        plot = False
    )
    
    # Go back to the network's main page
    return HttpResponseRedirect(reverse(networkIndex,args=(network.pk,)))

def networkSpecies(request, networkKey, species):
    """
    A view called when a user wants to view details for a single species in
    a given reaction network.
    """
    networkModel = get_object_or_404(Network, pk=networkKey)
    network = networkModel.load()
    
    label = species
    for spec in network.getAllSpecies():
        if spec.label == label:
            species = spec
            break
    else:
        raise Http404
    
    structure = getStructureMarkup(species)
    E0 = None
    if species.conformer:
        conformer = species.conformer
        hasTorsions = conformer and any([isinstance(mode, HinderedRotor) for mode in conformer.modes])
        if conformer.E0:
            E0 = '{0:g}'.format(conformer.E0.value_si / 4184.)  # convert to kcal/mol
    
    return render_to_response(
        'networkSpecies.html', 
        {
            'network': networkModel, 
            'networkKey': networkKey, 
            'species': species, 
            'label': label,
            'structure': structure,
            'E0': E0,
            'hasTorsions': hasTorsions,
        }, 
        context_instance=RequestContext(request),
    )

def computeMicrocanonicalRateCoefficients(network, T=1000):
    """
    Compute all of the microcanonical rate coefficients k(E) for the given
    network.
    """
    Elist = network.autoGenerateEnergyGrains(Tmax=2000, grainSize=0.5*4184, Ngrains=250)

    # Determine the values of some counters
    Ngrains = len(Elist)
    Nisom = len(network.isomers)
    Nreac = len(network.reactants)
    Nprod = len(network.products)
    dE = Elist[1] - Elist[0]

    # Get ground-state energies of all configurations
    E0 = network.calculateGroundStateEnergies()
    
    # Get first reactive grain for each isomer
    Ereac = numpy.ones(Nisom, numpy.float64) * 1e20
    for i in range(Nisom):
        for rxn in network.pathReactions:
            if rxn.reactants[0] == network.isomers[i] or rxn.products[0] == network.isomers[i]:
                if rxn.transitionState.conformer.E0.value_si < Ereac[i]:
                    Ereac[i] = rxn.transitionState.conformer.E0.value

    # Shift energy grains such that lowest is zero
    Emin = Elist[0]
    for rxn in network.pathReactions:
        rxn.transitionState.conformer.E0.value -= Emin
    E0 -= Emin
    Ereac -= Emin
    Elist -= Emin

    # Calculate density of states for each isomer and each reactant channel
    # that has the necessary parameters
    densStates0 = network.calculateDensitiesOfStates(Elist, E0)
    Kij, Gnj, Fim = network.calculateMicrocanonicalRates(Elist, densStates0, T=1000)
    
    Elist += Emin
    
    return Kij, Gnj, Fim, Elist, densStates0, Nisom, Nreac, Nprod

def networkPathReaction(request, networkKey, reaction):
    """
    A view called when a user wants to view details for a single path reaction
    in a given reaction network.
    """
    networkModel = get_object_or_404(Network, pk=networkKey)
    network = networkModel.load()
    
    try:
        index = int(reaction)
    except ValueError:
        raise Http404
    try:
        reaction = network.pathReactions[index-1]
    except IndexError:
        raise Http404
    
    reactants = ' + '.join([getStructureMarkup(reactant) for reactant in reaction.reactants])
    products = ' + '.join([getStructureMarkup(product) for product in reaction.products])
    arrow = '&hArr;' if reaction.reversible else '&rarr;'
    
    E0 = '{0:g}'.format(reaction.transitionState.conformer.E0.value_si / 4184.) # convert to kcal/mol
    
    conformer = reaction.transitionState.conformer
    hasTorsions = conformer and any([isinstance(mode, HinderedRotor) for mode in conformer.modes])
    kinetics = reaction.kinetics
    
    Kij, Gnj, Fim, Elist, densStates, Nisom, Nreac, Nprod = computeMicrocanonicalRateCoefficients(network)
    
    if reaction.isIsomerization():
        reac = network.isomers.index(reaction.reactants[0])
        prod = network.isomers.index(reaction.products[0])
        kflist = Kij[prod,reac,:]
        krlist = Kij[reac,prod,:]
    elif reaction.isAssociation():
        if reaction.reactants in network.products:
            reac = network.products.index(reaction.reactants) + Nreac
            prod = network.isomers.index(reaction.products[0])
            kflist = []
            krlist = Gnj[reac,prod,:]
        else:
            reac = network.reactants.index(reaction.reactants)
            prod = network.isomers.index(reaction.products[0])
            kflist = []
            krlist = Gnj[reac,prod,:]
    elif reaction.isDissociation():
        if reaction.products in network.products:
            reac = network.isomers.index(reaction.reactants[0])
            prod = network.products.index(reaction.products) + Nreac
            kflist = Gnj[prod,reac,:]
            krlist = []
        else:
            reac = network.isomers.index(reaction.reactants[0])
            prod = network.reactants.index(reaction.products)
            kflist = Gnj[prod,reac,:]
            krlist = []
        
    microcanonicalRates = {
        'Edata': list(Elist),
        'kfdata': list(kflist),
        'krdata': list(krlist),
    }
    
    return render_to_response(
        'networkPathReaction.html', 
        {
            'network': networkModel, 
            'networkKey': networkKey, 
            'reaction': reaction, 
            'index': index,
            'reactants': reactants,
            'products': products,
            'arrow': arrow,
            'E0': E0,
            'conformer': conformer,
            'hasTorsions': hasTorsions,
            'kinetics': kinetics,
            'microcanonicalRates': microcanonicalRates,
        }, 
        context_instance=RequestContext(request),
    )

def networkNetReaction(request, networkKey, reaction):
    """
    A view called when a user wants to view details for a single net reaction
    in a given reaction network.
    """
    networkModel = get_object_or_404(Network, pk=networkKey)
    network = networkModel.load()
    
    try:
        index = int(reaction)
    except ValueError:
        raise Http404
    try:
        reaction = network.netReactions[index-1]
    except IndexError:
        raise Http404
    
    reactants = ' + '.join([getStructureMarkup(reactant) for reactant in reaction.reactants])
    products = ' + '.join([getStructureMarkup(product) for product in reaction.products])
    arrow = '&hArr;' if reaction.reversible else '&rarr;'
    
    kinetics = reaction.kinetics
    
    return render_to_response(
        'networkNetReaction.html', 
        {
            'network': networkModel, 
            'networkKey': networkKey, 
            'reaction': reaction, 
            'index': index,
            'reactants': reactants,
            'products': products,
            'arrow': arrow,
            'kinetics': kinetics,
        }, 
        context_instance=RequestContext(request),
    )

def networkPlotKinetics(request, networkKey):
    """
    Generate k(T,P) vs. T and k(T,P) vs. P plots for all of the net reactions
    involving a given configuration as the reactant.
    """
    networkModel = get_object_or_404(Network, pk=networkKey)
    network = networkModel.load()
    
    configurations = []
    for isomer in network.isomers:
        configurations.append([isomer])
    configurations.extend(network.reactants)
    #configurations.extend(network.products)
    configurationLabels = []
    for configuration in configurations:
        labels = [spec.label for spec in configuration]
        labels.sort()
        configurationLabels.append(u' + '.join(labels))
    
    source = configurations[0]
    T = 1000
    P = 1e5
    
    if request.method == 'POST':
        form = PlotKineticsForm(configurationLabels, request.POST)
        if form.is_valid():
            source = configurations[configurationLabels.index(form.cleaned_data['reactant'])]
            T = form.cleaned_data['T']
            P = form.cleaned_data['P'] * 1e5
    else:
        form = PlotKineticsForm(configurationLabels)
    
    kineticsSet = {}
    for rxn in network.netReactions:
        if rxn.reactants == source:
            products = u' + '.join([spec.label for spec in rxn.products])
            kineticsSet[products] = rxn.kinetics
    
    return render_to_response(
        'networkPlotKinetics.html', 
        {
            'form': form,
            'network': networkModel, 
            'networkKey': networkKey, 
            'configurations': configurations, 
            'source': source,
            'kineticsSet': kineticsSet,
            'T': T,
            'P': P,
        }, 
        context_instance=RequestContext(request),
    )

def networkPlotMicro(request, networkKey):
    """
    A view for showing plots of items that are functions of energy, i.e.
    densities of states rho(E) and microcanonical rate coefficients k(E).
    """
    networkModel = get_object_or_404(Network, pk=networkKey)
    network = networkModel.load()
    
    Kij, Gnj, Fim, Elist, densStates, Nisom, Nreac, Nprod = computeMicrocanonicalRateCoefficients(network)
    
    densityOfStatesData = []
    for i, species in enumerate(network.isomers):
        densityOfStatesData.append({
            'label': species.label,
            'Edata': list(Elist),
            'rhodata': list(densStates[i,:]),
        })
    for n, reactants in enumerate(network.reactants):
        densityOfStatesData.append({
            'label': ' + '.join([species.label for species in reactants]),
            'Edata': list(Elist),
            'rhodata': list(densStates[n+Nisom,:]),
        })
    
    microKineticsData = []
    for reaction in network.pathReactions:
        
        reactants = ' + '.join([reactant.label for reactant in reaction.reactants])
        arrow = '='
        products = ' + '.join([product.label for product in reaction.products])
        
        if reaction.isIsomerization():
            if reaction.reactants[0] in network.isomers and reaction.products[0] in network.isomers:
                reac = network.isomers.index(reaction.reactants[0])
                prod = network.isomers.index(reaction.products[0])
                kflist = Kij[prod,reac,:]
                krlist = Kij[reac,prod,:]
            elif reaction.reactants[0] in network.isomers and reaction.products in network.products:
                reac = network.isomers.index(reaction.reactants[0])
                prod = network.products.index(reaction.products) + Nreac
                kflist = Gnj[prod,reac,:]
                krlist = []
            elif reaction.reactants in network.products and reaction.products[0] in network.isomers:
                reac = network.products.index(reaction.reactants) + Nreac
                prod = network.isomers.index(reaction.products[0])
                kflist = []
                krlist = Gnj[reac,prod,:]
        elif reaction.isAssociation():
            if reaction.reactants in network.products:
                reac = network.products.index(reaction.reactants) + Nreac
                prod = network.isomers.index(reaction.products[0])
                kflist = []
                krlist = Gnj[reac,prod,:]
            else:
                reac = network.reactants.index(reaction.reactants)
                prod = network.isomers.index(reaction.products[0])
                kflist = []
                krlist = Gnj[reac,prod,:]
        elif reaction.isDissociation():
            if reaction.products in network.products:
                reac = network.isomers.index(reaction.reactants[0])
                prod = network.products.index(reaction.products) + Nreac
                kflist = Gnj[prod,reac,:]
                krlist = []
            else:
                reac = network.isomers.index(reaction.reactants[0])
                prod = network.reactants.index(reaction.products)
                kflist = Gnj[prod,reac,:]
                krlist = []
        
        if len(kflist) > 0:
            microKineticsData.append({
                'label': '{0} {1} {2}'.format(reactants, arrow, products),
                'Edata': list(Elist),
                'kdata': list(kflist),
            })
        if len(krlist) > 0:
            microKineticsData.append({
                'label': '{0} {1} {2}'.format(products, arrow, reactants),
                'Edata': list(Elist),
                'kdata': list(krlist),
            })
    
    return render_to_response(
        'networkPlotMicro.html', 
        {
            'network': networkModel, 
            'networkKey': networkKey, 
            'densityOfStatesData': densityOfStatesData,
            'microKineticsData': microKineticsData,
        }, 
        context_instance=RequestContext(request),
    )
