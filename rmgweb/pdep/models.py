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
This module defines the Django models used by the pdep app.
"""

import os
import os.path

from django.db import models

import rmgweb.settings as settings

################################################################################

class Network(models.Model):
    """
    A Django model of a pressure-dependent reaction network. 
    """
    def upload_input_to(instance, filename):
        # Always name the uploaded input file "input.py"
        return 'pdep/networks/{0}/input.py'.format(instance.pk)
    title = models.CharField(max_length=50)
    inputFile = models.FileField(upload_to=upload_input_to, verbose_name='Input file')
    inputText = models.TextField(blank=True, verbose_name='')

    def getDirname(self):
        """
        Return the absolute path of the directory that the Network object uses
        to store files.
        """
        return os.path.join(settings.MEDIA_ROOT, 'pdep', 'networks', str(self.pk))
    
    def getInputFilename(self):
        """
        Return the absolute path of the input file.
        """
        return os.path.join(self.getDirname(), 'input.py')
    
    def getOutputFilename(self):
        """
        Return the absolute path of the output file.
        """
        return os.path.join(self.getDirname(), 'output.py')
    
    def getSurfaceFilename(self, format):
        """
        Return the absolute path of the PES image file in the given `format`.
        """
        return os.path.join(self.getDirname(), 'PES.{0}'.format(format.lower()))
    
    def inputFileExists(self):
        """
        Return ``True`` if the input file exists on the server or ``False`` if
        not.
        """
        return os.path.exists(self.getInputFilename())
        
    def outputFileExists(self):
        """
        Return ``True`` if the output file exists on the server or ``False`` if
        not.
        """
        return os.path.exists(self.getOutputFilename())
        
    def surfaceFileExists(self):
        """
        Return ``True`` if any potential energy surface image file exists
        """
        return (os.path.exists(self.getSurfaceFilename('png')) or
            os.path.exists(self.getSurfaceFilename('pdf')) or
            os.path.exists(self.getSurfaceFilename('svg')))
        
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
        
    def deleteInputFile(self):
        """
        Delete the input file for this network from the server.
        """
        if self.inputFileExists():
            os.remove(self.getInputFilename())
        
    def deleteOutputFile(self):
        """
        Delete the output file for this network from the server.
        """
        if self.outputFileExists():
            os.remove(self.getOutputFilename())
        
    def deleteSurfaceFiles(self):
        """
        Delete the PES image file(s) for this network from the server.
        """
        for ext in ['png', 'pdf', 'svg']:
            fpath = self.getSurfaceFilename(ext)
            if os.path.exists(fpath):
                os.remove(fpath)
        
    def loadInputText(self):
        """
        Load the input file text into the inputText field.
        """
        self.inputText = ''
        if self.inputFileExists():
            f = open(self.getInputFilename(),'r')
            for line in f:
                self.inputText += line
            f.close()
        
    def saveInputText(self):
        """
        Save the contents of the inputText field to the input file.
        """
        fpath = self.getInputFilename()
        self.createDir()
        f = open(fpath,'w')
        for line in self.inputText.splitlines():
            f.write(line + '\n')
        f.close()
        