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

from rmgpy.quantity import *
import os.path

from django.db import models
from django import forms
from django.utils.text import capfirst
from django.utils.deconstruct import deconstructible
from rmgpy.molecule.molecule import Molecule
from rmgpy.rmg.main import RMG
from rmgweb.main.tools import *
from rmgweb.database.tools import getLibraryLists

import rmgweb.settings as settings

@deconstructible
class uploadTo(object):
    """
    Factory class for path generation.
    """
    
    def __init__(self, subpath=''):
        self.subpath = subpath
    
    def __call__(self, instance, filename):
        return os.path.join(instance.folder, self.subpath)

class Chemkin(models.Model):
    """
    A Django model of a chemkin file.
    """

    def __init__(self, *args, **kwargs):
        super(Chemkin, self).__init__(*args, **kwargs)
        self.folder = os.path.join('rmg', 'tools', 'chemkin')
        self.path = os.path.join(settings.MEDIA_ROOT, self.folder)

    ChemkinFile = models.FileField(upload_to=uploadTo(os.path.join('chemkin', 'chem.inp')), verbose_name='Chemkin File')
    DictionaryFile = models.FileField(upload_to=uploadTo('RMG_Dictionary.txt'), verbose_name='RMG Dictionary', blank=True, null=True)
    Foreign = models.BooleanField(verbose_name="Not an RMG-generated Chemkin file")
    
    def createOutput(self):
        """
        Generate output html file from the path containing chemkin and dictionary files.
        """
        from rmgpy.chemkin import saveHTMLFile
        if self.Foreign:
            # Chemkin file was not from RMG, do not parse the comments when visualizing the file.
            saveHTMLFile(self.path, readComments = False)
        else:
            saveHTMLFile(self.path)

    def createDir(self):
        """
        Create the directory (and any other needed parent directories) that
        the Network uses for storing files.
        """
        try:
            os.makedirs(os.path.join(self.path,'chemkin'))
            os.makedirs(os.path.join(self.path,'species'))
        except OSError:
            # Fail silently on any OS errors
            pass

    def deleteDir(self):
        """
        Clean up everything by deleting the directory
        """
        import shutil
        try:
            shutil.rmtree(self.path)
        except OSError:
            pass
        
    def getKinetics(self):
        """
        Extracts the kinetic data from the chemkin file for plotting purposes.
        """
        from rmgpy.chemkin import loadChemkinFile
        from rmgpy.kinetics import ArrheniusEP, Chebyshev
        from rmgpy.reaction import Reaction
        from rmgpy.data.base import Entry
        
        kineticsDataList = []    
        chemkinPath= os.path.join(self.path, 'chemkin','chem.inp')
        dictionaryPath = os.path.join(self.path, 'RMG_Dictionary.txt' )
        if self.Foreign:
            readComments = False
        else:
            readComments = True
        if os.path.exists(dictionaryPath):
            speciesList, reactionList = loadChemkinFile(chemkinPath, dictionaryPath, readComments=readComments)
        else:
            speciesList, reactionList = loadChemkinFile(chemkinPath, readComments=readComments)
            
        for reaction in reactionList:            
            # If the kinetics are ArrheniusEP, replace them with Arrhenius
            if isinstance(reaction.kinetics, ArrheniusEP):
                reaction.kinetics = reaction.kinetics.toArrhenius(reaction.getEnthalpyOfReaction(298))

            if os.path.exists(dictionaryPath):
                reactants = ' + '.join([moleculeToInfo(reactant) for reactant in reaction.reactants])
                arrow = '&hArr;' if reaction.reversible else '&rarr;'
                products = ' + '.join([moleculeToInfo(product) for product in reaction.products])
                href = reaction.getURL()
            else:
                reactants = ' + '.join([reactant.label for reactant in reaction.reactants])
                arrow = '&hArr;' if reaction.reversible else '&rarr;'
                products = ' + '.join([product.label for product in reaction.products])
                href = ''
                
            source = str(reaction).replace('<=>','=')
            entry = Entry()   
            entry.result = reactionList.index(reaction)+1
            forwardKinetics = reaction.kinetics     
            forward = True
            chemkin = reaction.toChemkin(speciesList)
            
            reverseKinetics = reaction.generateReverseRateCoefficient()
            reverseKinetics.comment = 'Fitted reverse reaction. ' + reaction.kinetics.comment
            
            rev_reaction = Reaction(reactants = reaction.products, products = reaction.reactants, kinetics = reverseKinetics)
            chemkin_rev = rev_reaction.toChemkin(speciesList)
            
            kineticsDataList.append([reactants, arrow, products, entry, forwardKinetics, source, href, forward, chemkin, reverseKinetics, chemkin_rev])

        return kineticsDataList
    
    def createJavaKineticsLibrary(self):
        """
        Generates java reaction library files from your chemkin file.
        """
        from rmgpy.chemkin import loadChemkinFile, saveJavaKineticsLibrary
        
        chemkinPath = os.path.join(self.path, 'chemkin','chem.inp')
        dictionaryPath = os.path.join(self.path, 'RMG_Dictionary.txt' )
        speciesList, reactionList = loadChemkinFile(chemkinPath, dictionaryPath)
        saveJavaKineticsLibrary(self.path, speciesList, reactionList)
        return


