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
import time

import numpy as np
import rmgpy.constants as constants
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from rmgpy.statmech import *


from rmgweb.main.tools import *
from rmgweb.pdep.models import *
from rmgweb.pdep.forms import *

################################################################################


def index(request):
    """
    The Pressure Dependent Networks homepage.
    """
    if request.user.is_authenticated:
        networks = Network.objects.filter(user=request.user)
    else:
        networks = []
    return render(request, 'pdep.html', {'networks': networks})


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
    return HttpResponseRedirect(reverse('pdep:network-index', args=(network.pk,)))


def networkIndex(request, networkKey):
    """
    A view called when a user wants to see the main page for a Network object
    indicated by `networkKey`.
    """
    network_model = get_object_or_404(Network, pk=networkKey)

    # Get file sizes of files in
    file_size = {}
    modification_time = {}
    if network_model.inputFileExists():
        file_size['inputFile'] = '{0:.1f}'.format(os.path.getsize(network_model.getInputFilename()))
        modification_time['inputFile'] = time.ctime(os.path.getmtime(network_model.getInputFilename()))
    if network_model.outputFileExists():
        file_size['outputFile'] = '{0:.1f}'.format(os.path.getsize(network_model.getOutputFilename()))
        modification_time['outputFile'] = time.ctime(os.path.getmtime(network_model.getOutputFilename()))
    if network_model.logFileExists():
        file_size['logFile'] = '{0:.1f}'.format(os.path.getsize(network_model.getLogFilename()))
        modification_time['logFile'] = time.ctime(os.path.getmtime(network_model.getLogFilename()))
    if network_model.surfaceFilePNGExists():
        file_size['surfaceFilePNG'] = '{0:.1f}'.format(os.path.getsize(network_model.getSurfaceFilenamePNG()))
        modification_time['surfaceFilePNG'] = time.ctime(os.path.getmtime(network_model.getSurfaceFilenamePNG()))
    if network_model.surfaceFilePDFExists():
        file_size['surfaceFilePDF'] = '{0:.1f}'.format(os.path.getsize(network_model.getSurfaceFilenamePDF()))
        modification_time['surfaceFilePDF'] = time.ctime(os.path.getmtime(network_model.getSurfaceFilenamePDF()))
    if network_model.surfaceFileSVGExists():
        file_size['surfaceFileSVG'] = '{0:.1f}'.format(os.path.getsize(network_model.getSurfaceFilenameSVG()))
        modification_time['surfaceFileSVG'] = time.ctime(os.path.getmtime(network_model.getSurfaceFilenameSVG()))

    network = network_model.load()

    # Get species information
    spc_list = []
    if network is not None:
        for spec in network.get_all_species():
            speciesType = []
            if spec in network.isomers:
                speciesType.append('isomer')
            if any([spec in reactants.species for reactants in network.reactants]):
                speciesType.append('reactant')
            if any([spec in products.species for products in network.products]):
                speciesType.append('product')
            if spec in network.bath_gas:
                speciesType.append('bath gas')
            collision = 'yes' if spec.transport_data is not None else ''
            conformer = 'yes' if spec.conformer is not None else ''
            thermo = 'yes' if spec.conformer is not None or spec.thermo is not None else ''
            spc_list.append((spec.label, getStructureMarkup(spec), ', '.join(speciesType), collision, conformer, thermo))

    # Get path reaction information
    path_rxn_list = []
    if network is not None:
        for rxn in network.path_reactions:
            reactants = ' + '.join([getStructureMarkup(reactant) for reactant in rxn.reactants])
            products = ' + '.join([getStructureMarkup(reactant) for reactant in rxn.products])
            arrow = '&hArr;' if rxn.reversible else '&rarr;'
            conformer = 'yes' if rxn.transition_state.conformer is not None else ''
            kinetics = 'yes' if rxn.kinetics is not None else ''
            path_rxn_list.append((reactants, arrow, products, conformer, kinetics))

    # Get net reaction information
    net_rxn_list = []
    if network is not None:
        for rxn in network.net_reactions:
            reactants = ' + '.join([getStructureMarkup(reactant) for reactant in rxn.reactants])
            products = ' + '.join([getStructureMarkup(reactant) for reactant in rxn.products])
            arrow = '&hArr;' if rxn.reversible else '&rarr;'
            kinetics = 'yes' if rxn.kinetics is not None else ''
            net_rxn_list.append((reactants, arrow, products, kinetics))

    return render(request, 'networkIndex.html',
                  {'network': network_model,
                   'networkKey': networkKey,
                   'speciesList': spc_list,
                   'pathReactionList': path_rxn_list,
                   'netReactionList': net_rxn_list,
                   'filesize': file_size,
                   'modificationTime': modification_time,
                   })


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
            return HttpResponseRedirect(reverse('pdep:network-index', args=(network.pk,)))
    else:
        # Load the text from the input file into the inputText field
        network.loadInputText()
        # Create the form
        form = EditNetworkForm(instance=network)
    return render(request, 'networkEditor.html', {'network': network, 'networkKey': networkKey, 'form': form})


