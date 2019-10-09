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

from future import standard_library
standard_library.install_aliases()

import urllib.error
import urllib.parse
import urllib.request

from django.test import TestCase
from django.utils.encoding import iri_to_uri
from rmgpy.reaction import Reaction
from rmgpy.species import Species

from rmgweb.database.views import getReactionUrl


class urlTest(TestCase):

    def test_kinetics_search(self):
        """
        Test whether url is only encoded once
        """

        reactant1 = """
1 C u0 p0 c0 {2,S} {3,S} {4,S} {5,S}
2 H u0 p0 c0 {1,S}
3 H u0 p0 c0 {1,S}
4 H u0 p0 c0 {1,S}
5 H u0 p0 c0 {1,S}
"""
        reactant2 = """
multiplicity 2
1 O u1 p2 c0 {2,S}
2 H u0 p0 c0 {1,S}
"""

        response = self.client.post('/database/kinetics/search/', {'reactant1': reactant1,
                                                                   'reactant2': reactant2,
                                                                   'resonance': False})

        base_url = '/database/kinetics/results/reactant1={0}__reactant2={1}__res=False'
        expected_url = iri_to_uri(base_url.format(reactant1.strip(), reactant2.strip()))

        self.assertRedirects(response, expected_url)

    def test_getReactionURL(self):
        """
        Test whether url is only encoded once
        """

        reactant1 = Species().from_smiles('[CH3]')
        reactant2 = Species().from_smiles('[SH]')
        product1 = Species().from_smiles('CS')

        reaction = Reaction(reactants=[reactant1, reactant2], products=[product1])

        url = getReactionUrl(reaction, resonance=False)

        base_url = '/database/kinetics/reaction/reactant1={0}__reactant2={1}__product1={2}__res=False'
        expected_url = iri_to_uri(base_url.format(reactant1.to_adjacency_list(),
                                                  reactant2.to_adjacency_list(),
                                                  product1.to_adjacency_list()))

        self.assertEqual(url, expected_url)