class Diff(models.Model):
    """
    A Django model for storing 2 RMG models and comparing them.
    """
    def __init__(self, *args, **kwargs):
        super(Diff, self).__init__(*args, **kwargs)
        self.folder = os.path.join('rmg', 'tools', 'compare')
        self.path = os.path.join(settings.MEDIA_ROOT, self.folder)
        self.chemkin1 = os.path.join(self.path, 'chem1.inp')
        self.dict1 = os.path.join(self.path, 'RMG_Dictionary1.txt')
        self.chemkin2 = os.path.join(self.path, 'chem2.inp')
        self.dict2 = os.path.join(self.path, 'RMG_Dictionary2.txt')

    ChemkinFile1 = models.FileField(upload_to=uploadTo('chem1.inp'), verbose_name='Model 1: Chemkin File')
    DictionaryFile1 = models.FileField(upload_to=uploadTo('RMG_Dictionary1.txt'),verbose_name='Model 1: RMG Dictionary')    
    Foreign1 = models.BooleanField(verbose_name="Model 1 not an RMG-generated Chemkin file")
    ChemkinFile2 = models.FileField(upload_to=uploadTo('chem2.inp'), verbose_name='Model 2: Chemkin File')
    DictionaryFile2 = models.FileField(upload_to=uploadTo('RMG_Dictionary2.txt'),verbose_name='Model 2: RMG Dictionary')    
    Foreign2 = models.BooleanField(verbose_name="Model 2 not an RMG-generated Chemkin file")

    def createOutput(self):
        """
        Generate output html file from the path containing chemkin and dictionary files.
        """
        import rmgpy.tools.diff_models as diff_models

        kwargs = {
                'web':True,
                'wd': self.path,
                }
        diff_models.execute(
                    self.chemkin1, self.dict1, None,
                    self.chemkin2, self.dict2, None,
                    **kwargs
                    )

    def merge(self):
        """
        Merge the two models together to generate both chemkin and dictionary files.
        """

        import rmgpy.tools.merge_models as merge_models
        import sys

        inputModelFiles = []
        inputModelFiles.append((self.chemkin1, self.dict1, None))
        inputModelFiles.append((self.chemkin2, self.dict2, None))

        kwargs = {
            'wd': self.path,
            'transport': False,
        }
        
        logfile = os.path.join(self.path,'merging_log.txt')
        
        # Save stdout to logfile which the user can download
        with open(logfile, 'w') as f:
            stdout_orig = sys.stdout
            sys.stdout = f
            
            merge_models.execute(
                        inputModelFiles,
                        **kwargs
                        )
            
            sys.stdout = stdout_orig
        
    def createDir(self):
        """
        Create the directory (and any other needed parent directories) that
        the Network uses for storing files.
        """
        try:         
            os.makedirs(os.path.join(self.path,'species1'))
            os.makedirs(os.path.join(self.path,'species2'))
        except OSError:
            # Fail silently on any OS errors
            pass

    def deleteDir(self):
        """
        Clean up everything by deleting the directory
        """
        import shutil
        try:
            shutil.rmtree(self.path)
        except OSError:
            pass

class AdjlistConversion(models.Model):
    """
    A Django model for converting new style adjlists to old style ones.
    """
    def __init__(self, *args, **kwargs):
        super(AdjlistConversion, self).__init__(*args, **kwargs)
        self.folder = os.path.join('rmg', 'tools', 'adjlistConversion')
        self.path = os.path.join(settings.MEDIA_ROOT, self.folder)
        self.dictionary = os.path.join(self.path, 'species_dictionary.txt')

    DictionaryFile = models.FileField(upload_to=uploadTo('species_dictionary.txt'), verbose_name='RMG Dictionary')

    def createOutput(self):
        """
        Generate output html file from the path containing chemkin and dictionary files.
        """
        
        speciesList = []    
        with open(self.dictionary, 'r') as f:
            adjlist = ''
            for line in f:
                if line.strip() == '' and adjlist.strip() != '':
                    # Finish this adjacency list
                    species = Species().fromAdjacencyList(adjlist)
                    speciesList.append(species)
                    adjlist = ''
                else:
                    if "InChI" in line:
                        line = line.split()[0] + '\n'
                    if '//' in line:
                        index = line.index('//')
                        line = line[0:index]
                    adjlist += line
                
        with open(os.path.join(self.path,'RMG_Dictionary.txt'), 'w') as f:
            for spec in speciesList:
                try:
                    f.write(spec.molecule[0].toAdjacencyList(label=spec.label, removeH=True, oldStyle=True))
                    f.write('\n')
                except:
                    raise Exception('Ran into error saving adjlist for species {0}. It may not be compatible with old adjacency list format.'.format(spec))
                
    def createDir(self):
        """
        Create the directory (and any other needed parent directories) that
        the Network uses for storing files.
        """
        try:
            os.makedirs(self.path)
        except OSError:
            # Fail silently on any OS errors
            pass
        
    def deleteDir(self):
        """
        Clean up everything by deleting the directory
        """
        import shutil
        try:
            shutil.rmtree(self.path)
        except OSError:
            pass

