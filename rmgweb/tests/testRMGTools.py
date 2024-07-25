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

        chem_file = os.path.join(rmgpy.get_path(), 'tools', 'data', 'diffmodels', 'chem1.inp', blank=True, null=True)
        dict_file = os.path.join(rmgpy.get_path(), 'tools', 'data', 'diffmodels', 'species_dictionary1.txt', blank=True, null=True)

        with open(chem_file) as cf, open(dict_file) as df:
            response = self.client.post('/tools/chemkin/', {'chem_file': cf, 'dict_file': df})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'chemkin')

        # Check if inputs were correctly uploaded
        chem_input = os.path.join(folder, 'chemkin', 'chem.inp')
        dict_input = os.path.join(folder, 'RMG_Dictionary.txt')

        self.assertTrue(os.path.isfile(chem_input), 'Chemkin file was not uploaded')
        self.assertTrue(os.path.isfile(dict_input), 'Dictionary file was not uploaded')

        # Check if outputs were correctly generated
        html_output = os.path.join(folder, 'output.html')

        self.assertTrue(os.path.isfile(html_output), 'HTML Output was not generated')

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

        chem_file1 = os.path.join(rmgpy.get_path(), 'tools', 'data', 'diffmodels', 'chem1.inp', blank=True, null=True)
        dict_file1 = os.path.join(rmgpy.get_path(), 'tools', 'data', 'diffmodels', 'species_dictionary1.txt', blank=True, null=True)
        chem_file2 = os.path.join(rmgpy.get_path(), 'tools', 'data', 'diffmodels', 'chem2.inp', blank=True, null=True)
        dict_file2 = os.path.join(rmgpy.get_path(), 'tools', 'data', 'diffmodels', 'species_dictionary2.txt', blank=True, null=True)

        with open(chem_file1) as cf1, open(dict_file1) as df1, open(chem_file2) as cf2, open(dict_file2) as df2:
            response = self.client.post('/tools/compare/', {'chem_file1': cf1, 'dict_file1': df1, 'chem_file2': cf2, 'dict_file2': df2})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'compare')

        # Check if inputs were correctly uploaded
        chem_input1 = os.path.join(folder, 'chem1.inp')
        dict_input1 = os.path.join(folder, 'RMG_Dictionary1.txt')
        chem_input2 = os.path.join(folder, 'chem2.inp')
        dict_input2 = os.path.join(folder, 'RMG_Dictionary2.txt')

        self.assertTrue(os.path.isfile(chem_input1), 'Chemkin file 1 was not uploaded')
        self.assertTrue(os.path.isfile(dict_input1), 'Dictionary file 1 was not uploaded')
        self.assertTrue(os.path.isfile(chem_input2), 'Chemkin file was 2 not uploaded')
        self.assertTrue(os.path.isfile(dict_input2), 'Dictionary file 2 was not uploaded')

        # Check if outputs were correctly generated
        html_output = os.path.join(folder, 'diff.html')

        self.assertTrue(os.path.isfile(html_output), 'HTML Output was not generated')

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

        chem_file1 = os.path.join(rmgpy.get_path(), 'tools', 'data', 'diffmodels', 'chem1.inp', blank=True, null=True)
        dict_file1 = os.path.join(rmgpy.get_path(), 'tools', 'data', 'diffmodels', 'species_dictionary1.txt', blank=True, null=True)
        chem_file2 = os.path.join(rmgpy.get_path(), 'tools', 'data', 'diffmodels', 'chem2.inp', blank=True, null=True)
        dict_file2 = os.path.join(rmgpy.get_path(), 'tools', 'data', 'diffmodels', 'species_dictionary2.txt', blank=True, null=True)

        with open(chem_file1) as cf1, open(dict_file1) as df1, open(chem_file2) as cf2, open(dict_file2) as df2:
            response = self.client.post('/tools/merge_models/', {'chem_file1': cf1, 'dict_file1': df1, 'chem_file2': cf2, 'dict_file2': df2})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'compare')

        # Check if inputs were correctly uploaded
        chem_input1 = os.path.join(folder, 'chem1.inp')
        dict_input1 = os.path.join(folder, 'RMG_Dictionary1.txt')
        chem_input2 = os.path.join(folder, 'chem2.inp')
        dict_input2 = os.path.join(folder, 'RMG_Dictionary2.txt')

        self.assertTrue(os.path.isfile(chem_input1), 'Chemkin file 1 was not uploaded')
        self.assertTrue(os.path.isfile(dict_input1), 'Dictionary file 1 was not uploaded')
        self.assertTrue(os.path.isfile(chem_input2), 'Chemkin file was 2 not uploaded')
        self.assertTrue(os.path.isfile(dict_input2), 'Dictionary file 2 was not uploaded')

        # Check if outputs were correctly generated
        chem_output = os.path.join(folder, 'chem.inp')
        dict_output = os.path.join(folder, 'species_dictionary.txt')
        log_output = os.path.join(folder, 'merging_log.txt')

        self.assertTrue(os.path.isfile(chem_output), 'CHEMKIN file was not generated')
        self.assertTrue(os.path.isfile(dict_output), 'Species dictionary was not generated')
        self.assertTrue(os.path.isfile(log_output), 'Merging log file was not generated')

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

        input_file = os.path.join(rmgpy.get_path(), 'tools', 'data', 'flux', 'input_simple.py')
        chem_file = os.path.join(rmgpy.get_path(), 'tools', 'data', 'flux', 'chemkin', 'chem.inp')
        dict_file = os.path.join(rmgpy.get_path(), 'tools', 'data', 'flux', 'chemkin', 'species_dictionary.txt')

        with open(input_file) as nf, open(chem_file) as cf, open(dict_file) as df:
            response = self.client.post('/tools/flux/', {'input_file': nf, 'chem_file': cf, 'dict_file': df,
                                                         'max_nodes': 50, 'max_edges': 50, 'time_step': 1.25,
                                                         'concentration_tol': 1e-6, 'species_rate_tol': 1e-6})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'flux')

        # Check if inputs were correctly uploaded
        py_input = os.path.join(folder, 'input.py')
        chem_input = os.path.join(folder, 'chem.inp')
        dict_input = os.path.join(folder, 'species_dictionary.txt')

        self.assertTrue(os.path.isfile(py_input), 'RMG input file was not uploaded')
        self.assertTrue(os.path.isfile(chem_input), 'Chemkin file was not uploaded')
        self.assertTrue(os.path.isfile(dict_input), 'Dictionary file was not uploaded')

        # Check if outputs were correctly generated
        video_output = os.path.join(folder, 'flux', '1', 'flux_diagram.avi')
        species = os.path.join(folder, 'species')

        self.assertTrue(os.path.isfile(video_output), 'Video output was not generated')
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

        from rmgpy.chemkin import load_chemkin_file
        from rmgpy.rmg.model import ReactionModel

        input_file = os.path.join(rmgpy.get_path(), 'tools', 'data', 'generate', 'input.py')

        with open(input_file) as fp:
            response = self.client.post('/tools/populate_reactions/',  {'input_file': fp})

        self.assertEqual(response.status_code, 200)

        folder = os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'populateReactions')

        # Check if inputs were correctly uploaded
        py_input = os.path.join(folder, 'input.txt')

        self.assertTrue(os.path.isfile(py_input), 'RMG input file was not uploaded')

        # Check if outputs were correctly generated
        html_output = os.path.join(folder, 'output.html')
        chem_output = os.path.join(folder, 'chemkin', 'chem.inp')
        dict_output = os.path.join(folder, 'chemkin', 'species_dictionary.txt')

        self.assertTrue(os.path.isfile(html_output), 'HTML Output was not generated')
        self.assertTrue(os.path.isfile(chem_output), 'CHEMKIN file was not generated')
        self.assertTrue(os.path.isfile(dict_output), 'Species dictionary was not generated')

        # Check that the output is not empty
        model = ReactionModel()
        model.species, model.reactions = load_chemkin_file(chem_output, dict_output)

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

        chem_file = os.path.join(os.path.dirname(rmgweb.__file__), 'tests', 'files', 'kinetics', 'chem.inp')
        dict_file = os.path.join(os.path.dirname(rmgweb.__file__), 'tests', 'files', 'kinetics', 'species_dictionary.txt')

        with open(chem_file) as cf, open(dict_file) as df:
            response = self.client.post('/tools/plot_kinetics/', {'chem_file': cf, 'dict_file': df})

        self.assertEqual(response.status_code, 200)

        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'rmg', 'tools', 'chemkin'))

    def test_2(self):
        """
        Test without uploading dictionary file
        """

        chem_file = os.path.join(os.path.dirname(rmgweb.__file__), 'tests', 'files', 'kinetics', 'chem.inp')

        with open(chem_file) as cf:
            response = self.client.post('/tools/plot_kinetics/', {'chem_file': cf})

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

        response = self.client.post('/tools/evaluate_nasa/', {'nasa': nasa})

        self.assertEqual(response.status_code, 200)

