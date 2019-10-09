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

import os
import shutil

import rmgpy
from django.test import TestCase

import rmgweb
import rmgweb.settings as settings


class ChemkinTest(TestCase):

    def test_0(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/tools/chemkin/')

        self.assertEqual(response.status_code, 200)

    def test_1(self):
        """
        Test post functionality of /tools/chemkin/
        """

        chemFile = os.path.join(rmgpy.getPath(), 'tools', 'data', 'diffmodels', 'chem1.inp')
        dictFile = os.path.join(rmgpy.getPath(), 'tools', 'data', 'diffmodels', 'species_dictionary1.txt')

        with open(chemFile) as cf, open(dictFile) as df:
            response = self.client.post('/tools/chemkin/', {'ChemkinFile': cf, 'DictionaryFile': df})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'chemkin')

        # Check if inputs were correctly uploaded
        chemInput = os.path.join(folder, 'chemkin', 'chem.inp')
        dictInput = os.path.join(folder, 'RMG_Dictionary.txt')

        self.assertTrue(os.path.isfile(chemInput), 'Chemkin file was not uploaded')
        self.assertTrue(os.path.isfile(dictInput), 'Dictionary file was not uploaded')

        # Check if outputs were correctly generated
        htmlOutput = os.path.join(folder, 'output.html')

        self.assertTrue(os.path.isfile(htmlOutput), 'HTML Output was not generated')

        # Clean up
        shutil.rmtree(folder)


class CompareTest(TestCase):

    def test_0(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/tools/compare/')

        self.assertEqual(response.status_code, 200)

    def test_1(self):
        """
        Test basic functionality of /tools/compare/
        """

        chemFile1 = os.path.join(rmgpy.getPath(), 'tools', 'data', 'diffmodels', 'chem1.inp')
        dictFile1 = os.path.join(rmgpy.getPath(), 'tools', 'data', 'diffmodels', 'species_dictionary1.txt')
        chemFile2 = os.path.join(rmgpy.getPath(), 'tools', 'data', 'diffmodels', 'chem2.inp')
        dictFile2 = os.path.join(rmgpy.getPath(), 'tools', 'data', 'diffmodels', 'species_dictionary2.txt')

        with open(chemFile1) as cf1, open(dictFile1) as df1, open(chemFile2) as cf2, open(dictFile2) as df2:
            response = self.client.post('/tools/compare/', {'ChemkinFile1': cf1, 'DictionaryFile1': df1, 'ChemkinFile2': cf2, 'DictionaryFile2': df2})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'compare')

        # Check if inputs were correctly uploaded
        chemInput1 = os.path.join(folder, 'chem1.inp')
        dictInput1 = os.path.join(folder, 'RMG_Dictionary1.txt')
        chemInput2 = os.path.join(folder, 'chem2.inp')
        dictInput2 = os.path.join(folder, 'RMG_Dictionary2.txt')

        self.assertTrue(os.path.isfile(chemInput1), 'Chemkin file 1 was not uploaded')
        self.assertTrue(os.path.isfile(dictInput1), 'Dictionary file 1 was not uploaded')
        self.assertTrue(os.path.isfile(chemInput2), 'Chemkin file was 2 not uploaded')
        self.assertTrue(os.path.isfile(dictInput2), 'Dictionary file 2 was not uploaded')

        # Check if outputs were correctly generated
        htmlOutput = os.path.join(folder, 'diff.html')

        self.assertTrue(os.path.isfile(htmlOutput), 'HTML Output was not generated')

        shutil.rmtree(folder)

    def test_2(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/tools/merge_models/')

        self.assertEqual(response.status_code, 200)

    def test_3(self):
        """
        Test basic functionality of /tools/merge_models/
        """

        chemFile1 = os.path.join(rmgpy.getPath(), 'tools', 'data', 'diffmodels', 'chem1.inp')
        dictFile1 = os.path.join(rmgpy.getPath(), 'tools', 'data', 'diffmodels', 'species_dictionary1.txt')
        chemFile2 = os.path.join(rmgpy.getPath(), 'tools', 'data', 'diffmodels', 'chem2.inp')
        dictFile2 = os.path.join(rmgpy.getPath(), 'tools', 'data', 'diffmodels', 'species_dictionary2.txt')

        with open(chemFile1) as cf1, open(dictFile1) as df1, open(chemFile2) as cf2, open(dictFile2) as df2:
            response = self.client.post('/tools/merge_models/', {'ChemkinFile1': cf1, 'DictionaryFile1': df1, 'ChemkinFile2': cf2, 'DictionaryFile2': df2})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'compare')

        # Check if inputs were correctly uploaded
        chemInput1 = os.path.join(folder, 'chem1.inp')
        dictInput1 = os.path.join(folder, 'RMG_Dictionary1.txt')
        chemInput2 = os.path.join(folder, 'chem2.inp')
        dictInput2 = os.path.join(folder, 'RMG_Dictionary2.txt')

        self.assertTrue(os.path.isfile(chemInput1), 'Chemkin file 1 was not uploaded')
        self.assertTrue(os.path.isfile(dictInput1), 'Dictionary file 1 was not uploaded')
        self.assertTrue(os.path.isfile(chemInput2), 'Chemkin file was 2 not uploaded')
        self.assertTrue(os.path.isfile(dictInput2), 'Dictionary file 2 was not uploaded')

        # Check if outputs were correctly generated
        chemOutput = os.path.join(folder, 'chem.inp')
        dictOutput = os.path.join(folder, 'species_dictionary.txt')
        logOutput = os.path.join(folder, 'merging_log.txt')

        self.assertTrue(os.path.isfile(chemOutput), 'CHEMKIN file was not generated')
        self.assertTrue(os.path.isfile(dictOutput), 'Species dictionary was not generated')
        self.assertTrue(os.path.isfile(logOutput), 'Merging log file was not generated')

        shutil.rmtree(folder)


