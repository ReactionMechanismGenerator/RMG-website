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
from rmgpy.molecule import Molecule
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
    DictionaryFile = models.FileField(upload_to=upload_dictionary_to,verbose_name='RMG Dictionary')

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
    ChemkinFile2 = models.FileField(upload_to=upload_chemkin2_to, verbose_name='Model 2: Chemkin File')
    DictionaryFile2 = models.FileField(upload_to=upload_dictionary2_to,verbose_name='Model 2: RMG Dictionary')

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
        saveCompareHTML(self.path, self.chemkin1, self.dict1, self.chemkin2, self.dict2)

    def createDir(self):
        """
        Create the directory (and any other needed parent directories) that
        the Network uses for storing files.
        """
        try:
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