def networkDelete(request, networkKey):
    """
    A view called when a user wants to delete a network with the specified networkKey.
    """
    network = get_object_or_404(Network, pk=networkKey)
    network.delete()
    return HttpResponseRedirect(reverse('pdep:index'))


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
            return HttpResponseRedirect(reverse('pdep:network-index', args=(network.pk,)))
    else:
        # Create the form
        form = UploadNetworkForm(instance=network)
    return render(request, 'networkUpload.html', {'network': network, 'networkKey': networkKey, 'form': form})


def networkDrawPNG(request, networkKey):
    """
    A view called when a user wants to draw the potential energy surface for
    a given Network in PNG format.
    """

    network_model = get_object_or_404(Network, pk=networkKey)

    network_model.load()
    # Run Arkane! This may take some time...
    network_model.pdep.execute(
        output_file=network_model.getOutputFilename(),
        plot=False,
        file_format='png'
    )

    # Go back to the network's main page
    return HttpResponseRedirect(reverse('pdep:network-index', args=(network_model.pk,)))


def networkDrawPDF(request, networkKey):
    """
    A view called when a user wants to draw the potential energy surface for
    a given Network in PDF format.
    """

    network_model = get_object_or_404(Network, pk=networkKey)

    network_model.load()
    # Run Arkane! This may take some time...
    network_model.pdep.execute(
        output_file=network_model.getOutputFilename(),
        plot=False,
        file_format='pdf'
    )

    # Go back to the network's main page
    return HttpResponseRedirect(reverse('pdep:network-index', args=(network_model.pk,)))


def networkDrawSVG(request, networkKey):
    """
    A view called when a user wants to draw the potential energy surface for
    a given Network in SVG format.
    """
    network_model = get_object_or_404(Network, pk=networkKey)

    network_model.load()
    # Run Arkane! This may take some time...
    network_model.pdep.execute(
        output_file=network_model.getOutputFilename(),
        plot=False,
        file_format='svg'
    )

    # Go back to the network's main page
    return HttpResponseRedirect(reverse('pdep:network-index', args=(network_model.pk,)))


def networkRun(request, networkKey):
    """
    A view called when a user wants to run Arkane on the pdep input file for a
    given Network.
    """
    network_model = get_object_or_404(Network, pk=networkKey)

    network_model.load()
    # Run Arkane! This may take some time...
    network_model.pdep.execute(
        output_file=network_model.getOutputFilename(),
        plot=False,
        file_format='png'
    )

    # Go back to the network's main page
    return HttpResponseRedirect(reverse('pdep:network-index', args=(network_model.pk,)))


def networkSpecies(request, networkKey, species):
    """
    A view called when a user wants to view details for a single species in
    a given reaction network.
    """
    network_model = get_object_or_404(Network, pk=networkKey)
    network = network_model.load()

    label = species
    for spec in network.get_all_species():
        if spec.label == label:
            species = spec
            break
    else:
        raise Http404

    structure = getStructureMarkup(species)
    E0 = None
    if species.conformer:
        conformer = species.conformer
        has_torsions = conformer and any([isinstance(mode, HinderedRotor) for mode in conformer.modes])
        if conformer.E0:
            E0 = '{0:g}'.format(conformer.E0.value_si / 4184.)  # convert to kcal/mol

    return render(request, 'networkSpecies.html',
                  {'network': network_model,
                   'networkKey': networkKey,
                   'species': species,
                   'label': label,
                   'structure': structure,
                   'E0': E0,
                   'hasTorsions': has_torsions,
                   })