class FluxDiagram(models.Model):
    """
    A Django model for generating a flux diagram using RMG-Py.
    """
    def __init__(self, *args, **kwargs):
        super(FluxDiagram, self).__init__(*args, **kwargs)
        self.folder = os.path.join('rmg', 'tools', 'flux')
        self.path = os.path.join(settings.MEDIA_ROOT, self.folder)

    InputFile = models.FileField(upload_to=uploadTo('input.py'), verbose_name='RMG Input File')
    ChemkinFile = models.FileField(upload_to=uploadTo('chem.inp'), verbose_name='Chemkin File')
    DictionaryFile = models.FileField(upload_to=uploadTo('species_dictionary.txt'),verbose_name='RMG Dictionary')
    ChemkinOutput = models.FileField(upload_to=uploadTo('chemkin_output.out'), verbose_name='Chemkin Output File (Optional)', blank=True,null=True)
    Java = models.BooleanField(verbose_name="From RMG-Java")
    MaxNodes = models.PositiveIntegerField(default=50, verbose_name='Maximum Nodes')
    MaxEdges = models.PositiveIntegerField(default=50, verbose_name='Maximum Edges')
    TimeStep = models.FloatField(default=1.25, verbose_name='Multiplicative Time Step Factor')
    ConcentrationTolerance = models.FloatField(default=1e-6, verbose_name='Concentration Tolerance')   # The lowest fractional concentration to show (values below this will appear as zero)
    SpeciesRateTolerance = models.FloatField(default=1e-6, verbose_name='Species Rate Tolerance')   # The lowest fractional species rate to show (values below this will appear as zero)

    def createDir(self):
        """
        Create the directory (and any other needed parent directories) that
        the Network uses for storing files.
        """
        try:
            os.makedirs(self.path)
        except OSError:
            # Fail silently on any OS errors
            pass

    def deleteDir(self):
        """
        Clean up everything by deleting the directory
        """
        import shutil
        try:
            shutil.rmtree(self.path)
        except OSError:
            pass


class PopulateReactions(models.Model):
    """
    A Django model for a PopulateReactions input file.
    """
    def __init__(self, *args, **kwargs):
        super(PopulateReactions, self).__init__(*args, **kwargs)
        self.folder = os.path.join('rmg', 'tools', 'populateReactions')
        self.path = os.path.join(settings.MEDIA_ROOT, self.folder)
        self.input = os.path.join(self.path, 'input.txt')

    InputFile = models.FileField(upload_to=uploadTo('input.txt'), verbose_name='Input File')

    def createOutput(self):
        """
        Generate output html file from the path containing chemkin and dictionary files.
        """
        
        import subprocess
        import rmgpy
        command = ('python',
            os.path.join(os.path.dirname(rmgpy.getPath()), 'scripts', 'generateReactions.py'),
            self.input,
            '-q',
        )
        subprocess.check_call(command, cwd=self.path)
        

    def createDir(self):
        """
        Create the directory (and any other needed parent directories) that
        the Network uses for storing files.
        """
        try:
            os.makedirs(os.path.join(self.path))
        except OSError:
            # Fail silently on any OS errors
            pass

    def deleteDir(self):
        """
        Clean up everything by deleting the directory
        """
        import shutil
        try:
            shutil.rmtree(self.path)
        except OSError:
            pass
        
        
        
################################################################################
# INPUT MODEL
################################################################################

from arkane.pdep import PressureDependenceJob
from rmgpy.solver.base import TerminationTime, TerminationConversion
from rmgpy.solver.simple import SimpleReactor
from rmgpy.species import Species        
from rmgpy.molecule import Molecule
from rmgpy.rmg.model import CoreEdgeReactionModel    
from rmgpy.rmg.input import readInputFile
import quantities

temp_units = (('K','K',),('C','C',))
p_units = (('bar','bar',),('torr','torr',),('atm','atm',))
t_units = (('ms','ms',),('s','s',),('hr','hr',))


