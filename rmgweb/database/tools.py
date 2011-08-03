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

"""
This module contains additional classes and functions used by the database
app that don't belong to any other module.
"""

import socket

from rmgpy.kinetics import Arrhenius
from rmgpy.molecule import Molecule
from rmgpy.species import Species
from rmgpy.reaction import Reaction
from rmgpy.data.base import Entry
from rmgpy.data.kinetics import TemplateReaction, DepositoryReaction
from rmgweb.main.tools import *

################################################################################

def generateSpeciesThermo(species, database):
    """
    Generate the thermodynamics data for a given :class:`Species` object
    `species` using the provided `database`.
    """
    
    thermoData = None
    
    species.generateResonanceIsomers()
    for molecule in species.molecule:
        thermoData0 = database.thermo.getThermoData(molecule)
        if thermoData is None or thermoData0.getEnthalpy(298) < thermoData.getEnthalpy(298):
            thermoData = thermoData0
            
    species.thermo = thermoData
        
################################################################################

def generateReactions(database, reactants, products=None):
    """
    Generate the reactions (and associated kinetics) for a given set of
    `reactants` and an optional set of `products`. A list of reactions is
    returned, with a reaction for each matching kinetics entry in any part of
    the database. This means that the same reaction may appear multiple times
    with different kinetics in the output. If the RMG-Java server is running,
    this function will also query it for reactions and kinetics.
    """
    
    # get RMG-py reactions
    reactionList = []
    reactionList.extend(database.kinetics.generateReactionsFromLibraries(reactants, products))
    reactionList.extend(database.kinetics.generateReactionsFromFamilies(reactants, products))
    if len(reactants) == 1:
        # if only one reactant, react it with itself bimolecularly, with RMG-py
        # the java version already does this (it includes A+A reactions when you react A)
        reactants2 = [reactants[0], reactants[0]]
        reactionList.extend(database.kinetics.generateReactionsFromLibraries(reactants2, products))
        reactionList.extend(database.kinetics.generateReactionsFromFamilies(reactants2, products))
    
    # get RMG-py kinetics
    reactionList0 = reactionList; reactionList = []
    for reaction in reactionList0:
        # If the reaction already has kinetics (e.g. from a library),
        # assume the kinetics are satisfactory
        if reaction.kinetics is not None:
            reactionList.append(reaction)
        else:
            # Set the reaction kinetics
            # Only reactions from families should be missing kinetics
            assert isinstance(reaction, TemplateReaction)
            # Get all of the kinetics for the reaction
            kineticsList = reaction.family.getKinetics(reaction, template=reaction.template, degeneracy=reaction.degeneracy, returnAllKinetics=True)
            if reaction.family.ownReverse and hasattr(reaction,'reverse'):
                kineticsListReverse = reaction.family.getKinetics(reaction, template=reaction.template, degeneracy=reaction.degeneracy, returnAllKinetics=True)
                for kinetics, source, entry, isForward in kineticsListReverse:
                    for kinetics0, source0, entry0, isForward0 in kineticsList:
                        if source0 is not None and source is not None and entry0 is entry and isForward != isForward0:
                            # We already have this estimate from the forward direction, so don't duplicate it in the results
                            break
                    else:
                        kineticsList.append([kinetics, source, entry, not isForward])
                # We're done with the "reverse" attribute, so delete it to save a bit of memory
                delattr(reaction,'reverse')
            # Make a new reaction object for each kinetics result
            for kinetics, source, entry, isForward in kineticsList:
                if isForward:
                    reactant_species = reaction.reactants[:]
                    product_species = reaction.products[:]
                else:
                    reactant_species = reaction.products[:]
                    product_species = reaction.reactants[:]
                if source is not None:
                    rxn = DepositoryReaction(
                        reactants = reactant_species,
                        products = product_species,
                        kinetics = kinetics,
                        #degeneracy = reaction.degeneracy,
                        thirdBody = reaction.thirdBody,
                        reversible = reaction.reversible,
                        depository = source,
                        family = reaction.family,
                        entry = entry,
                    )
                else:
                    rxn = TemplateReaction(
                        reactants = reactant_species,
                        products = product_species,
                        kinetics = kinetics,
                        #degeneracy = reaction.degeneracy,
                        thirdBody = reaction.thirdBody,
                        reversible = reaction.reversible,
                        family = reaction.family,
                    )
                reactionList.append(rxn)
    
    # get RMG-java reactions
    rmgJavaReactionList = getRMGJavaKinetics(reactants, products)
    
    return reactionList, rmgJavaReactionList
    
################################################################################