def computeMicrocanonicalRateCoefficients(network, T=1000):
    """
    Compute all of the microcanonical rate coefficients k(E) for the given
    network.
    """

    network.T = T
    if network.e_list is None:
        e_list = network.select_energy_grains(T=2000, grain_size=0.5*4184, grain_count=250)
        network.e_list = e_list
    else:
        e_list = network.e_list
    # Determine the values of some counters
    # n_grains = len(Elist)
    n_isom = len(network.isomers)
    n_reac = len(network.reactants)
    n_prod = len(network.products)
#    dE = Elist[1] - Elist[0]
#
#    # Get ground-state energies of all configurations
#    E0 = network.calculateGroundStateEnergies()
#
#    # Get first reactive grain for each isomer
#    e_reac = np.ones(Nisom, np.float64) * 1e20
#    for i in range(Nisom):
#        for rxn in network.path_reactions:
#            if rxn.reactants[0] == network.isomers[i] or rxn.products[0] == network.isomers[i]:
#                if rxn.transition_state.conformer.E0.value_si < Ereac[i]:
#                    Ereac[i] = rxn.transition_state.conformer.E0.value
#
#    # Shift energy grains such that lowest is zero
#    Emin = Elist[0]
#    for rxn in network.path_reactions:
#        rxn.transition_state.conformer.E0.value -= Emin
#    E0 -= Emin
#    Ereac -= Emin
#    Elist -= Emin

    # Choose the angular momenta to use to compute k(T,P) values at this temperature
    # (This only applies if the J-rotor is adiabatic
    if not network.active_j_rotor:
        j_list = network.j_list = np.arange(0, 20, 1, np.int)
        n_j = network.n_j = len(j_list)
    else:
        j_list = network.j_list = np.array([0], np.int)
        n_j = network.n_j = 1

    if not hasattr(network, 'densStates'):
        # Calculate density of states for each isomer and each reactant channel
        # that has the necessary parameters
        network.calculate_densities_of_states()
        # Map the densities of states onto this set of energies
        # Also shift each density of states to a common zero of energy
        network.map_densities_of_states()

        # Use free energy to determine equilibrium ratios of each isomer and product channel
        network.calculate_equilibrium_ratios()
        network.calculate_microcanonical_rates()

    # Rescale densities of states such that, when they are integrated
    # using the Boltzmann factor as a weighting factor, the result is unity
    for i in range(n_isom + n_reac):
        Q = 0.0
        for s in range(n_j):
            Q += np.sum(network.dens_states[i, :, s] * (2 * j_list[s]+1) * np.exp(-e_list / constants.R / T))
        network.dens_states[i, :, :] /= Q

    Kij = network.Kij
    Gnj = network.Gnj
    Fim = network.Fim
    dens_states_0 = network.dens_states
    # Elist += Emin

    return Kij, Gnj, Fim, e_list, dens_states_0, n_isom, n_reac, n_prod


