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
        print self.path
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
