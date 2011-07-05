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
    return True   

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
        
        Finds both bimolecular and unimolecular reactions for only 1 reactant input, or only 1 product 
        """
        lines = reactionline.split("\t")
        reaction_string = lines[0]
        reactants, products = reaction_string.split(" --> ")
        return not (
            any([reactants.find(reactant) == -1 for reactant in reactantNames]) or 
            any([products.find(product) == -1 for product in productNames])
        )
    
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
        entry = Entry(longDesc=comments)
    
        return reactants, products, kinetics, entry
    
    def identifySpecies(species_dict, molecule):
        """
        Given a species_dict list and the species adjacency list, identifies
        whether species is found in the list and returns its name if found.
        """
        for name, adjlist in species_dict:
            listmolecule = Molecule().fromAdjacencyList(adjlist)
            if molecule.isIsomorphic(listmolecule):
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
    
    species_dict = dict([(key, Molecule().fromAdjacencyList(value)) for key, value in species_dict])
    
    # Both products were actually found in species dictionary or were blank
    if all(productNames):

        # Constants for all entries
        degeneracy = 1
        source = 'RMG-Java'

        # Search for da Reactions
        print 'SEARCHING FOR REACTIONS...\n'
        for reactionline in reactions_list:
            print reactionline + '\n'
            # Search for both forward and backward reactions
            indicator1 = searchReaction(reactionline, reactantNames, productNames)
            indicator2 = searchReaction(reactionline, productNames, reactantNames)
            if indicator1 == True or indicator2 == True:
                print 'FOUND A REACTION!'
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