class Input(models.Model):
    """
    Model for RMG Input Conditions
    """
        
    def __init__(self, *args, **kwargs):
        super(Input, self).__init__(*args, **kwargs)
        self.rmg = RMG()
        self.folder = os.path.join('rmg', 'tools', 'input')
        self.path = os.path.join(settings.MEDIA_ROOT, self.folder)
        self.loadpath = os.path.join(self.path, 'input_upload.py')
        self.savepath = os.path.join(self.path, 'input.py')

    input_upload = models.FileField(upload_to=uploadTo('input_upload.py'), verbose_name='Input File', blank = True)
    
    # Pressure Dependence
    p_methods=(('off','off',),('modified strong collision','Modified Strong Collision',),('reservoir state','Reservoir State',))
    pdep = models.CharField(max_length = 50, default = 'off', choices = p_methods)
    # Advanced Options for PDep
    # Grain Size
    maximumGrainSize = models.FloatField(blank = True, default = 2, null = True)
    grain_units = (('kcal/mol','kcal/mol',),('kJ/mol','kJ/mol',))
    grainsize_units = models.CharField(max_length = 50, default = 'kcal/mol', choices = grain_units)
    minimumNumberOfGrains = models.PositiveIntegerField(blank = True, default = 200, null = True)
    maximumAtoms = models.PositiveIntegerField(blank = True, null = True)
    # P and T Range
    p_low = models.FloatField(blank = True, null = True)
    p_high = models.FloatField(blank = True, null = True)
    prange_units = models.CharField(max_length = 50, default = 'bar', choices=p_units)
    p_interp = models.PositiveIntegerField(blank = True, null = True, default = 5)
    temp_low = models.FloatField(blank = True, null = True)
    temp_high = models.FloatField(blank = True, null = True)
    temprange_units = models.CharField(max_length = 50, default = 'K', choices = temp_units)
    temp_interp = models.PositiveIntegerField(blank = True, null=True, default = 8)
    # Interpolation
    interpolation_choices = (('chebyshev','Chebyshev',),('pdeparrhenius','Pressure Dependent Arrhenius',))
    interpolation = models.CharField(max_length = 50, default = 'chebyshev', choices = interpolation_choices)
    temp_basis = models.PositiveIntegerField(blank = True, default = 6, null = True)
    p_basis = models.PositiveIntegerField(blank = True, default = 4, null = True)

    # Tolerance
    toleranceMoveToCore = models.FloatField(default = 0.1)
    toleranceKeepInEdge= models.FloatField(default = 0.0)
    # Tolerance Advanced Options
    toleranceInterruptSimulation = models.FloatField(default = 1.0)
    maximumEdgeSpecies = models.PositiveIntegerField(default = 100000)
    minCoreSizeForPrune = models.PositiveIntegerField(default = 50)
    minSpeciesExistIterationsForPrune = models.PositiveIntegerField(default = 2)
    filterReactions = models.BooleanField(default = False)
    simulator_atol = models.FloatField(default = 1e-16)
    simulator_rtol = models.FloatField(default = 1e-8)
    simulator_sens_atol = models.FloatField(default = 1e-6)
    simulator_sens_rtol = models.FloatField(default = 1e-4)
    
    # Quantum Calculations
    on_off = (('off','off',),('on','on',))
    quantumCalc = models.CharField(max_length = 50, default = 'off', choices = on_off)
    software_options = (('mopac','MOPAC',),('gaussian','GAUSSIAN',))
    software = models.CharField(max_length = 50, default = 'off', choices = software_options)
    method_options = (('pm3','pm3',),('pm6','pm6',),('pm7','pm7 (MOPAC2012 only)',))
    method = models.CharField(max_length = 50, default = 'off', choices = method_options)
    fileStore = models.CharField(max_length = 100, default = 'QMfiles', blank = True)
    scratchDirectory = models.CharField(max_length = 100, default = 'QMscratch', blank = True)
    onlyCyclics = models.BooleanField(default=True)
    maxRadicalNumber = models.PositiveSmallIntegerField(blank = True, default=0)
    
    # Generated Species Constraints
    speciesConstraints = models.CharField(max_length = 50, default = 'off', choices = on_off)
    allowed_inputSpecies = models.BooleanField(default = False)
    allowed_seedMechanisms = models.BooleanField(default = False)
    allowed_reactionLibraries = models.BooleanField(default = False)
    maximumCarbonAtoms = models.PositiveSmallIntegerField(blank = True, null = True)
    maximumOxygenAtoms = models.PositiveSmallIntegerField(blank = True, null = True)
    maximumNitrogenAtoms = models.PositiveSmallIntegerField(blank = True, null = True)
    maximumSiliconAtoms = models.PositiveSmallIntegerField(blank = True, null = True)
    maximumSulfurAtoms = models.PositiveSmallIntegerField(blank = True, null = True)
    maximumHeavyAtoms = models.PositiveSmallIntegerField(blank = True, null = True)
    maximumRadicalElectrons = models.PositiveSmallIntegerField(blank = True, null = True)
    allowSingletO2 = models.BooleanField(default = False)
    
    # Additional Options
    saveRestartPeriod=models.FloatField(blank = True, null=True)
    restartunits = (('second','seconds'),('hour','hours'),('day','days'),('week','weeks'))
    saveRestartPeriodUnits = models.CharField(max_length = 50, default = 'hour', choices = restartunits)
    generateOutputHTML=models.BooleanField(default = False)
    generatePlots=models.BooleanField(default = False)
    saveSimulationProfiles = models.BooleanField(default = False)
    saveEdgeSpecies = models.BooleanField(default = False)
    verboseComments = models.BooleanField(default = False)

    def createDir(self):
        """
        Create the directory (and any other needed parent directories) that
        the Network uses for storing files.
        """
        try:
            os.makedirs(self.path)
        except OSError:
            # Fail silently on any OS errors
            pass

    def deleteDir(self):
        """
        Clean up everything by deleting the directory
        """
        import shutil
        try:
            shutil.rmtree(self.path)
        except OSError:
            pass
        
    def loadForm(self, path):
        """
        Load input.py file onto form initial data.
        """        
        readInputFile(path, self.rmg)
        
        # Databases
        initial_thermo_libraries = []
        if self.rmg.thermoLibraries:
            for item in self.rmg.thermoLibraries:
                initial_thermo_libraries.append({'thermolib': item})
        
        initial_reaction_libraries = []
        if self.rmg.seedMechanisms:
            for item in self.rmg.seedMechanisms:
                initial_reaction_libraries.append({'reactionlib': item, 'seedmech': True, 'edge': False})
        if self.rmg.reactionLibraries:
            for item, edge in self.rmg.reactionLibraries:
                initial_reaction_libraries.append({'reactionlib': item, 'seedmech': False, 'edge': edge})
        
        # Reactor systems
        initial_reactor_systems = []
        for system in self.rmg.reactionSystems:
            temperature = system.T.getValue()
            temperature_units = system.T.units
            pressure = system.P.getValue()
            pressure_units = system.P.units
            initialMoleFractions = system.initialMoleFractions
            for item in system.termination:
                if isinstance(item, TerminationTime):
                    terminationtime = item.time.getValue()
                    time_units = item.time.units
                else:
                    species = item.species.label
                    conversion = item.conversion
            # Sensitivity
            if system.sensitiveSpecies:
                sensitivity = []
                for item in system.sensitiveSpecies:
                    sensitivity.append(item.label)
                sensitivity = ','.join(sensitivity)
                sensitivityThreshold = system.sensitivityThreshold
            else:
                sensitivity = ''
                sensitivityThreshold = 0.001
            initial_reactor_systems.append({'temperature': temperature, 'temperature_units': temperature_units,
                                            'pressure': pressure, 'pressure_units': pressure_units,
                                            'terminationtime': terminationtime, 'time_units': time_units,
                                            'species': species, 'conversion': conversion,
                                            'sensitivity': sensitivity, 'sensitivityThreshold': sensitivityThreshold})
        
        # Species
        initial_species = []
        for item in self.rmg.initialSpecies:
            name = item.label
            adjlist = item.molecule[0].toAdjacencyList()
            inert = False if item.reactive else True
            spec, isNew = self.rmg.reactionModel.makeNewSpecies(item.molecule[0], label = item.label, reactive = item.reactive)
            molefrac = initialMoleFractions[spec]
            initial_species.append({'name': name, 'adjlist': adjlist, 
                                    'inert': inert, 'molefrac': molefrac})
            
        # Tolerances
        initial = {}
        initial['simulator_atol'] = self.rmg.absoluteTolerance 
        initial['simulator_rtol'] = self.rmg.relativeTolerance 
        initial['simulator_sens_atol'] = self.rmg.sensitivityAbsoluteTolerance 
        initial['simulator_sens_rtol'] = self.rmg.sensitivityRelativeTolerance 
        initial['toleranceKeepInEdge'] = self.rmg.fluxToleranceKeepInEdge 
        initial['toleranceMoveToCore']= self.rmg.fluxToleranceMoveToCore
        initial['toleranceInterruptSimulation'] = self.rmg.fluxToleranceInterrupt
        initial['maximumEdgeSpecies'] = self.rmg.maximumEdgeSpecies 
        initial['minCoreSizeForPrune'] = self.rmg.minCoreSizeForPrune
        initial['minSpeciesExistIterationsForPrune'] = self.rmg.minSpeciesExistIterationsForPrune
        initial['filterReactions'] = self.rmg.filterReactions
                
        # Pressure Dependence
        if self.rmg.pressureDependence:
            # Pressure dependence method
            initial['pdep'] = self.rmg.pressureDependence.method.lower()
            # Process interpolation model
            initial['interpolation'] = self.rmg.pressureDependence.interpolationModel[0].lower()
            if initial['interpolation'] == 'chebyshev':
                initial['temp_basis'] = self.rmg.pressureDependence.interpolationModel[1]
                initial['p_basis'] = self.rmg.pressureDependence.interpolationModel[2]
            # Temperature and pressure ranges
            initial['temp_low'] = self.rmg.pressureDependence.Tmin.getValue()
            initial['temp_high'] = self.rmg.pressureDependence.Tmax.getValue()
            initial['temprange_units'] = self.rmg.pressureDependence.Tmax.units
            initial['temp_interp'] = self.rmg.pressureDependence.Tcount
            initial['p_low'] = self.rmg.pressureDependence.Pmin.getValue()
            initial['p_high'] = self.rmg.pressureDependence.Pmax.getValue()
            initial['prange_units'] = self.rmg.pressureDependence.Pmax.units
            initial['p_interp'] = self.rmg.pressureDependence.Pcount
            # Process grain size and count
            initial['maximumGrainSize'] = self.rmg.pressureDependence.maximumGrainSize.getValue()
            initial['grainsize_units'] = self.rmg.pressureDependence.maximumGrainSize.units
            initial['minimumNumberOfGrains'] = self.rmg.pressureDependence.minimumGrainCount
            
            initial['maximumAtoms'] = self.rmg.pressureDependence.maximumAtoms
        else:
            initial['pdep'] = 'off'    
            
        # Species Constraints
        if self.rmg.speciesConstraints:
            initial['speciesConstraints'] = 'on'
            for key, value in self.rmg.speciesConstraints.items():
                if key == 'allowed':
                    allowed_dict = {'input species':'allowed_inputSpecies', 'reaction libraries':'allowed_reactionLibraries', 'seed mechanisms':'allowed_seedMechanisms'}
                    if isinstance(value,list):
                        for allowed_name in value:
                            field = allowed_dict[allowed_name.lower()]
                            initial[field] = True
                    else:
                        raise Exception("Input File generatedSpeciesConstraints(allowed='[..]'), allowed block must be a list containing either 'reaction libraries', 'seed mechanisms', or 'input species'." )
                else:
                    initial[key] = value
        else:
            initial['speciesConstraints'] = 'off'
        
        # Quantum Calculations
        if self.rmg.quantumMechanics:
            initial['quantumCalc'] = 'on'
            initial['software'] = self.rmg.quantumMechanics.settings.software
            initial['method'] = self.rmg.quantumMechanics.settings.method
            if self.rmg.quantumMechanics.settings.fileStore:
                initial['fileStore'] = os.path.split(self.rmg.quantumMechanics.settings.fileStore)[0]
            else:
                initial['fileStore'] = ''
            if self.rmg.quantumMechanics.settings.scratchDirectory:
                initial['scratchDirectory'] = os.path.split(self.rmg.quantumMechanics.settings.scratchDirectory)[0]
            else:
                initial['scratchDirectory'] = ''
            initial['onlyCyclics'] = self.rmg.quantumMechanics.settings.onlyCyclics
            initial['maxRadicalNumber'] = self.rmg.quantumMechanics.settings.maxRadicalNumber
        else:
            initial['quantumCalc'] = 'off'
        
        # Additional Options
        if self.rmg.saveRestartPeriod:
            initial['saveRestartPeriod'] = self.rmg.saveRestartPeriod.getValue()
            initial['saveRestartPeriodUnits'] = self.rmg.saveRestartPeriod.units
        if self.rmg.generateOutputHTML:
            initial['generateOutputHTML'] = True
        if self.rmg.generatePlots:
            initial['generatePlots'] = True
        if self.rmg.saveSimulationProfiles:
            initial['saveSimulationProfiles'] = True
        if self.rmg.saveEdgeSpecies:
            initial['saveEdgeSpecies'] = True
        if self.rmg.verboseComments:
            initial['verboseComments'] = True
            
        return initial_thermo_libraries, initial_reaction_libraries, initial_reactor_systems, initial_species, initial
        
    def saveForm(self, posted, form):
        """
        Save form data into input.py file specified by the path.
        """
        # Clean past history
        self.rmg = RMG()
        
        # Databases
        #self.rmg.databaseDirectory = settings['database.directory']
        self.rmg.thermoLibraries  = []
        if posted.thermo_libraries.all():
            self.rmg.thermoLibraries = [item.thermolib.encode() for item in posted.thermo_libraries.all()]
        self.rmg.reactionLibraries = []
        self.rmg.seedMechanisms = []
        if posted.reaction_libraries.all():
            for item in posted.reaction_libraries.all():
                if not item.seedmech and not item.edge:
                    self.rmg.reactionLibraries.append((item.reactionlib.encode(), False))
                elif not item.seedmech:
                    self.rmg.reactionLibraries.append((item.reactionlib.encode(), True))
                else:
                    self.rmg.seedMechanisms.append(item.reactionlib.encode())
        self.rmg.statmechLibraries = []
        self.rmg.kineticsDepositories = 'default'
        self.rmg.kineticsFamilies = 'default'
        self.rmg.kineticsEstimator = 'rate rules'
        
        # Species
        self.rmg.initialSpecies = []
        speciesDict = {}
        initialMoleFractions = {}
        self.rmg.reactionModel = CoreEdgeReactionModel()
        for item in posted.reactor_species.all():
            structure = Molecule().fromAdjacencyList(item.adjlist.encode())
            spec, isNew = self.rmg.reactionModel.makeNewSpecies(structure, label = item.name.encode(), reactive = False if item.inert else True)
            self.rmg.initialSpecies.append(spec)
            speciesDict[item.name.encode()] = spec
            initialMoleFractions[spec] = item.molefrac
            
        # Reactor systems
        self.rmg.reactionSystems = []
        for item in posted.reactor_systems.all():
            T = Quantity(item.temperature, item.temperature_units.encode())
            P = Quantity(item.pressure, item.pressure_units.encode())            
            termination = []
            if item.conversion:
                termination.append(TerminationConversion(speciesDict[item.species.encode()], item.conversion))
            termination.append(TerminationTime(Quantity(item.terminationtime, item.time_units.encode())))
            # Sensitivity Analysis
            sensitiveSpecies = []
            if item.sensitivity:
                if isinstance(item.sensitivity.encode(), str):
                    sensitivity = item.sensitivity.encode().split(',')
                for spec in sensitivity:
                    sensitiveSpecies.append(speciesDict[spec.strip()])
            system = SimpleReactor(T, P, initialMoleFractions, termination, sensitiveSpecies, item.sensitivityThreshold)
            self.rmg.reactionSystems.append(system)
    
        # Simulator tolerances
        self.rmg.absoluteTolerance = form.cleaned_data['simulator_atol']
        self.rmg.relativeTolerance = form.cleaned_data['simulator_rtol']
        self.rmg.sensitivityAbsoluteTolerance = form.cleaned_data['simulator_sens_atol']
        self.rmg.sensitivityRelativeTolerance = form.cleaned_data['simulator_sens_rtol']
        self.rmg.fluxToleranceKeepInEdge = form.cleaned_data['toleranceKeepInEdge']
        self.rmg.fluxToleranceMoveToCore = form.cleaned_data['toleranceMoveToCore']
        self.rmg.fluxToleranceInterrupt = form.cleaned_data['toleranceInterruptSimulation']
        self.rmg.maximumEdgeSpecies = form.cleaned_data['maximumEdgeSpecies']
        self.rmg.minCoreSizeForPrune = form.cleaned_data['minCoreSizeForPrune']
        self.rmg.minSpeciesExistIterationsForPrune = form.cleaned_data['minSpeciesExistIterationsForPrune']
        self.rmg.filterReactions = form.cleaned_data['filterReactions']
        
        # Pressure Dependence
        pdep = form.cleaned_data['pdep'].encode()
        if pdep != 'off':
            self.rmg.pressureDependence = PressureDependenceJob(network=None)
            self.rmg.pressureDependence.method = pdep
            
            # Process interpolation model
            if form.cleaned_data['interpolation'].encode() == 'chebyshev':
                self.rmg.pressureDependence.interpolationModel = (form.cleaned_data['interpolation'].encode(), form.cleaned_data['temp_basis'], form.cleaned_data['p_basis'])
            else:
                self.rmg.pressureDependence.interpolationModel = (form.cleaned_data['interpolation'].encode(),)
            
            # Temperature and pressure range
            self.rmg.pressureDependence.Tmin = Quantity(form.cleaned_data['temp_low'], form.cleaned_data['temprange_units'].encode())
            self.rmg.pressureDependence.Tmax = Quantity(form.cleaned_data['temp_high'], form.cleaned_data['temprange_units'].encode())
            self.rmg.pressureDependence.Tcount = form.cleaned_data['temp_interp']
            self.rmg.pressureDependence.generateTemperatureList() 
            self.rmg.pressureDependence.Pmin = Quantity(form.cleaned_data['p_low'], form.cleaned_data['prange_units'].encode())
            self.rmg.pressureDependence.Pmax = Quantity(form.cleaned_data['p_high'], form.cleaned_data['prange_units'].encode())
            self.rmg.pressureDependence.Pcount = form.cleaned_data['p_interp']
            self.rmg.pressureDependence.generatePressureList()
            
            # Process grain size and count
            self.rmg.pressureDependence.grainSize = Quantity(form.cleaned_data['maximumGrainSize'], form.cleaned_data['grainsize_units'].encode())
            self.rmg.pressureDependence.grainCount = form.cleaned_data['minimumNumberOfGrains']
            
            self.rmg.pressureDependence.maximumAtoms = form.cleaned_data['maximumAtoms']
        # Additional Options
        self.rmg.units = 'si' 
        self.rmg.saveRestartPeriod = Quantity(form.cleaned_data['saveRestartPeriod'], form.cleaned_data['saveRestartPeriodUnits'].encode()) if form.cleaned_data['saveRestartPeriod'] else None
        self.rmg.generateOutputHTML = form.cleaned_data['generateOutputHTML']
        self.rmg.generatePlots = form.cleaned_data['generatePlots']
        self.rmg.saveSimulationProfiles = form.cleaned_data['saveSimulationProfiles']
        self.rmg.saveEdgeSpecies = form.cleaned_data['saveEdgeSpecies']
        self.rmg.verboseComments = form.cleaned_data['verboseComments']
        
        # Species Constraints
        speciesConstraints = form.cleaned_data['speciesConstraints']
        if speciesConstraints == 'on':
            allowed = []
            if form.cleaned_data['allowed_inputSpecies']: allowed.append('input species')
            if form.cleaned_data['allowed_seedMechanisms']: allowed.append('seed mechanisms')
            if form.cleaned_data['allowed_reactionLibraries']: allowed.append('reaction libraries')
            self.rmg.speciesConstraints['allowed'] = allowed
            self.rmg.speciesConstraints['maximumCarbonAtoms'] = form.cleaned_data['maximumCarbonAtoms']
            self.rmg.speciesConstraints['maximumOxygenAtoms'] = form.cleaned_data['maximumOxygenAtoms']
            self.rmg.speciesConstraints['maximumNitrogenAtoms'] = form.cleaned_data['maximumNitrogenAtoms']
            self.rmg.speciesConstraints['maximumSiliconAtoms'] = form.cleaned_data['maximumSiliconAtoms']
            self.rmg.speciesConstraints['maximumSulfurAtoms'] = form.cleaned_data['maximumSulfurAtoms']
            self.rmg.speciesConstraints['maximumHeavyAtoms'] = form.cleaned_data['maximumHeavyAtoms']
            self.rmg.speciesConstraints['maximumRadicalElectrons'] = form.cleaned_data['maximumRadicalElectrons']
            self.rmg.speciesConstraints['allowSingletO2'] = form.cleaned_data['allowSingletO2']
        
        # Quantum Calculations
        quantumCalc = form.cleaned_data['quantumCalc']
        if quantumCalc == 'on':
            from rmgpy.qm.main import QMCalculator
            self.rmg.quantumMechanics = QMCalculator(software = form.cleaned_data['software'].encode(),
                                                     method = form.cleaned_data['method'].encode(),
                                                     fileStore = form.cleaned_data['fileStore'].encode(),
                                                     scratchDirectory = form.cleaned_data['scratchDirectory'].encode(),
                                                     onlyCyclics = form.cleaned_data['onlyCyclics'],
                                                     maxRadicalNumber = form.cleaned_data['maxRadicalNumber'],
                                                     )
        
        # Save the input.py file        
        self.rmg.saveInput(self.savepath)

