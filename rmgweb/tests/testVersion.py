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

from django.test import TestCase


class VersionTest(TestCase):

    def test_gets_to_version_page(self):
        """
        Test that /version gives expected response
        """

        response = self.client.get('/version')

        self.assertEqual(response.status_code, 200)

    def test_retrieves_versions_of_rmg_database(self):
        """
        Test that the context contains the expected git info
        """

        response = self.client.get('/version')

        self.assertTrue(response.context['pc'], 'RMG-Py commit is empty')
        self.assertTrue(response.context['dc'], 'RMG-database commit is empty')
        self.assertTrue(response.context['wc'], 'RMG-website commit is empty')

        self.assertTrue(response.context['pd'], 'RMG-Py date is empty')
        self.assertTrue(response.context['dd'], 'RMG-database date is empty')
        self.assertTrue(response.context['wd'], 'RMG-website date is empty')

        self.assertTrue(response.context['pds'], 'RMG-Py short date is empty')
        self.assertTrue(response.context['dds'], 'RMG-database short date is empty')
        self.assertTrue(response.context['wds'], 'RMG-website short date is empty')

        self.assertTrue(response.context['ps'], 'RMG-Py subject is empty')
        self.assertTrue(response.context['ds'], 'RMG-database subject is empty')
        self.assertTrue(response.context['ws'], 'RMG-website subject is empty')
