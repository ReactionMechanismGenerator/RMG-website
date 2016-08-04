from django.test import TestCase

class VersionTest(TestCase):
    
    def test_0(self):
        """
        Test that /version gives expected response
        """
        
        response = self.client.get('/version')
        
        self.assertEqual(response.status_code, 200)
    
    def test_1(self):
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
        
        self.assertTrue(response.context['pb'], 'RMG-Py body is empty')
        self.assertTrue(response.context['db'], 'RMG-database body is empty')
        self.assertTrue(response.context['wb'], 'RMG-website body is empty')
        