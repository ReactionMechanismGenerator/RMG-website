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

def searchreaction(reactionline, reactant1, reactant2, product1, product2):
    """
    Reads reaction line and returns True if reaction occurs:
    reactant1 + reactant2 --> product1 + product2
    
    Finds both bimolecular and unimolecular reactions for only 1 reactant input, or only 1 product 
    """

    lines = reactionline.split("\t")

    reaction_string = lines[0]
    reactants, products = reaction_string.split(" --> ")

    if reactants.find(reactant1) == -1 or reactants.find(reactant2) == -1 or products.find(product1) == -1 or products.find(product2) == -1:
        return False
    else:
        return True

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
    

def getRMGJavaKinetics(reactant1, reactant2='', product1='', product2=''):
    """
    Get the kinetics for the given `reaction` as estimated by RMG-Java. The
    reactants and products of the given reaction should be :class:`Molecule`
    objects.
    
    This is done by querying a socket running RMG-Java as a service. We
    construct the input file for a PopulateReactions job, pass that as input
    to the RMG-Java service, then parse the output to find the kinetics of
    the reaction we are interested in.
    """
    
    kineticsDataList = []

    # First send search request to PopulateReactions server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(10)
    client_socket.connect(("localhost", 5000))
        
    # Generate species list for Java request
    header1 = 'reactant1 (molecule/cm3) 1\n'
    popreactants = header1 + reactant1 + '\n\n'
    if reactant2 != '':
        header2 = 'reactant2 (molecule/cm3) 1\n'
        popreactants = popreactants + header2 + reactant2 + '\n\n'
    popreactants = popreactants + 'END' +'\n'

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
    reactant1_name = species_dict[0][0]

    reactant2_name = ''
    if reactant2 != '':
        reactant2_name = species_dict[1][0]
        # BIMOLECULAR

    product1_name = ''
    if product1 != '':
        product1_name = identifyspecies(species_dict, product1)

    product2_name = ''
    if product2 != '':
        product2_name = identifyspecies(species_dict, product2)


    # Both products were actually found in species dictionary or were blank
    if product1_name != False and product2_name != False:

        # Constants for all entries
        degeneracy = 1
        source = 'RMG-Java'

        # Search for da Reactions
        print 'SEARCHING FOR REACTIONS...\n'
        for reactionline in reactions_list:
            print reactionline + '\n'
            # Search for both forward and backward reactions
            indicator1 = searchreaction(reactionline, reactant1_name, reactant2_name, product1_name, product2_name)
            indicator2 = searchreaction(reactionline, product1_name, product2_name, reactant1_name, reactant2_name)

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
