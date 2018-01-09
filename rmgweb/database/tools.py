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
import sys
import os
import rmgweb.settings
import pybel
import openbabel as ob
import xlrd
import itertools


from rmgpy.kinetics import Arrhenius
from rmgpy.molecule.molecule import Molecule
from rmgpy.species import Species
from rmgpy.reaction import Reaction
from rmgpy.data.base import Entry
from rmgpy.data.kinetics import TemplateReaction, DepositoryReaction
from rmgweb.main.tools import *

from rmgpy.data.thermo import ThermoDatabase
from rmgpy.data.kinetics import KineticsDatabase
from rmgpy.data.transport import TransportDatabase
from rmgpy.data.rmg import SolvationDatabase
from rmgpy.data.rmg import RMGDatabase
from rmgpy.data.rmg import StatmechDatabase


class RMGWebDatabase(object):
    """Wrapper class for RMGDatabase that provides loading functionality."""

    def __init__(self):
        self.database = RMGDatabase()
        self.database.kinetics = KineticsDatabase()
        self.database.thermo = ThermoDatabase()
        self.database.transport = TransportDatabase()
        self.database.statmech = StatmechDatabase()
        self.database.solvation = SolvationDatabase()
        self.database.loadForbiddenStructures(os.path.join(rmgweb.settings.DATABASE_PATH, 'forbiddenStructures.py'))
        self.timestamps = {}

    @property
    def kinetics(self):
        """Get the kinetics database."""
        return self.database.kinetics

    @property
    def thermo(self):
        """Get the thermo database."""
        return self.database.thermo

    @property
    def transport(self):
        """Get the transport database."""
        return self.database.transport

    @property
    def statmech(self):
        """Get the statmech database."""
        return self.database.statmech

    @property
    def solvation(self):
        """Get the solvation database."""
        return self.database.solvation

    def reset_timestamp(self, path):
        """
        Reset the files timestamp in the dictionary of timestamps.
        """
        mtime = os.stat(path).st_mtime
        self.timestamps[path] = mtime

    def reset_dir_timestamps(self, dirpath):
        """
        Walk the directory tree from dirpath, calling reset_timestamp(file) on each file.
        """
        print "Resetting 'last loaded' timestamps for {0} in process {1}".format(dirpath, os.getpid())
        for root, dirs, files in os.walk(dirpath):
            for name in files:
                self.reset_timestamp(os.path.join(root, name))

    def is_file_modified(self, path):
        """
        Return True if the file at `path` has been modified since `reset_timestamp(path)` was last called.
        """
        # If path doesn't denote a file and were previously
        # tracking it, then it has been removed or the file type
        # has changed, so return True.
        if not os.path.isfile(path):
            return path in self.timestamps

        # If path wasn't being tracked then it's new, so return True
        elif path not in self.timestamps:
            return True

        # Force restart when modification time has changed, even
        # if time now older, as that could indicate older file
        # has been restored.
        elif os.stat(path).st_mtime != self.timestamps[path]:
            return True

        # All the checks have been passed, so the file was not modified
        else:
            return False

    def is_dir_modified(self, dirpath):
        """
        Returns True if anything in the directory at dirpath has been modified since reset_dir_timestamps(dirpath).
        """
        to_check = set([path for path in self.timestamps if path.startswith(dirpath)])
        for root, dirs, files in os.walk(dirpath):
            for name in files:
                path = os.path.join(root, name)
                if self.is_file_modified(path):
                    return True
                to_check.remove(path)
        # If there's anything left in to_check, it's probably now gone and this will return True:
        for path in to_check:
            if self.is_file_modified(path):
                return True
        # Passed all tests.
        return False

    ################################################################################

    def load(self, component='', section=''):
        """
        Load the requested `component` of the RMG database if modified since last loaded.
        """
        if component in ['thermo', '']:
            if section in ['depository', '']:
                dirpath = os.path.join(rmgweb.settings.DATABASE_PATH, 'thermo', 'depository')
                if self.is_dir_modified(dirpath):
                    self.database.thermo.loadDepository(dirpath)
                    self.reset_dir_timestamps(dirpath)
            if section in ['libraries', '']:
                dirpath = os.path.join(rmgweb.settings.DATABASE_PATH, 'thermo', 'libraries')
                if self.is_dir_modified(dirpath):
                    self.database.thermo.loadLibraries(dirpath)
                    # put them in our preferred order, so that when we look up thermo in order to estimate kinetics,
                    # we use our favorite values first.
                    preferred_order = [
                        'primaryThermoLibrary',
                        'DFT_QCI_thermo',
                        'GRI-Mech3.0',
                        'CBS_QB3_1dHR',
                        'KlippensteinH2O2',
                    ]
                    new_order = [i for i in preferred_order if i in self.database.thermo.libraryOrder]
                    for i in self.database.thermo.libraryOrder:
                        if i not in new_order:
                            new_order.append(i)
                    self.database.thermo.libraryOrder = new_order
                    self.reset_dir_timestamps(dirpath)
            if section in ['groups', '']:
                dirpath = os.path.join(rmgweb.settings.DATABASE_PATH, 'thermo', 'groups')
                if self.is_dir_modified(dirpath):
                    self.database.thermo.loadGroups(dirpath)
                    self.reset_dir_timestamps(dirpath)

        if component in ['transport', '']:
            if section in ['libraries', '']:
                dirpath = os.path.join(rmgweb.settings.DATABASE_PATH, 'transport', 'libraries')
                if self.is_dir_modified(dirpath):
                    self.database.transport.loadLibraries(dirpath)
                    self.reset_dir_timestamps(dirpath)
            if section in ['groups', '']:
                dirpath = os.path.join(rmgweb.settings.DATABASE_PATH, 'transport', 'groups')
                if self.is_dir_modified(dirpath):
                    self.database.transport.loadGroups(dirpath)
                    self.reset_dir_timestamps(dirpath)

        if component in ['solvation', '']:
            dirpath = os.path.join(rmgweb.settings.DATABASE_PATH, 'solvation')
            if self.is_dir_modified(dirpath):
                self.database.solvation.load(dirpath)
                self.reset_dir_timestamps(dirpath)

        if component in ['kinetics', '']:
            if section in ['libraries', '']:
                dirpath = os.path.join(rmgweb.settings.DATABASE_PATH, 'kinetics', 'libraries')
                if self.is_dir_modified(dirpath):
                    self.database.kinetics.loadLibraries(dirpath)
                    self.reset_dir_timestamps(dirpath)
            if section in ['families', '']:
                dirpath = os.path.join(rmgweb.settings.DATABASE_PATH, 'kinetics', 'families')
                if self.is_dir_modified(dirpath):
                    self.database.kinetics.loadFamilies(dirpath, families='all', depositories='all')
                    self.reset_dir_timestamps(dirpath)

                    # Make sure to load the entire thermo database prior to adding training values to the rules
                    self.load('thermo', '')
                    for family in self.database.kinetics.families.values():
                        oldentries = len(family.rules.entries)
                        family.addKineticsRulesFromTrainingSet(thermoDatabase=self.database.thermo)
                        newentries = len(family.rules.entries)
                        if newentries != oldentries:
                            print '{0} new entries added to {1} family after adding rules from training set.'.format(
                                newentries - oldentries, family.label)
                        # Filling in rate rules in kinetics families by averaging...
                        family.fillKineticsRulesByAveragingUp()

        if component in ['statmech', '']:
            dirpath = os.path.join(rmgweb.settings.DATABASE_PATH, 'statmech')
            if self.is_dir_modified(dirpath):
                self.database.statmech.load(dirpath)
                self.reset_dir_timestamps(dirpath)

    def get_transport_database(self, section, subsection):
        """
        Return the component of the transport database corresponding to the
        given `section` and `subsection`. If either of these is invalid, a
        :class:`ValueError` is raised.
        """
        try:
            if section == 'libraries':
                db = self.database.transport.libraries[subsection]
            elif section == 'groups':
                db = self.database.transport.groups[subsection]
            else:
                raise ValueError('Invalid value "%s" for section parameter.' % section)
        except KeyError:
            raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)

        return db

    def get_solvation_database(self, section, subsection):
        """
        Return the component of the solvation database corresponding to the
        given `section` and `subsection`. If either of these is invalid, a
        :class:`ValueError` is raised.
        """
        try:
            if section == '':
                db = self.database.solvation  # return general SolvationDatabase
            elif section == 'libraries':
                db = self.database.solvation.libraries[subsection]
            elif section == 'groups':
                db = self.database.solvation.groups[subsection]
            else:
                raise ValueError('Invalid value "%s" for section parameter.' % section)
        except KeyError:
            raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)

        return db

    def get_statmech_database(self, section, subsection):
        """
        Return the component of the statmech database corresponding to the
        given `section` and `subsection`. If either of these is invalid, a
        :class:`ValueError` is raised.
        """
        try:
            if section == 'depository':
                db = self.database.statmech.depository[subsection]
            elif section == 'libraries':
                db = self.database.statmech.libraries[subsection]
            elif section == 'groups':
                db = self.database.statmech.groups[subsection]
            else:
                raise ValueError('Invalid value "%s" for section parameter.' % section)
        except KeyError:
            raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)

        return db

    def get_thermo_database(self, section, subsection):
        """
        Return the component of the thermodynamics database corresponding to the
        given `section` and `subsection`. If either of these is invalid, a
        :class:`ValueError` is raised.
        """
        try:
            if section == 'depository':
                db = self.database.thermo.depository[subsection]
            elif section == 'libraries':
                db = self.database.thermo.libraries[subsection]
            elif section == 'groups':
                db = self.database.thermo.groups[subsection]
            else:
                raise ValueError('Invalid value "%s" for section parameter.' % section)
        except KeyError:
            raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)

        return db

    def get_kinetics_database(self, section, subsection):
        """
        Return the component of the kinetics database corresponding to the
        given `section` and `subsection`. If either of these is invalid, a
        :class:`ValueError` is raised.
        """
        db = None
        try:
            if section == 'libraries':
                db = self.database.kinetics.libraries[subsection]
            elif section == 'families':
                subsection = subsection.split('/')
                if subsection[0] != '' and len(subsection) == 2:
                    family = self.database.kinetics.families[subsection[0]]
                    if subsection[1] == 'groups':
                        db = family.groups
                    elif subsection[1] == 'rules':
                        db = family.rules
                    else:
                        label = '{0}/{1}'.format(family.label, subsection[1])
                        db = (d for d in family.depositories if d.label == label).next()
            else:
                raise ValueError('Invalid value "%s" for section parameter.' % section)
        except (KeyError, StopIteration):
            raise ValueError('Invalid value "%s" for subsection parameter.' % subsection)
        return db