def reactionHasReactants(reaction, reactants):
    """
    Return ``True`` if the given `reaction` has all of the specified
    `reactants` (and no others), or ``False if not.
    """
    if len(reactants) == len(reaction.products) == 1:
        if reaction.products[0].isIsomorphic(reactants[0]): 
            return False
    elif len(reactants) == len(reaction.products) == 2:
        if reaction.products[0].isIsomorphic(reactants[0]) and reaction.products[1].isIsomorphic(reactants[1]):
            return False
        elif reaction.products[0].isIsomorphic(reactants[1]) and reaction.products[1].isIsomorphic(reactants[0]):
            return False
    elif len(reactants) == 1 and len(reaction.products) == 2:
        if reaction.products[0].isIsomorphic(reactants[0]) and reaction.products[1].isIsomorphic(reactants[0]):
            return False
    return True

def getRMGJavaKineticsFromReaction(reaction):
    """
    Get the kinetics for the given `reaction` (with reactants and products as :class:`Species`)
    
    Returns a copy of the reaction, with kinetics estimated by Java.
    """
    reactantList = [species.molecule[0] for species in reaction.reactants]
    productList = [species.molecule[0] for species in reaction.products]
    reactionList = getRMGJavaKinetics(reactantList, productList)
    #assert len(reactionList) == 1
    if len(reactionList) > 1:
        print "WARNING - RMG-Java identified {0} reactions that match {1!s} instead of 1".format(len(reactionList),reaction)
        reactionList[0].kinetics.comment += "\nWARNING - RMG-Java identified {0} reactions that match this. These kinetics are just from one of them.".format(len(reactionList))
    if len(reactionList) == 0:
        print "WARNING - RMG-Java could not find the reaction {0!s}".format(reaction)
        return None
    return reactionList[0]
    
    