def networkPathReaction(request, networkKey, reaction):
    """
    A view called when a user wants to view details for a single path reaction
    in a given reaction network.
    """
    network_model = get_object_or_404(Network, pk=networkKey)
    network = network_model.load()

    try:
        index = int(reaction)
    except ValueError:
        raise Http404
    try:
        reaction = network.path_reactions[index-1]
    except IndexError:
        raise Http404

    e0 = '{0:g}'.format(reaction.transition_state.conformer.E0.value_si / 4184.)  # convert to kcal/mol

    conformer = reaction.transition_state.conformer
    has_torsions = conformer and any([isinstance(mode, HinderedRotor) for mode in conformer.modes])
    kinetics = reaction.kinetics

    Kij, Gnj, Fim, e_list, dens_states, n_isom, n_reac, n_prod = computeMicrocanonicalRateCoefficients(network)

    reactants = [reactant.species for reactant in network.reactants]
    products = [product.species for product in network.products]
    isomers = [isomer.species[0] for isomer in network.isomers]

    if reaction.is_isomerization():
        reac = isomers.index(reaction.reactants[0])
        prod = isomers.index(reaction.products[0])
        kf_list = Kij[prod, reac, :]
        kr_list = Kij[reac, prod, :]
    elif reaction.is_association():
        if reaction.reactants in products:
            reac = products.index(reaction.reactants) + n_reac
            prod = isomers.index(reaction.products[0])
            kf_list = []
            kr_list = Gnj[reac, prod, :]
        else:
            reac = reactants.index(reaction.reactants)
            prod = isomers.index(reaction.products[0])
            kf_list = []
            kr_list = Gnj[reac, prod, :]
    elif reaction.is_dissociation():
        if reaction.products in products:
            reac = isomers.index(reaction.reactants[0])
            prod = products.index(reaction.products) + n_reac
            kf_list = Gnj[prod, reac, :]
            kr_list = []
        else:
            reac = isomers.index(reaction.reactants[0])
            prod = reactants.index(reaction.products)
            kf_list = Gnj[prod, reac, :]
            kr_list = []

    microcanonical_rates = {
        'Edata': list(e_list),
        'kfdata': list(kf_list),
        'krdata': list(kr_list),
    }

    reactants_render = ' + '.join([getStructureMarkup(reactant) for reactant in reaction.reactants])
    products_render = ' + '.join([getStructureMarkup(product) for product in reaction.products])
    arrow = '&hArr;' if reaction.reversible else '&rarr;'

    return render(request, 'networkPathReaction.html',
                  {'network': network_model,
                   'networkKey': networkKey,
                   'reaction': reaction,
                   'index': index,
                   'reactants': reactants_render,
                   'products': products_render,
                   'arrow': arrow,
                   'E0': e0,
                   'conformer': conformer,
                   'hasTorsions': has_torsions,
                   'kinetics': kinetics,
                   'microcanonicalRates': microcanonical_rates,
                   })


def networkNetReaction(request, networkKey, reaction):
    """
    A view called when a user wants to view details for a single net reaction
    in a given reaction network.
    """
    network_model = get_object_or_404(Network, pk=networkKey)
    network = network_model.load()

    try:
        index = int(reaction)
    except ValueError:
        raise Http404
    try:
        reaction = network.net_reactions[index-1]
    except IndexError:
        raise Http404

    reactants = ' + '.join([getStructureMarkup(reactant) for reactant in reaction.reactants])
    products = ' + '.join([getStructureMarkup(product) for product in reaction.products])
    arrow = '&hArr;' if reaction.reversible else '&rarr;'

    kinetics = reaction.kinetics

    return render(request, 'networkNetReaction.html',
                  {'network': network_model,
                   'networkKey': networkKey,
                   'reaction': reaction,
                   'index': index,
                   'reactants': reactants,
                   'products': products,
                   'arrow': arrow,
                   'kinetics': kinetics,
                   })


def networkPlotKinetics(request, networkKey):
    """
    Generate k(T,P) vs. T and k(T,P) vs. P plots for all of the net reactions
    involving a given configuration as the reactant.
    """
    network_model = get_object_or_404(Network, pk=networkKey)
    network = network_model.load()

    configurations = []
    for isomer in network.isomers:
        configurations.append([isomer])
    configurations.extend(network.reactants)
    # configurations.extend(network.products)
    config_labels = []
    for configuration in config_labels:
        labels = [spec.label for spec in configuration]
        labels.sort()
        config_labels.append(u' + '.join(labels))

    source = configurations[0]
    T = 1000
    P = 1e5

    if request.method == 'POST':
        form = PlotKineticsForm(config_labels, request.POST)
        if form.is_valid():
            source = configurations[config_labels.index(form.cleaned_data['reactant'])]
            T = form.cleaned_data['T']
            P = form.cleaned_data['P'] * 1e5
    else:
        form = PlotKineticsForm(config_labels)

    kineticsSet = {}
    for rxn in network.net_reactions:
        if rxn.reactants == source:
            products = u' + '.join([spec.label for spec in rxn.products])
            kineticsSet[products] = rxn.kinetics

    return render(request, 'networkPlotKinetics.html',
                  {'form': form,
                   'network': network_model,
                   'networkKey': networkKey,
                   'configurations': configurations,
                   'source': source,
                   'kineticsSet': kineticsSet,
                   'T': T,
                   'P': P,
                   })


