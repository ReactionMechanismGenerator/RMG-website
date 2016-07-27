import unittest
import os.path
import shutil

from rmgpy.tools.fluxdiagram import *

class GenerateFluxDiagramTest(unittest.TestCase):

    def test_minimal_use_species_drawings(self):
    	"""
    	Uses pre-generated png species drawings to include
    	in the video.
    	"""
    	folder = os.path.join(os.getcwd(),'rmgweb/rmg/tests/minimal')
        inputFile = os.path.join(folder,'input.py')
        speciesPath = os.path.join(os.path.dirname(inputFile), 'species_pngs')

        run(inputFile, speciesPath)

        outputdir = os.path.join(folder, 'flux/')
        outputdir_sys1 = os.path.join(outputdir, '1/')
        outputfile = os.path.join(outputdir_sys1, 'flux_diagram.avi')
        self.assertTrue(os.path.isfile(outputfile))
        
        shutil.rmtree(outputdir)

    def test_minimal_do_not_use_species_drawings(self):
    	"""
    	Generate a video with species labels, without species drawings.
    	"""
    	folder = os.path.join(os.getcwd(),'rmgweb/rmg/tests/minimal')
        inputFile = os.path.join(folder,'input.py')

        run(inputFile)

        outputdir = os.path.join(folder, 'flux/')
        
        outputdir_sys1 = os.path.join(outputdir, '1/')
        outputfile = os.path.join(outputdir_sys1, 'flux_diagram.avi')
        self.assertTrue(os.path.isfile(outputfile))
        
        shutil.rmtree(outputdir)

        speciesdir = os.path.join(folder, 'species/')
        shutil.rmtree(speciesdir)