class FluxDiagramTest(TestCase):

    def test_0(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/tools/flux/')

        self.assertEqual(response.status_code, 200)

    def test_1(self):
        """
        Test basic functionality of /tools/flux/
        """

        inputFile = os.path.join(rmgpy.getPath(), 'tools', 'data', 'flux', 'input_simple.py')
        chemFile = os.path.join(rmgpy.getPath(), 'tools', 'data', 'flux', 'chemkin', 'chem.inp')
        dictFile = os.path.join(rmgpy.getPath(), 'tools', 'data', 'flux', 'chemkin', 'species_dictionary.txt')

        with open(inputFile) as nf, open(chemFile) as cf, open(dictFile) as df:
            response = self.client.post('/tools/flux/', {'InputFile': nf, 'ChemkinFile': cf, 'DictionaryFile': df,
                                                         'MaxNodes': 50, 'MaxEdges': 50, 'TimeStep': 1.25,
                                                         'ConcentrationTolerance': 1e-6, 'SpeciesRateTolerance': 1e-6})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'flux')

        # Check if inputs were correctly uploaded
        pyInput = os.path.join(folder, 'input.py')
        chemInput = os.path.join(folder, 'chem.inp')
        dictInput = os.path.join(folder, 'species_dictionary.txt')

        self.assertTrue(os.path.isfile(pyInput), 'RMG input file was not uploaded')
        self.assertTrue(os.path.isfile(chemInput), 'Chemkin file was not uploaded')
        self.assertTrue(os.path.isfile(dictInput), 'Dictionary file was not uploaded')

        # Check if outputs were correctly generated
        videoOutput = os.path.join(folder, '1', 'flux_diagram.avi')
        species = os.path.join(folder, 'species')

        self.assertTrue(os.path.isfile(videoOutput), 'Video output was not generated')
        self.assertTrue(os.path.isdir(species), 'Species directory was not generated')

        shutil.rmtree(folder)


class PopulateReactionsTest(TestCase):

    def test_0(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/tools/populate_reactions/')

        self.assertEqual(response.status_code, 200)

    def test_1(self):
        """
        Test basic functionality of /tools/populate_reactions/
        """

        from rmgpy.chemkin import loadChemkinFile
        from rmgpy.rmg.model import ReactionModel

        inputFile = os.path.join(rmgpy.getPath(), 'tools', 'data', 'generate', 'input.py')

        with open(inputFile) as fp:
            response = self.client.post('/tools/populate_reactions/',  {'InputFile': fp})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'populateReactions')

        # Check if inputs were correctly uploaded
        pyInput = os.path.join(folder, 'input.txt')

        self.assertTrue(os.path.isfile(pyInput), 'RMG input file was not uploaded')

        # Check if outputs were correctly generated
        htmlOutput = os.path.join(folder, 'output.html')
        chemOutput = os.path.join(folder, 'chemkin', 'chem.inp')
        dictOutput = os.path.join(folder, 'chemkin', 'species_dictionary.txt')

        self.assertTrue(os.path.isfile(htmlOutput), 'HTML Output was not generated')
        self.assertTrue(os.path.isfile(chemOutput), 'CHEMKIN file was not generated')
        self.assertTrue(os.path.isfile(dictOutput), 'Species dictionary was not generated')

        # Check that the output is not empty
        model = ReactionModel()
        model.species, model.reactions = loadChemkinFile(chemOutput, dictOutput)

        self.assertTrue(model.species, 'No species were generated')
        self.assertTrue(model.reactions, 'No reactions were generated')

        shutil.rmtree(folder)


