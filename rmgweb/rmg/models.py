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

from rmgpy.quantity import *
import os.path

from django.db import models
from django import forms
from django.utils.text import capfirst
from rmgpy.molecule.molecule import Molecule
from rmgpy.rmg.main import RMG
from rmgweb.main.tools import *
from rmgweb.database.views import loadDatabase

import rmgweb.settings as settings




class Chemkin(models.Model):
    """
    A Django model of a chemkin file.
    """

    def __init__(self, *args, **kwargs):
        super(Chemkin, self).__init__(*args, **kwargs)
        self.path = self.getDirname()

    def upload_chemkin_to(instance, filename):
        return instance.path + '/chemkin/chem.inp'
    def upload_dictionary_to(instance, filename):
        return instance.path + '/RMG_Dictionary.txt'
    ChemkinFile = models.FileField(upload_to=upload_chemkin_to, verbose_name='Chemkin File')
    DictionaryFile = models.FileField(upload_to=upload_dictionary_to,verbose_name='RMG Dictionary', blank=True, null=True)
    Foreign = models.BooleanField(verbose_name="Not an RMG-generated Chemkin file")
    
    def getDirname(self):
        """
        Return the absolute path of the directory that the object uses
        to store files.
        """
        return os.path.join(settings.MEDIA_ROOT, 'rmg','tools/')

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
            os.makedirs(os.path.join(self.getDirname(),'chemkin'))
            os.makedirs(os.path.join(self.getDirname(),'species'))
        except OSError:
            # Fail silently on any OS errors
            pass

    def deleteDir(self):
        """
        Clean up everything by deleting the directory
        """
        import shutil
        try:
            shutil.rmtree(self.getDirname())
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
        chemkinPath= self.path + '/chemkin/chem.inp'
        dictionaryPath = self.path + 'RMG_Dictionary.txt' 
        if os.path.exists(dictionaryPath):
            speciesList, reactionList = loadChemkinFile(chemkinPath, dictionaryPath)
        else:
            speciesList, reactionList = loadChemkinFile(chemkinPath)
            
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
        
        chemkinPath = self.path + '/chemkin/chem.inp'
        dictionaryPath = self.path + 'RMG_Dictionary.txt' 
        speciesList, reactionList = loadChemkinFile(chemkinPath, dictionaryPath)
        saveJavaKineticsLibrary(self.path, speciesList, reactionList)
        return


class Diff(models.Model):
    """
    A Django model for storing 2 RMG models and comparing them.
    """
    def __init__(self, *args, **kwargs):
        super(Diff, self).__init__(*args, **kwargs)
        self.path = self.getDirname()
        self.chemkin1 = self.path + '/chem1.inp'
        self.dict1 = self.path + '/RMG_Dictionary1.txt'
        self.chemkin2 = self.path + '/chem2.inp'
        self.dict2 = self.path + '/RMG_Dictionary2.txt'

    def upload_chemkin1_to(instance, filename):
        return instance.path + '/chem1.inp'
    def upload_dictionary1_to(instance, filename):
        return instance.path + '/RMG_Dictionary1.txt'
    def upload_chemkin2_to(instance, filename):
        return instance.path + '/chem2.inp'
    def upload_dictionary2_to(instance, filename):
        return instance.path + '/RMG_Dictionary2.txt'
    ChemkinFile1 = models.FileField(upload_to=upload_chemkin1_to, verbose_name='Model 1: Chemkin File')
    DictionaryFile1 = models.FileField(upload_to=upload_dictionary1_to,verbose_name='Model 1: RMG Dictionary')    
    Foreign1 = models.BooleanField(verbose_name="Model 1 not an RMG-generated Chemkin file")
    ChemkinFile2 = models.FileField(upload_to=upload_chemkin2_to, verbose_name='Model 2: Chemkin File')
    DictionaryFile2 = models.FileField(upload_to=upload_dictionary2_to,verbose_name='Model 2: RMG Dictionary')    
    Foreign2 = models.BooleanField(verbose_name="Model 2 not an RMG-generated Chemkin file")

    def getDirname(self):
        """
        Return the absolute path of the directory that the object uses
        to store files.
        """
        return os.path.join(settings.MEDIA_ROOT, 'rmg','tools','compare/')

    def createOutput(self):
        """
        Generate output html file from the path containing chemkin and dictionary files.
        """
        from diffModels import saveCompareHTML
        readComments1 = not self.Foreign1
        readComments2 = not self.Foreign2
        saveCompareHTML(self.path, self.chemkin1, self.dict1, self.chemkin2, self.dict2, readComments1, readComments2)

    def merge(self):
        """
        Merge the two models together to generate both chemkin and dictionary files.
        """
        import subprocess        
        
        logfile = os.path.join(self.path,'merging_log.txt')
        out = open(logfile,"w")
        
        pypath = os.path.join(settings.PROJECT_PATH, '..','..', 'RMG-Py','mergeModels.py')
        subprocess.Popen(['python', pypath, 
                    '--model1', self.chemkin1, self.dict1,
                    '--model2', self.chemkin2, self.dict2
                    ], cwd=self.path, stderr=subprocess.STDOUT, stdout=out)
        
    def createDir(self):
        """
        Create the directory (and any other needed parent directories) that
        the Network uses for storing files.
        """
        try:         
            os.makedirs(os.path.join(self.getDirname(),'species1'))
            os.makedirs(os.path.join(self.getDirname(),'species2'))
        except OSError:
            # Fail silently on any OS errors
            pass

    def deleteDir(self):
        """
        Clean up everything by deleting the directory
        """
        import shutil
        try:
            shutil.rmtree(self.getDirname())
        except OSError:
            pass



