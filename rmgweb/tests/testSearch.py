from django.test import TestCase


class KineticsTest(TestCase):

    def test_kinetics_search_1(self):
        """
        Test that kinetics search accepts 1 reactant
        """

        reactant1 = """
1 C u0 p0 c0 {2,S} {3,S} {4,S} {5,S}
2 H u0 p0 c0 {1,S}
3 H u0 p0 c0 {1,S}
4 H u0 p0 c0 {1,S}
5 H u0 p0 c0 {1,S}
"""

        response = self.client.post('/database/kinetics/search/', {'reactant1': reactant1})

        self.assertEqual(response.status_code, 302)

    def test_kinetics_search_1_1(self):
        """
        Test that kinetics search accepts 1 reactant and 1 product
        """

        reactant1 = """
multiplicity 2
1  C u0 p0 c0 {2,S} {6,S} {7,S} {8,S}
2  C u0 p0 c0 {1,S} {3,S} {9,S} {10,S}
3  C u1 p0 c0 {2,S} {4,S} {5,S}
4  H u0 p0 c0 {3,S}
5  H u0 p0 c0 {3,S}
6  H u0 p0 c0 {1,S}
7  H u0 p0 c0 {1,S}
8  H u0 p0 c0 {1,S}
9  H u0 p0 c0 {2,S}
10 H u0 p0 c0 {2,S}
"""
        product1 = """
multiplicity 2
1  C u0 p0 c0 {2,S} {5,S} {6,S} {7,S}
2  C u1 p0 c0 {1,S} {3,S} {4,S}
3  H u0 p0 c0 {2,S}
4  C u0 p0 c0 {2,S} {8,S} {9,S} {10,S}
5  H u0 p0 c0 {1,S}
6  H u0 p0 c0 {1,S}
7  H u0 p0 c0 {1,S}
8  H u0 p0 c0 {4,S}
9  H u0 p0 c0 {4,S}
10 H u0 p0 c0 {4,S}
"""

        response = self.client.post('/database/kinetics/search/', {'reactant1': reactant1, 'product1': product1})

        self.assertEqual(response.status_code, 302)

    def test_kinetics_search_1_2(self):
        """
        Test that kinetics search accepts 1 reactant and 2 products
        """

        reactant1 = """
1 C u0 p0 c0 {2,S} {3,S} {4,S} {5,S}
2 H u0 p0 c0 {1,S}
3 H u0 p0 c0 {1,S}
4 H u0 p0 c0 {1,S}
5 H u0 p0 c0 {1,S}
"""
        product1 = """
multiplicity 2
1 C u1 p0 c0 {2,S} {3,S} {4,S}
2 H u0 p0 c0 {1,S}
3 H u0 p0 c0 {1,S}
4 H u0 p0 c0 {1,S}
"""
        product2 = """
multiplicity 2
1 H u1 p0 c0
"""

        response = self.client.post('/database/kinetics/search/', {'reactant1': reactant1,
                                                                   'product1': product1,
                                                                   'product2': product2})

        self.assertEqual(response.status_code, 302)

    def test_kinetics_search_2(self):
        """
        Test that kinetics search accepts 2 reactants
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

        self.assertEqual(response.status_code, 302)

    def test_kinetics_search_2_1(self):
        """
        Test that kinetics search accepts 2 reactants and 1 product
        """

        reactant1 = """
multiplicity 2
1 C u1 p0 c0 {2,S} {3,S} {4,S}
2 H u0 p0 c0 {1,S}
3 H u0 p0 c0 {1,S}
4 H u0 p0 c0 {1,S}
"""
        reactant2 = """
multiplicity 2
1 O u1 p2 c0 {2,S}
2 H u0 p0 c0 {1,S}
"""
        product1 = """
1 C u0 p0 c0 {2,S} {3,S} {4,S} {5,S}
2 H u0 p0 c0 {1,S}
3 H u0 p0 c0 {1,S}
4 H u0 p0 c0 {1,S}
5 O u0 p2 c0 {1,S} {6,S}
6 H u0 p0 c0 {5,S}
"""

        response = self.client.post('/database/kinetics/search/', {'reactant1': reactant1,
                                                                   'reactant2': reactant2,
                                                                   'product1': product1})

        self.assertEqual(response.status_code, 302)

    def test_kinetics_search_2_2(self):
        """
        Test that kinetics search accepts 2 reactants and 2 products
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
        product1 = """
multiplicity 2
1 C u1 p0 c0 {2,S} {3,S} {4,S}
2 H u0 p0 c0 {1,S}
3 H u0 p0 c0 {1,S}
4 H u0 p0 c0 {1,S}
"""
        product2 = """
1 O u0 p2 c0 {2,S} {3,S}
2 H u0 p0 c0 {1,S}
3 H u0 p0 c0 {1,S}
"""

        response = self.client.post('/database/kinetics/search/', {'reactant1': reactant1,
                                                                   'reactant2': reactant2,
                                                                   'product1': product1,
                                                                   'product2': product2})

        self.assertEqual(response.status_code, 302)