def getRMGJavaKinetics(reactantList, productList=None):
    """
    Get the kinetics for the given `reaction` as estimated by RMG-Java. The
    reactants and products of the given reaction should be :class:`Molecule`
    objects.
    
    This is done by querying a socket running RMG-Java as a service. We
    construct the input file for a PopulateReactions job, pass that as input
    to the RMG-Java service, then parse the output to find the kinetics of
    the reaction we are interested in.
    """
    
    def formSpecies(species):
        """
        This function takes a species string from RMG-Java containing both name
        and adjlist and returns them separately.
        """
        lines = species.split("\n")
        species_name = lines[0]
        adjlist = "\n".join(lines[1:])
        return species_name, adjlist

    def cleanResponse(response):
        """
        This function cleans up response from PopulateReactions server and gives a
        species dictionary and reactions list.
        """
    
        # Split species dictionary from reactions list
        response = response.split("\n\n\n")
        species_list = response[0].split("\n\n")
        reactions = response[1].split("\n\n")
        reactions = reactions[1]
    
        # split species into adjacency lists with names
        species_dict = [formSpecies(item) for item in species_list]
    
        # split reactions into list of single line reactions
        reactions_list = reactions.split("\n")
    
        return species_dict, reactions_list
    
    def searchReaction(reactionline, reactantNames, productNames):
        """
        Reads reaction line and returns True if reaction occurs:
        reactant1 + reactant2 --> product1 + product2
        
        Finds both bimolecular and unimolecular reactions for only 1 reactant input, or only 1 product.
        (reactants and products could be in either order 1,2 or 2,1)
        """
        lines = reactionline.split("\t")
        reaction_string = lines[0]
        reactants, products = reaction_string.split(" --> ")
        reactants = reactants.split(' + ')
        products = products.split(' + ')
        
        reactantsMatch = len(reactantNames) == 0
        if len(reactantNames) == len(reactants):
            reactantsMatch = sorted(reactants) == sorted(reactantNames)
        elif len(reactantNames) == 1 and len(reactants) > 1:
            reactantsMatch = all([r == reactantNames[0] for r in reactants])
            
        productsMatch = len(productNames) == 0
        if len(productNames) == len(products):
            productsMatch = sorted(products) == sorted(productNames)
        elif len(productNames) == 1 and len(products) > 1:
            productsMatch = all([p == productNames[0] for p in products])

        return (reactantsMatch and productsMatch)
    
    def extractKinetics(reactionline):
        """
        Takes a reaction line from RMG and creates Arrhenius object from
        the kinetic data, as well as extracts names of reactants, products and comments.
    
        Units from RMG-Java are in cm3, mol, s.
        Reference Temperature T0 = 1 K.
        """
        lines = reactionline.split("\t")
    
        reaction_string = lines[0]
        reactants, products = reaction_string.split(" --> ")
        reactants = reactants.split(" + ")
        products = products.split(" + ")
    
        kinetics = Arrhenius(
            A = (float(lines[1]),"cm**3/mol/s"),
            n = float(lines[2]),
            Ea = (float(lines[3]),"kcal/mol"),
            T0 = (1,"K"),
        )
    
        comments = "\t".join(lines[4:])
        kinetics.comment = "Estimated by RMG-Java:\n"+comments
        entry = Entry(longDesc=comments)
    
        return reactants, products, kinetics, entry
    
    def identifySpecies(species_dict, molecule):
        """
        Given a species_dict list and the species adjacency list, identifies
        whether species is found in the list and returns its name if found.
        """
        resonance_isomers = molecule.generateResonanceIsomers()
        for name, adjlist in species_dict:
            listmolecule = Molecule().fromAdjacencyList(adjlist)
            for isomer in resonance_isomers:
                if isomer.isIsomorphic(listmolecule):
                    return name
        return False

    productList = productList or []
    reactionList = []

    # First send search request to PopulateReactions server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(10)
    try:
        client_socket.connect(("localhost", 5000))
    except IOError:
        print 'Unable to query RMG-Java for kinetics. (Is the RMG-Java server running?)'
        return reactionList
    
    # Generate species list for Java request
    popreactants = ''
    added_reactants = set()
    for index, reactant in enumerate(reactantList):
        reactant.clearLabeledAtoms()
        for r in added_reactants:
            if r.isIsomorphic(reactant):
                break # already added this reactant
        else: # exhausted the added_reactants list without finding duplicate and breaking
            added_reactants.add(reactant)
            popreactants += 'reactant{0:d} (molecule/cm3) 1\n{1}\n\n'.format(index+1, reactant.toAdjacencyList())
    popreactants += 'END\n'
    
    # Send request to server
    print "SENDING REQUEST FOR RMG-JAVA SEARCH TO SERVER"
    client_socket.sendall(popreactants)
    partial_response = client_socket.recv(512)
    response = partial_response
    while partial_response:
        partial_response = client_socket.recv(512)
        response += partial_response
    client_socket.close()
    print "FINISHED REQUEST. CLOSED CONNECTION TO SERVER"

    # Clean response from server
    species_dict, reactions_list = cleanResponse(response)

    # Name the species in reaction
    reactantNames = []
    for reactant in reactantList:
        reactantNames.append(identifySpecies(species_dict, reactant))
    productNames = []
    for product in productList:
        productNames.append(identifySpecies(species_dict, product))
        # identifySpecies(species_dict, product) returns "False" if it can't find product
        if not identifySpecies(species_dict, product):
            print "Could not find this requested product in the species dictionary from RMG-Java:"
            print str(product)
    
    species_dict = dict([(key, Molecule().fromAdjacencyList(value)) for key, value in species_dict])
    
    # Both products were actually found in species dictionary or were blank
    if all(productNames):

        # Constants for all entries
        degeneracy = 1
        source = 'RMG-Java'

        # Search for da Reactions
        print 'Searching output for desired reaction...\n'
        for reactionline in reactions_list:
            if reactionline.strip().startswith('DUP'):
                print "WARNING - DUPLICATE REACTION KINETICS ARE NOT BEING SUMMED"
                # if set, the `reaction` variable should still point to the reaction from the previous reactionline iteration
                if reaction:
                    reaction.kinetics.comment += "\nWARNING - DUPLICATE REACTION KINETICS IDENTIFIED BUT NOT SUMMED"
                continue # to next reaction line.

            reaction = None
            # Search for both forward and backward reactions
            indicator1 = searchReaction(reactionline, reactantNames, productNames)
            indicator2 = searchReaction(reactionline, productNames, reactantNames)
            if indicator1 == True or indicator2 == True:
                print 'Found a matching reaction:'
                print reactionline
                reactants, products, kinetics, entry = extractKinetics(reactionline)
                reaction = Reaction(
                    reactants = [species_dict[reactant] for reactant in reactants],
                    products = [species_dict[product] for product in products],
                    kinetics = kinetics,
                    degeneracy = degeneracy,
                )
                reactionList.append(reaction)
    
    # Return the reactions as containing Species objects, not Molecule objects
    for reaction in reactionList:
        reaction.reactants = [Species(label=reactant.toSMILES(), molecule=[reactant]) for reactant in reaction.reactants]
        reaction.products = [Species(label=product.toSMILES(), molecule=[product]) for product in reaction.products]
    
    return reactionList