################################################################################

def generateSpeciesThermo(species, database):
    """
    Generate the thermodynamics data for a given :class:`Species` object
    `species` using the provided `database`.
    """
    species.generate_resonance_structures()
    species.thermo = database.thermo.getThermoData(species)
        
################################################################################

def generateReactions(database, reactants, products=None, only_families=None, resonance=True):
    """
    Generate the reactions (and associated kinetics) for a given set of
    `reactants` and an optional set of `products`. A list of reactions is
    returned, with a reaction for each matching kinetics entry in any part of
    the database. This means that the same reaction may appear multiple times
    with different kinetics in the output.

    If `only_families` is a list of strings, only those labeled families are 
    used: no libraries and no RMG-Java kinetics are returned.
    """
    from rmgpy.rmg.model import getFamilyLibraryObject
    # get RMG-py reactions
    reactionList = database.kinetics.generate_reactions(reactants, products, only_families=only_families, resonance=resonance)
    if len(reactants) == 1:
        # if only one reactant, react it with itself bimolecularly, with RMG-py
        # the java version already does this (it includes A+A reactions when you react A)
        reactants2 = [reactants[0], reactants[0]]
        reactionList.extend(database.kinetics.generate_reactions(reactants2, products, only_families=only_families, resonance=resonance))
    
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
            family = getFamilyLibraryObject(reaction.family)
            kineticsList = family.getKinetics(reaction, templateLabels=reaction.template, degeneracy=reaction.degeneracy, returnAllKinetics=True)
            if family.ownReverse and hasattr(reaction,'reverse'):
                kineticsListReverse = family.getKinetics(reaction.reverse, templateLabels=reaction.reverse.template, degeneracy=reaction.reverse.degeneracy, returnAllKinetics=True)
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
                
                if source == 'rate rules' or source == 'group additivity':
                    rxn = TemplateReaction(
                        reactants = reactant_species,
                        products = product_species,
                        kinetics = kinetics,
                        degeneracy = reaction.degeneracy,
                        reversible = reaction.reversible,
                        family = reaction.family,
                        estimator = source,
                        template = reaction.template,
                    )
                else:
                    rxn = DepositoryReaction(
                        reactants = reactant_species,
                        products = product_species,
                        kinetics = kinetics,
                        degeneracy = reaction.degeneracy,
                        reversible = reaction.reversible,
                        depository = source,
                        family = reaction.family,
                        entry = entry,
                    )                    
                    
                reactionList.append(rxn)

    return reactionList
    
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
        
        if len(reactants) == 1:
            Aunits = "s^-1"
        elif len(reactants) == 2:
            Aunits = "cm**3/mol/s"
        else:   # 3 reactants?
            Aunits = "cm**6/(mol^2*s)"
            
        kinetics = Arrhenius(
            A = (float(lines[1]), Aunits),
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
        resonance_isomers = molecule.generate_resonance_structures()
        for name, adjlist in species_dict:
            listmolecule = Molecule().fromAdjacencyList(adjlist, saturateH=True)
            for isomer in resonance_isomers:
                if isomer.isIsomorphic(listmolecule):
                    return name
        return False

    productList = productList or []
    reactionList = []

    # Generate species list for Java request
    popreactants = ''
    added_reactants = set()
    for index, reactant in enumerate(reactantList):
        assert isinstance(reactant, Molecule)
        reactant.clearLabeledAtoms()
        for r in added_reactants:
            if r.isIsomorphic(reactant):
                break # already added this reactant
        else: # exhausted the added_reactants list without finding duplicate and breaking
            added_reactants.add(reactant)
            popreactants += 'reactant{0:d} (molecule/cm3) 1\n{1}\n\n'.format(index+1, reactant.toAdjacencyList(removeLonePairs=True))
    popreactants += 'END\n'
    
    
    # First send search request to PopulateReactions server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(10)
    try:
        client_socket.connect(("localhost", 5000))
    except IOError:
        print >> sys.stderr, 'Unable to query RMG-Java for kinetics. (Is the RMG-Java server running?)'
        sys.stderr.flush()
        return reactionList
    
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
    try:
        species_dict, reactions_list = cleanResponse(response)
    except:
        # Return an empty reaction list if an error occurred on the java server side,
        # instead of having the website crash.
        print "AN ERROR OCCURRED IN THE JAVA SERVER."
        print response
        return []

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
    
    species_dict = dict([(key, Molecule().fromAdjacencyList(value,saturateH=True)) for key, value in species_dict])
    
    # Both products were actually found in species dictionary or were blank
    reaction = None
    if all(productNames):

        # Constants for all entries
        degeneracy = 1

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
                reaction = DepositoryReaction(
                    reactants = [species_dict[reactant] for reactant in reactants],
                    products = [species_dict[product] for product in products],
                    kinetics = kinetics,
                    degeneracy = degeneracy,
                    entry = entry,
                )

                reactionList.append(reaction)
    
    # Return the reactions as containing Species objects, not Molecule objects
    for reaction in reactionList:
        reaction.reactants = [Species(molecule=[reactant]) for reactant in reaction.reactants]
        reaction.products = [Species(molecule=[product]) for product in reaction.products]
    
    return reactionList

def getAbrahamAB(smiles):

    class functionalgroup():
        """
        functional group definitions and the associated A and B values for the Abraham hydrogen bonding descriptors
        """
        def __init__(self,SMART, name, data):
            self.name = name
            self.smarts = SMART
            self.value = float()
            self.value = data
    
    class query():
        """
        Defines the properties of a molecular query which may be the detergent molecule or dirt molecule
        """
        def __init__(self):
            self.name = str()
            self.smiles = str()
            self.A = float()
            self.B = float()
        
        def MatchPlattsAGroups(self, smiles):
            
            # Load functional group database
            current_dir = os.getcwd()
            filepath = os.path.join(current_dir, 'groups.xls')
            wb = xlrd.open_workbook(filepath)
            wb.sheet_names()
        
            data = wb.sheet_by_name(u'PlattsA')
            col1 = data.col_values(0)
            col2 = data.col_values(1)
            col3 = data.col_values(2)
        
            databaseA = []
            for (SMART, name, A) in zip(col1, col2, col3):
                    databaseA.append(functionalgroup(SMART, name, A))
            
            platts_A = 0
            mol = pybel.readstring("smi", smiles)
            for x in databaseA:
                # Initialize with dummy SMLES to check for validity of real one
                smarts = pybel.Smarts("CC")
                smarts.obsmarts = ob.OBSmartsPattern()
                success = smarts.obsmarts.Init(x.smarts.__str__())
                if success:
                    smarts = pybel.Smarts(x.smarts.__str__())
                else:
                    print "Invalid SMARTS pattern", x.smarts.__str__()
                    break
                matched = smarts.findall(mol)
                x.num = len(matched)
                if (x.num > 0):
                    print "Found group", x.smarts.__str__(), 'named', x.name, 'with contribution', x.value, 'to A', x.num, 'times'
                platts_A += (x.num) * (x.value)
                        
            self.A = platts_A + 0.003
               
        def MatchPlattsBGroups(self, smiles):
            
            # Load functional group database
            current_dir = os.getcwd()
            filepath = os.path.join(current_dir, 'groups.xls')
            wb = xlrd.open_workbook(filepath)
            wb.sheet_names()
        
            data = wb.sheet_by_name(u'PlattsB')
            col1 = data.col_values(0)
            col2 = data.col_values(1)
            col3 = data.col_values(2)
        
            databaseB = []
            for (SMART, name, B) in zip(col1, col2, col3):
                    databaseB.append(functionalgroup(SMART, name, B))
            
            platts_B = 0
            mol = pybel.readstring("smi", smiles)
            for x in databaseB:
                # Initialize with dummy SMLES to check for validity of real one
                smarts = pybel.Smarts("CC")
                smarts.obsmarts = ob.OBSmartsPattern()
                success = smarts.obsmarts.Init(x.smarts.__str__())
                if success:
                    smarts = pybel.Smarts(x.smarts.__str__())
                else:
                    print "Invalid SMARTS pattern", x.smarts.__str__()
                    break
                matched = smarts.findall(mol)
                x.num = len(matched)
                if (x.num > 0):
                    print "Found group", x.smarts.__str__(), 'named', x.name, 'with contribution', x.value, 'to B', x.num, 'times'
                platts_B += (x.num) * (x.value)
            
            self.B = platts_B + 0.071 

    molecule = query()
    molecule.smiles = smiles
    molecule.MatchPlattsAGroups(molecule.smiles)
    molecule.MatchPlattsBGroups(molecule.smiles)
    
    return molecule.A, molecule.B


################################################################################

# Initialize module level database instance
database = RMGWebDatabase()

################################################################################