class PlotKineticsTest(TestCase):

    def test_0(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/tools/plot_kinetics/')

        self.assertEqual(response.status_code, 200)

    def test_1(self):
        """
        Test basic functionality of /tools/plot_kinetics/
        """

        chemFile = os.path.join(os.path.dirname(rmgweb.__file__), 'tests', 'files', 'kinetics', 'chem.inp')
        dictFile = os.path.join(os.path.dirname(rmgweb.__file__), 'tests', 'files', 'kinetics', 'species_dictionary.txt')

        with open(chemFile) as cf, open(dictFile) as df:
            response = self.client.post('/tools/plot_kinetics/', {'ChemkinFile': cf, 'DictionaryFile': df})

        self.assertEqual(response.status_code, 200)

        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'chemkin'))

    def test_2(self):
        """
        Test without uploading dictionary file
        """

        chemFile = os.path.join(os.path.dirname(rmgweb.__file__), 'tests', 'files', 'kinetics', 'chem.inp')

        with open(chemFile) as cf:
            response = self.client.post('/tools/plot_kinetics/', {'ChemkinFile': cf})

        self.assertEqual(response.status_code, 200)

        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'chemkin'))


class EvaluateNASATest(TestCase):

    def test_0(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/tools/evaluate_nasa/')

        self.assertEqual(response.status_code, 200)

    def test_1(self):
        """
        Test basic functionality of /tools/evaluate_nasa/
        """

        nasa = """CH3                     C 1  H 3            G100.000   5000.000  1337.62       1
 3.54144859E+00 4.76788187E-03-1.82149144E-06 3.28878182E-10-2.22546856E-14    2
 1.62239622E+04 1.66040083E+00 3.91546822E+00 1.84153688E-03 3.48743616E-06    3
-3.32749553E-09 8.49963443E-13 1.62856393E+04 3.51739246E-01                   4"""

        response = self.client.post('/tools/evaluate_nasa/', {'NASA': nasa})

        self.assertEqual(response.status_code, 200)


class AdjlistConversionTest(TestCase):

    def test_0(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/tools/adjlist_conversion/')

        self.assertEqual(response.status_code, 200)

    def test_1(self):
        """
        Test basic functionality of /tools/adjlist_conversion/
        """

        dictFile = os.path.join(os.path.dirname(rmgweb.__file__), 'tests', 'files', 'kinetics', 'species_dictionary.txt')

        with open(dictFile) as df:
            response = self.client.post('/tools/adjlist_conversion/', {'DictionaryFile': df})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'adjlistConversion')

        # Check if inputs were correctly uploaded
        dictInput = os.path.join(folder, 'species_dictionary.txt')

        self.assertTrue(os.path.isfile(dictInput), 'Dictionary file was not uploaded')

        # Check if outputs were correctly generated
        htmlOutput = os.path.join(folder, 'RMG_Dictionary.txt')

        self.assertTrue(os.path.isfile(htmlOutput), 'Species dictionary was not generated')

        shutil.rmtree(folder)


class JavaLibraryTest(TestCase):

    def test_0(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/tools/java_kinetics_library/')

        self.assertEqual(response.status_code, 200)

    def test_1(self):
        """
        Test basic functionality of /tools/java_kinetics_library/
        """

        chemFile = os.path.join(os.path.dirname(rmgweb.__file__), 'tests', 'files', 'kinetics', 'chem.inp')
        dictFile = os.path.join(os.path.dirname(rmgweb.__file__), 'tests', 'files', 'kinetics', 'species_dictionary.txt')

        with open(chemFile) as cf, open(dictFile) as df:
            response = self.client.post('/tools/java_kinetics_library/', {'ChemkinFile': cf, 'DictionaryFile': df})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'chemkin')

        # Check if inputs were correctly uploaded
        chemInput = os.path.join(folder, 'chemkin', 'chem.inp')
        dictInput = os.path.join(folder, 'RMG_Dictionary.txt')

        self.assertTrue(os.path.isfile(chemInput), 'Chemkin file was not uploaded')
        self.assertTrue(os.path.isfile(dictInput), 'Dictionary file was not uploaded')

        # Check if outputs were correctly generated
        reactions = os.path.join(folder, 'reactions.txt')
        pdep = os.path.join(folder, 'pdepreactions.txt')
        species = os.path.join(folder, 'species.txt')

        self.assertTrue(os.path.isfile(reactions), 'Reactions file was not generated')
        self.assertTrue(os.path.isfile(pdep), 'Pdep reactions file was not generated')
        self.assertTrue(os.path.isfile(species), 'Species file was not generated')

        shutil.rmtree(folder)