class FluxDiagram(models.Model):
    """
    A Django model for generating a flux diagram using RMG-Py.
    """
    def __init__(self, *args, **kwargs):
        super(FluxDiagram, self).__init__(*args, **kwargs)
        self.path = self.getDirname()

    def upload_input_to(instance, filename):
        return instance.path + '/input.py'
    def upload_chemkin_to(instance, filename):
        return instance.path + '/chem.inp'
    def upload_dictionary_to(instance, filename):
        return instance.path + '/species_dictionary.txt'
    def upload_chemkinoutput_to(instance, filename):
        return instance.path + '/chemkin_output.out'
    InputFile = models.FileField(upload_to=upload_input_to, verbose_name='RMG Input File')
    ChemkinFile = models.FileField(upload_to=upload_chemkin_to, verbose_name='Chemkin File')
    DictionaryFile = models.FileField(upload_to=upload_dictionary_to,verbose_name='RMG Dictionary')
    ChemkinOutput = models.FileField(upload_to=upload_chemkinoutput_to, verbose_name='Chemkin Output File (Optional)', blank=True,null=True)
    Java = models.BooleanField(verbose_name="From RMG-Java")
    MaxNodes = models.PositiveIntegerField(default=50, verbose_name='Maximum Nodes')
    MaxEdges = models.PositiveIntegerField(default=50, verbose_name='Maximum Edges')
    TimeStep = models.FloatField(default=1.25, verbose_name='Multiplicative Time Step Factor')
    ConcentrationTolerance = models.FloatField(default=1e-6, verbose_name='Concentration Tolerance')   # The lowest fractional concentration to show (values below this will appear as zero)
    SpeciesRateTolerance = models.FloatField(default=1e-6, verbose_name='Species Rate Tolerance')   # The lowest fractional species rate to show (values below this will appear as zero)
    
    

    def getDirname(self):
        """
        Return the absolute path of the directory that the object uses
        to store files.
        """
        return os.path.join(settings.MEDIA_ROOT, 'rmg','tools','flux/')

    def createDir(self):
        """
        Create the directory (and any other needed parent directories) that
        the Network uses for storing files.
        """
        try:
            os.makedirs(self.getDirname())
        except OSError:
            # Fail silently on any OS errors
            pass

    def deleteDir(self):
        """
        Clean up everything by deleting the directory
        """
        import shutil
        try:
            shutil.rmtree(self.getDirname())
        except OSError:
            pass


class PopulateReactions(models.Model):
    """
    A Django model for a PopulateReactions input file.
    """

    def __init__(self, *args, **kwargs):
        super(PopulateReactions, self).__init__(*args, **kwargs)        
        self.path = self.getDirname()
        self.input = self.path + '/input.txt'

    def upload_input_to(instance, filename):
        return instance.path + '/input.txt'
    InputFile = models.FileField(upload_to=upload_input_to, verbose_name='Input File')
  
    def getDirname(self):
        """
        Return the absolute path of the directory that the object uses
        to store files.
        """
        return os.path.join(settings.MEDIA_ROOT, 'rmg','tools','populateReactions/')

    def createOutput(self):
        """
        Generate output html file from the path containing chemkin and dictionary files.
        """
        
        
        import subprocess
        import rmgpy
        command = ('python',
            os.path.join(rmgpy.getPath(), '..', 'generateReactions.py'),
            self.input,
        )
        subprocess.check_call(command, cwd=self.path)
        
        #from generateReactions import populateReactions
        #populateReactions(self.input)

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

