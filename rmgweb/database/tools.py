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
from rmgpy.data.base import Entry
from rmgweb.main.tools import *

################################################################################

def cleanresponse(response):
    """
    This function cleans up response from PopulateReactions server and gives a
    species dictionary and reactions list.
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

def searchreaction(reactionline, reactantNames, productNames):
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

def extractkinetics(reactionline):
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

    KineticsModel = Arrhenius(
        A = (float(lines[1]),"cm**3/mol/s"),
        n = float(lines[2]),
        Ea = (float(lines[3]),"kcal/mol"),
        T0 = (1,"K"),
    )

    comments = "\t".join(lines[4:])
    entry = Entry(longDesc=comments)

    return reactants, products, KineticsModel, entry

def identifyspecies(species_dict, species):
    """
    Given a species_dict list and the species adjacency list, identifies
    whether species is found in the list and returns its name if found.
    """
    molecule = Molecule().fromAdjacencyList(species)
    for name, adjlist in species_dict:
        listmolecule = Molecule().fromAdjacencyList(adjlist)
        if molecule.isIsomorphic(listmolecule) == True:
            return name

    return False

def getspeciesstructure(species_dict, speciesname):
    """
    Given a species_dict list and the name of the species, returns structure of the species.
    Returns blank structure if not found.
    """
    structure = ''
    for name, adjlist in species_dict:
        if speciesname == name:
            molecule = Molecule().fromAdjacencyList(str(adjlist.replace(';', '\n')))
            structure = getStructureMarkup(molecule)
            return structure

    return structure
    

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
    
    productList = productList or []
    kineticsDataList = []

    # First send search request to PopulateReactions server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(10)
    client_socket.connect(("localhost", 5000))
        
    # Generate species list for Java request
    popreactants = ''
    for index, reactant in enumerate(reactantList):
        reactant.clearLabeledAtoms()
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
    species_dict, reactions_list = cleanresponse(response)

    # Name the species in reaction
    reactantNames = []
    for index, reactant in enumerate(reactantList):
        reactantNames.append(species_dict[index][0])
    productNames = []
    for index, product in enumerate(productList):
        productNames.append(identifyspecies(species_dict, product))
    
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
            indicator1 = searchreaction(reactionline, reactantNames, productNames)
            indicator2 = searchreaction(reactionline, productNames, reactantNames)

            if indicator1 == True or indicator2 == True:
                print 'FOUND A REACTION!'
                reactants, products, kineticsModel, entry = extractkinetics(reactionline)
                numReactants = len(reactants)
                numProducts = len(products)
                kineticsParameters = prepareKineticsParameters(kineticsModel, numReactants, degeneracy)

                # draw figures
                reactants_structures = [getspeciesstructure(species_dict, speciesname) for speciesname in reactants]
                products_structures = [getspeciesstructure(species_dict, speciesname) for speciesname in products]
                if numReactants == 2:
                    reactants_fig = ' + '.join(reactants_structures)
                else:
                    reactants_fig = reactants_structures[0]
                if numProducts == 2:
                    products_fig = ' + '.join(products_structures)
                else:
                    products_fig = products_structures[0]

                # Unused vars for render_to_response
                section = ''
                subsection = ''
                databaseName = 'RMG-Java Database'
                reference = ''
                referenceLink = ''
                referenceType = ''
                arrow = '&hArr;'

                #return render_to_response('kineticsEntry.html', {'section': section, 'subsection': subsection, 'databaseName': databaseName, 'entry': entry, 'reactants': reactants_fig, 'arrow': arrow, 'products': products_fig, 'reference': reference, 'referenceLink': referenceLink, 'referenceType': referenceType, 'kineticsParameters': kineticsParameters, 'kineticsModel': kineticsModel}, context_instance=RequestContext(request))
                
                #href = reverse(kineticsJavaEntry, kwargs={'entry': entry,'reactants_fig': reactants_fig, 'products_fig': products_fig, 'kineticsParameters': kineticsParameters, 'kineticsModel': kineticsModel})
                href = 'dummy link'
                kineticsDataList.append([reactants_fig, arrow, products_fig, entry, kineticsParameters, source, href])
    
    return kineticsDataList
