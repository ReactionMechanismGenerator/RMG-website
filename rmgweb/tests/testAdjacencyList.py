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

class AdjacencyListViewTests(TestCase):
    def test_getAdjacencyList_Empty(self):
        identifier = ''
        response = self.client.get('/adjacencylist/' + identifier)
        self.assertEquals(response.content, "")
        self.assertEqual(response.status_code, 200)

    def test_getAdjacencyList_SMILES(self):
        identifier = 'C'
        response = self.client.get('/adjacencylist/' + identifier)
        self.assertEqual(response.status_code, 200)

    def test_getAdjacencyList_InChI(self):
        identifier = 'InChI=1S/CH4/h1H4'
        response = self.client.get('/adjacencylist/' + identifier)
        self.assertEqual(response.status_code, 200)

    def test_getAdjacencyList_IUPACName(self):
        identifier = 'methane'
        response = self.client.get('/adjacencylist/' + identifier)
        self.assertEqual(response.status_code, 200)