from rmgpy.measure.input import getTemperaturesForModel, getPressuresForModel
from rmgpy.measure.main import MEASURE
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
        self.path = self.getDirname()
        self.loadpath = self.path + '/input_upload.py'
        self.savepath = self.path + '/input.py'

    def upload_input_to(instance, filename):
        return instance.path + '/input_upload.py'

    input_upload = models.FileField(upload_to=upload_input_to, verbose_name='Input File', blank = True)
    
    # Pressure Dependence
    p_methods=(('off','off',),('modified strong collision','Modified Strong Collision',),('reservoir state','Reservoir State',))
    pdep = models.CharField(max_length = 50, default = 'off', choices = p_methods)
    # Advanced Options for PDep
    # Grain Size
    maximumGrainSize = models.FloatField(blank = True, default = 2, null = True)
    grain_units = (('kcal/mol','kcal/mol',),('kJ/mol','kJ/mol',))
    grainsize_units = models.CharField(max_length = 50, default = 'kcal/mol', choices = grain_units)
    minimumNumberOfGrains = models.PositiveIntegerField(blank = True, default = 200, null = True)
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
    toleranceMoveToCore = models.FloatField(blank=True, null=True)
    toleranceKeepInEdge= models.FloatField(default = 0.0)
    # Tolerance Advanced Options
    toleranceInterruptSimulation = models.FloatField(default = 1.0)
    maximumEdgeSpecies = models.PositiveIntegerField(default = 100000)
    simulator_atol = models.FloatField(default = 1e-16)
    simulator_rtol = models.FloatField(default = 1e-8)
    # Additional Options
    saveRestartPeriod=models.FloatField(blank = True, null=True)
    restartunits = (('second','seconds'),('hour','hours'),('day','days'),('week','weeks'))
    saveRestartPeriodUnits = models.CharField(max_length = 50, default = 'hour', choices = restartunits)
    drawMolecules=models.BooleanField()
    generatePlots=models.BooleanField()
    saveConcentrationProfiles = models.BooleanField()


    def getDirname(self):
        """
        Return the absolute path of the directory that the object uses
        to store files.
        """
        return os.path.join(settings.MEDIA_ROOT, 'rmg','tools','input/')

    def createDir(self):
        """
        Create the directory (and any other needed parent directories) that
        the Network uses for storing files.
        """
        try:
            os.makedirs(self.getDirname())
        except OSError:
            # Fail silently on any OS errors
            pass

    def deleteDir(self):
        """
        Clean up everything by deleting the directory
        """
        import shutil
        try:
            shutil.rmtree(self.getDirname())
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
            for item in self.rmg.seedMechanism:
                initial_reaction_libraries.append({'reactionlib': item, 'seedmech': True, 'edge': False})
        if self.rmg.reactionLibraries:
            for item, edge in self.rmg.reactionLibraries:
                initial_reaction_libraries.append({'reactionlib': item, 'seedmech': False, 'edge': edge})
        
        # Reactor systems
        initial_reactor_systems = []
        for system in self.rmg.reactionSystems:
            temperature = system.T.getValueInGivenUnits()
            temperature_units = system.T.units
            pressure = system.P.getValueInGivenUnits()
            pressure_units = system.P.units
            initialMoleFractions = system.initialMoleFractions
            for item in system.termination:
                if isinstance(item, TerminationTime):
                    terminationtime = item.time.getValueInGivenUnits()
                    time_units = item.time.units
                else:
                    species = item.species.label
                    conversion = item.conversion
            initial_reactor_systems.append({'temperature': temperature, 'temperature_units': temperature_units,
                                            'pressure': pressure, 'pressure_units': pressure_units,
                                            'terminationtime': terminationtime, 'time_units': time_units,
                                            'species': species, 'conversion': conversion})       
        
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
        initial['toleranceKeepInEdge'] = self.rmg.fluxToleranceKeepInEdge 
        initial['toleranceMoveToCore']= self.rmg.fluxToleranceMoveToCore
        initial['toleranceInterruptSimulation'] = self.rmg.fluxToleranceInterrupt
        initial['maximumEdgeSpecies'] = self.rmg.maximumEdgeSpecies 
                
        # Pressure Dependence
        if self.rmg.pressureDependence:
            initial['interpolation'] = self.rmg.pressureDependence.model[0]
            initial['temp_basis'] = self.rmg.pressureDependence.model[1]
            initial['p_basis'] = self.rmg.pressureDependence.model[2]
            initial['temp_low'] = self.rmg.pressureDependence.Tmin.getValueInGivenUnits()
            initial['temp_high'] = self.rmg.pressureDependence.Tmax.getValueInGivenUnits()
            initial['temprange_units'] = self.rmg.pressureDependence.Tmax.units
            initial['temp_interp'] = self.rmg.pressureDependence.Tcount
            initial['p_low'] = self.rmg.pressureDependence.Pmin.getValueInGivenUnits()
            initial['p_high'] = self.rmg.pressureDependence.Pmax.getValueInGivenUnits()
            initial['prange_units'] = self.rmg.pressureDependence.Pmax.units
            initial['p_interp'] = self.rmg.pressureDepence.Pcount
            
            initial['maximumGrainSize'] = self.rmg.pressureDependence.grainSize.getValueInGivenUnits()
            initial['grainsize_units'] = self.rmg.pressureDependence.grainSize.units
            initial['minimumNumberOfGrains'] = self.rmg.pressureDependence.grainCount

        else:
            initial['pdep'] = 'off'    
            
        # Additional Options
        if self.rmg.saveRestartPeriod:
            initial['saveRestartPeriod'] = self.rmg.saveRestartPeriod.getValueInGivenUnits()
            initial['saveRestartPeriodUnits'] = self.rmg.saveConcentrationProfiles.units
        if self.rmg.drawMolecules:
            initial['drawMolecules'] = True
        if self.rmg.generatePlots:
            initial['generatePlots'] = True
        if self.rmg.saveConcentrationProfiles:
            initial['saveConcentrationProfiles'] = True       
            
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
        self.rmg.kineticsDepositories = ['training']
        self.rmg.kineticsFamilies = ['!Intra_Disproportionation']        
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
            system = SimpleReactor(T, P, initialMoleFractions, termination)
            self.rmg.reactionSystems.append(system)
    
        # Simulator tolerances
        self.rmg.absoluteTolerance = form.cleaned_data['simulator_atol']
        self.rmg.relativeTolerance = form.cleaned_data['simulator_rtol']
        self.rmg.fluxToleranceKeepInEdge = form.cleaned_data['toleranceKeepInEdge']
        self.rmg.fluxToleranceMoveToCore = form.cleaned_data['toleranceMoveToCore']
        self.rmg.fluxToleranceInterrupt = form.cleaned_data['toleranceInterruptSimulation']
        self.rmg.maximumEdgeSpecies = form.cleaned_data['maximumEdgeSpecies']
        
        # Pressure Dependence
        pdep = form.cleaned_data['pdep'].encode()
        if pdep != 'off':
            self.rmg.pressureDependence = MEASURE()
            self.rmg.pressureDependence.method = pdep
            # Temperature and pressure range
            interpolation = (form.cleaned_data['interpolation'].encode(), form.cleaned_data['temp_basis'], form.cleaned_data['p_basis'])
            self.rmg.pressureDependence.Tmin = Quantity(form.cleaned_data['temp_low'], form.cleaned_data['temprange_units'].encode())
            self.rmg.pressureDependence.Tmax = Quantity(form.cleaned_data['temp_high'], form.cleaned_data['temprange_units'].encode())
            self.rmg.pressureDependence.Tcount = form.cleaned_data['temp_interp']
            Tlist = getTemperaturesForModel(interpolation, self.rmg.pressureDependence.Tmin.value, self.rmg.pressureDependence.Tmax.value, self.rmg.pressureDependence.Tcount)
            self.rmg.pressureDependence.Tlist = Quantity(Tlist,"K")
            
            self.rmg.pressureDependence.Pmin = Quantity(form.cleaned_data['p_low'], form.cleaned_data['prange_units'].encode())
            self.rmg.pressureDependence.Pmax = Quantity(form.cleaned_data['p_high'], form.cleaned_data['prange_units'].encode())
            self.rmg.pressureDependence.Pcount = form.cleaned_data['p_interp']
            Plist = getPressuresForModel(interpolation, self.rmg.pressureDependence.Pmin.value, self.rmg.pressureDependence.Pmax.value, self.rmg.pressureDependence.Pcount)
            self.rmg.pressureDependence.Plist = Quantity(Plist,"Pa")
            
            # Process grain size and count
            self.rmg.pressureDependence.grainSize = Quantity(form.cleaned_data['maximumGrainSize'], form.cleaned_data['grainsize_units'].encode())
            self.rmg.pressureDependence.grainCount = form.cleaned_data['minimumNumberOfGrains']
        
            # Process interpolation model
            self.rmg.pressureDependence.model = interpolation
        
        # Additional Options
        self.rmg.units = 'si' 
        self.rmg.saveRestartPeriod = Quantity(form.cleaned_data['saveRestartPeriod'], form.cleaned_data['saveRestartPeriodUnits'].encode()) if form.cleaned_data['saveRestartPeriod'] else None
        self.rmg.drawMolecules = form.cleaned_data['drawMolecules']
        self.rmg.generatePlots = form.cleaned_data['generatePlots']
        self.rmg.saveConcentrationProfiles = form.cleaned_data['saveConcentrationProfiles']

        # Save the input.py file        
        self.rmg.saveInput(self.savepath)

################################################################################
# DATABASE MODELS
################################################################################

database = loadDatabase('','libraries')
ThermoLibraries = [(label, label) for label, library in database.thermo.libraries.iteritems()]
ThermoLibraries.sort()
KineticsLibraries = [(label, label) for label, library in database.kinetics.libraries.iteritems()]
KineticsLibraries.sort()

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
    