def networkPlotMicro(request, networkKey):
    """
    A view for showing plots of items that are functions of energy, i.e.
    densities of states rho(E) and microcanonical rate coefficients k(E).
    """
    network_model = get_object_or_404(Network, pk=networkKey)
    network = network_model.load()

    Kij, Gnj, Fim, e_list, dens_states, n_isom, n_reac, n_prod = computeMicrocanonicalRateCoefficients(network)

    dens_states_data = []

    reactants = [reactant.species for reactant in network.reactants]
    products = [product.species for product in network.products]
    isomers = [isomer.species[0] for isomer in network.isomers]

    for i, species in enumerate(isomers):
        dens_states_data.append({
            'label': species.label,
            'Edata': list(e_list),
            'rhodata': list(dens_states[i, :]),
        })
    for n, spc_list in enumerate(reactants):
        dens_states_data.append({
            'label': ' + '.join([species.label for species in spc_list]),
            'Edata': list(e_list),
            'rhodata': list(dens_states[n + n_isom, :]),
        })

    micro_kinetics_data = []
    for reaction in network.path_reactions:

        reactants_render = ' + '.join([reactant.label for reactant in reaction.reactants])
        arrow = '='
        products_render = ' + '.join([product.label for product in reaction.products])

        if reaction.is_isomerization():
            if reaction.reactants[0] in isomers and reaction.products[0] in isomers:
                reac = isomers.index(reaction.reactants[0])
                prod = isomers.index(reaction.products[0])
                kf_list = Kij[prod, reac, :]
                kr_list = Kij[reac, prod, :]
            elif reaction.reactants[0] in isomers and reaction.products in products:
                reac = isomers.index(reaction.reactants[0])
                prod = products.index(reaction.products) + n_reac
                kf_list = Gnj[prod, reac, :]
                kr_list = []
            elif reaction.reactants in products and reaction.products[0] in isomers:
                reac = products.index(reaction.reactants) + n_reac
                prod = isomers.index(reaction.products[0])
                kf_list = []
                kr_list = Gnj[reac, prod, :]
        elif reaction.is_association():
            if reaction.reactants in products:
                reac = products.index(reaction.reactants) + n_reac
                prod = isomers.index(reaction.products[0])
                kf_list = []
                kr_list = Gnj[reac, prod, :]
            else:
                reac = reactants.index(reaction.reactants)
                prod = isomers.index(reaction.products[0])
                kf_list = []
                kr_list = Gnj[reac, prod, :]
        elif reaction.is_dissociation():
            if reaction.products in products:
                reac = isomers.index(reaction.reactants[0])
                prod = products.index(reaction.products) + n_reac
                kf_list = Gnj[prod, reac, :]
                kr_list = []
            else:
                reac = isomers.index(reaction.reactants[0])
                prod = reactants.index(reaction.products)
                kf_list = Gnj[prod, reac, :]
                kr_list = []

        if len(kf_list) > 0:
            micro_kinetics_data.append({
                'label': '{0} {1} {2}'.format(reactants_render, arrow, products_render),
                'Edata': list(e_list),
                'kdata': list(kf_list),
            })
        if len(kr_list) > 0:
            micro_kinetics_data.append({
                'label': '{0} {1} {2}'.format(products_render, arrow, reactants_render),
                'Edata': list(e_list),
                'kdata': list(kr_list),
            })

    return render(request, 'networkPlotMicro.html',
                  {'network': network_model,
                   'networkKey': networkKey,
                   'densityOfStatesData': dens_states_data,
                   'microKineticsData': micro_kinetics_data,
                   })
