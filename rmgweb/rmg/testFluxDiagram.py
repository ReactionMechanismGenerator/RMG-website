import unittest
import os.path
import shutil

from rmgpy.tools.fluxdiagram import *

class GenerateFluxDiagramTest(unittest.TestCase):

    def test_minimal(self):
    	folder = os.path.join(os.getcwd(),'rmgweb/rmg/tests/minimal')
        inputFile = os.path.join(folder,'input.py')

        run(inputFile)

        outputdir = os.path.join(folder, 'flux/')
        outputdir_sys1 = os.path.join(outputdir, '1/')
        outputfile = os.path.join(outputdir_sys1, 'flux_diagram.avi')
        self.assertTrue(os.path.isfile(outputfile))
        
        shutil.rmtree(outputdir)