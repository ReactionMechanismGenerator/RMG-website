from django.test import TestCase
import urllib
from django.utils.encoding import iri_to_uri
from rmgpy.species import Species
from rmgpy.reaction import Reaction
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

        response = self.client.post('/database/kinetics/search/', {'reactant1': reactant1, 'reactant2': reactant2})

        base_url = 'http://testserver/database/kinetics/results/reactant1={0}__reactant2={1}'
        expected_url = iri_to_uri(base_url.format(reactant1, reactant2))

        self.assertRedirects(response, expected_url)

    def test_getReactionURL(self):
        """
        Test whether url is only encoded once
        """

        reactant1 = Species().fromSMILES('[CH3]')
        reactant2 = Species().fromSMILES('[SH]')
        product1 = Species().fromSMILES('CS')

        reaction = Reaction(reactants=[reactant1, reactant2], products=[product1])

        url = getReactionUrl(reaction)

        base_url = '/database/kinetics/reaction/reactant1={0}__reactant2={1}__product1={2}'
        expected_url = iri_to_uri(base_url.format(reactant1.toAdjacencyList(),
                                                    reactant2.toAdjacencyList(),
                                                    product1.toAdjacencyList()))

        self.assertEqual(url, expected_url)

