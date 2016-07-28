from django.test import TestCase
import os.path
import rmgpy
import rmgweb
import rmgweb.settings as settings
import shutil

class ChemkinTest(TestCase):
    
    def test_1(self):
        """
        Test basic functionality of /tools/chemkin/
        """
        
        chemfile = os.path.join(rmgpy.getPath(),'tools','data','diffmodels','chem1.inp')
        dictfile = os.path.join(rmgpy.getPath(),'tools','data','diffmodels','species_dictionary1.txt')
        
        with open(chemfile) as cf, open(dictfile) as df:
            response = self.client.post('/tools/chemkin/', {'ChemkinFile': cf, 'DictionaryFile': df})
        
        self.assertEqual(response.status_code, 200)
        
        folder = os.path.join(settings.MEDIA_ROOT,'rmg','tools','chemkin')
        
        htmlfile = os.path.join(folder,'output.html')
        
        self.assertTrue(os.path.isfile(htmlfile),'HTML Output was not generated')
        
        shutil.rmtree(folder)

class CompareTest(TestCase):
    
    def test_1(self):
        """
        Test basic functionality of /tools/compare/
        """
        
        chemfile1 = os.path.join(rmgpy.getPath(),'tools','data','diffmodels','chem1.inp')
        dictfile1 = os.path.join(rmgpy.getPath(),'tools','data','diffmodels','species_dictionary1.txt')
        chemfile2 = os.path.join(rmgpy.getPath(),'tools','data','diffmodels','chem2.inp')
        dictfile2 = os.path.join(rmgpy.getPath(),'tools','data','diffmodels','species_dictionary2.txt')
        
        with open(chemfile1) as cf1, open(dictfile1) as df1, open(chemfile2) as cf2, open(dictfile2) as df2:
            response = self.client.post('/tools/compare/', {'ChemkinFile1': cf1, 'DictionaryFile1': df1, 'ChemkinFile2': cf2, 'DictionaryFile2': df2})
        
        self.assertEqual(response.status_code, 200)
        
        folder = os.path.join(settings.MEDIA_ROOT,'rmg','tools','compare')
        
        htmlfile = os.path.join(folder,'diff.html')
        
        self.assertTrue(os.path.isfile(htmlfile),'HTML Output was not generated')
        
        shutil.rmtree(folder)
    
    def test_2(self):
        """
        Test basic functionality of /tools/merge_models/
        """
        
        chemfile1 = os.path.join(rmgpy.getPath(),'tools','data','diffmodels','chem1.inp')
        dictfile1 = os.path.join(rmgpy.getPath(),'tools','data','diffmodels','species_dictionary1.txt')
        chemfile2 = os.path.join(rmgpy.getPath(),'tools','data','diffmodels','chem2.inp')
        dictfile2 = os.path.join(rmgpy.getPath(),'tools','data','diffmodels','species_dictionary2.txt')
        
        with open(chemfile1) as cf1, open(dictfile1) as df1, open(chemfile2) as cf2, open(dictfile2) as df2:
            response = self.client.post('/tools/merge_models/', {'ChemkinFile1': cf1, 'DictionaryFile1': df1, 'ChemkinFile2': cf2, 'DictionaryFile2': df2})
        
        self.assertEqual(response.status_code, 200)
        
        folder = os.path.join(settings.MEDIA_ROOT,'rmg','tools','compare')
        
        chemfile = os.path.join(folder,'chem.inp')
        dictfile = os.path.join(folder,'species_dictionary.txt')
        logfile = os.path.join(folder,'merging_log.txt')
        
        self.assertTrue(os.path.isfile(chemfile),'CHEMKIN file was not generated')
        self.assertTrue(os.path.isfile(dictfile),'Species dictionary was not generated')
        self.assertTrue(os.path.isfile(logfile),'Merging log file was not generated')
        
        shutil.rmtree(folder)

class FluxDiagramTest(TestCase):
    
    def test_1(self):
        """
        Test basic functionality of /tools/flux/
        """
        
        inputfile = os.path.join(rmgpy.getPath(),'tools','data','flux','input.py')
        chemfile = os.path.join(rmgpy.getPath(),'tools','data','flux','chemkin','chem.inp')
        dictfile = os.path.join(rmgpy.getPath(),'tools','data','flux','chemkin','species_dictionary.txt')
        
        with open(inputfile) as nf, open(chemfile) as cf, open(dictfile) as df:
            response = self.client.post('/tools/flux/', {'InputFile': nf, 'ChemkinFile': cf, 'DictionaryFile': df, 
                                                         'MaxNodes': 50, 'MaxEdges': 50, 'TimeStep': 1.25, 
                                                         'ConcentrationTolerance': 1e-6, 'SpeciesRateTolerance': 1e-6})
        
        self.assertEqual(response.status_code, 200)
        
        folder = os.path.join(settings.MEDIA_ROOT,'rmg','tools','flux')
        
        videofile = os.path.join(folder,'1','flux_diagram.avi')
        species = os.path.join(folder,'species')
        
        self.assertTrue(os.path.isfile(videofile),'Video output was not generated')
        self.assertTrue(os.path.isdir(species),'Species directory was not generated')
        
        shutil.rmtree(folder)

