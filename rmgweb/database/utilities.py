# utilities.py
# A file that contains a method for creating SolventList outside of models, forms or views
# Created to break cyclic import error created from importing getSolventList() from database.views

#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
#
#	RMG Website - A Django-powered website for Reaction Mechanism Generator
#
#	Copyright (c) 2011 Prof. William H. Green (whgreen@mit.edu) and the
#	RMG Team (rmg_dev@mit.edu)
#
#	Permission is hereby granted, free of charge, to any person obtaining a
#	copy of this software and associated documentation files (the 'Software'),
#	to deal in the Software without restriction, including without limitation
#	the rights to use, copy, modify, merge, publish, distribute, sublicense,
#	and/or sell copies of the Software, and to permit persons to whom the
#	Software is furnished to do so, subject to the following conditions:
#
#	The above copyright notice and this permission notice shall be included in
#	all copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#	DEALINGS IN THE SOFTWARE.
#
################################################################################

import cookielib
import copy
import os
import re
import shutil
import socket
import StringIO # cStringIO is faster, but can't do Unicode
import subprocess
import sys
import time
import urllib
import urllib2

from BeautifulSoup import BeautifulSoup

from rmgpy.molecule.molecule import Molecule
from rmgpy.molecule.group import Group
from rmgpy.thermo import *
from rmgpy.kinetics import *
from rmgpy.transport import *
from rmgpy.reaction import Reaction
from rmgpy.quantity import Quantity

import rmgpy
from rmgpy.data.base import *
from rmgpy.data.thermo import ThermoDatabase
from rmgpy.data.kinetics import *
from rmgpy.data.rmg import RMGDatabase
from rmgpy.data.solvation import * 
from rmgpy.data.statmech import *
from rmgpy.data.transport import *

from rmgweb.database.tools import *

# Creating the SolventList
def getSolventList():
    """
    Return list of solvent molecules for initializing solvation search form.
    """
    loadDatabase('solvation','')
    SolventList = [(entry.label, index) for index,entry in database.solvation.libraries['solvent'].entries.iteritems()]
    return SolventList