################################################################################
# DATABASE MODELS
################################################################################
thermo_libraries, kinetics_libraries = getLibraryLists()
ThermoLibraries = [(label, label) for label in thermo_libraries]
KineticsLibraries = [(label, label) for label in kinetics_libraries]

class ThermoLibrary(models.Model):
    input = models.ForeignKey(Input, related_name = 'thermo_libraries')
    thermolib = models.CharField(choices = ThermoLibraries, max_length=200, blank=True)
    def __unicode__(self):
        return self.thermolib

class ReactionLibrary(models.Model):
    input = models.ForeignKey(Input, related_name = 'reaction_libraries')
    reactionlib = models.CharField(choices = KineticsLibraries, max_length=200, blank=True)
    edge = models.BooleanField()
    seedmech = models.BooleanField()
    def __unicode__(self):
        return self.reactionlib

################################################################################
# SPECIES MODEL
################################################################################

class ReactorSpecies(models.Model):
    input = models.ForeignKey(Input, related_name='reactor_species')
    name = models.CharField(max_length=200)
    identifier = models.CharField(max_length=200, blank = True)
    adjlist = models.TextField()
    molefrac = models.FloatField()
    inert = models.BooleanField()
    def __unicode__(self):
        return self.name


################################################################################
# REACTOR MODEL
################################################################################

class Reactor(models.Model):
    input = models.ForeignKey(Input, related_name='reactor_systems')
    temperature = models.FloatField()
    temperature_units = models.CharField(max_length=50, default = 'K', choices=temp_units)
    pressure= models.FloatField()
    pressure_units = models.CharField(max_length=50, default = 'bar', choices=p_units)
    # NOTE: Initial Mole Fractions cannot be set individually for each reactor system 
    # through the web form right now.
    # Termination Criteria
    # Must always specify a termination time, but need not always specify a conversion
    terminationtime = models.FloatField()
    time_units = models.CharField(max_length=50, choices=t_units, default = 's')
    species = models.CharField(max_length=50, blank=True, null=True)
    conversion = models.FloatField(blank=True, null=True)
    # Sensitivity
    sensitivity = models.CharField(max_length=200, blank=True, null=True)
    sensitivityThreshold = models.FloatField(default = 0.001)
    