class PopulateReactionsTest(TestCase):
    
    def test_1(self):
        """
        Test basic functionality of /tools/populate_reactions/
        """
        
        from rmgpy.chemkin import loadChemkinFile
        from rmgpy.rmg.model import ReactionModel
        
        inputfile = os.path.join(rmgpy.getPath(),'tools','data','generate','input.py')
        
        with open(inputfile) as fp:
            response = self.client.post('/tools/populate_reactions/', {'InputFile': fp})
        
        self.assertEqual(response.status_code, 200)
        
        folder = os.path.join(settings.MEDIA_ROOT,'rmg','tools','populateReactions')
        
        htmlfile = os.path.join(folder,'output.html')
        chemfile = os.path.join(folder,'chemkin','chem.inp')
        dictfile = os.path.join(folder,'chemkin','species_dictionary.txt')
        
        self.assertTrue(os.path.isfile(htmlfile),'HTML Output was not generated')
        self.assertTrue(os.path.isfile(chemfile),'CHEMKIN file was not generated')
        self.assertTrue(os.path.isfile(dictfile),'Species dictionary was not generated')
        
        model = ReactionModel()
        model.species, model.reactions = loadChemkinFile(chemfile, dictfile)
        
        self.assertTrue(model.species,'No species were generated')
        self.assertTrue(model.reactions, 'No reactions were generated')
        
        shutil.rmtree(folder)

class PlotKineticsTest(TestCase):
    
    def test_1(self):
        """
        Test basic functionality of /tools/plot_kinetics/
        """
        
        chemfile = os.path.join(os.path.dirname(rmgweb.__file__),'tests','files','kinetics','chem.inp')
        dictfile = os.path.join(os.path.dirname(rmgweb.__file__),'tests','files','kinetics','species_dictionary.txt')
        
        with open(chemfile) as cf, open(dictfile) as df:
            response = self.client.post('/tools/plot_kinetics/', {'ChemkinFile': cf, 'DictionaryFile': df})
        
        self.assertEqual(response.status_code, 200)
        
    def test_2(self):
        """
        Test without uploading dictionary file
        """
        
        chemfile = os.path.join(os.path.dirname(rmgweb.__file__),'tests','files','kinetics','chem.inp')
        
        with open(chemfile) as cf:
            response = self.client.post('/tools/plot_kinetics/', {'ChemkinFile': cf})
        
        self.assertEqual(response.status_code, 200)

class EvaluateNASATest(TestCase):
    
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
    
    def test_1(self):
        """
        Test basic functionality of /tools/adjlist_conversion/
        """
        
        dictfile = os.path.join(os.path.dirname(rmgweb.__file__),'tests','files','kinetics','species_dictionary.txt')
        
        with open(dictfile) as df:
            response = self.client.post('/tools/adjlist_conversion/', {'DictionaryFile': df})
        
        self.assertEqual(response.status_code, 200)
        
        folder = os.path.join(settings.MEDIA_ROOT,'rmg','tools','adjlistConversion')
        
        htmlfile = os.path.join(folder,'RMG_Dictionary.txt')
        
        self.assertTrue(os.path.isfile(htmlfile),'Species dictionary was not generated')
        
        shutil.rmtree(folder)

class JavaLibraryTest(TestCase):
    
    def test_1(self):
        """
        Test basic functionality of /tools/java_kinetics_library/
        """
        
        chemfile = os.path.join(os.path.dirname(rmgweb.__file__),'tests','files','kinetics','chem.inp')
        dictfile = os.path.join(os.path.dirname(rmgweb.__file__),'tests','files','kinetics','species_dictionary.txt')
        
        with open(chemfile) as cf, open(dictfile) as df:
            response = self.client.post('/tools/java_kinetics_library/', {'ChemkinFile': cf, 'DictionaryFile': df})
        
        self.assertEqual(response.status_code, 200)
        
        folder = os.path.join(settings.MEDIA_ROOT,'rmg','tools','chemkin')
        
        reactions = os.path.join(folder,'reactions.txt')
        pdep = os.path.join(folder,'pdepreactions.txt')
        species = os.path.join(folder,'species.txt')
        
        self.assertTrue(os.path.isfile(reactions),'Reactions file was not generated')
        self.assertTrue(os.path.isfile(pdep),'Pdep reactions file was not generated')
        self.assertTrue(os.path.isfile(species),'Species file was not generated')
        
        shutil.rmtree(folder)
