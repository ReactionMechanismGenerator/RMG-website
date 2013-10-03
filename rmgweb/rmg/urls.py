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

from django.conf.urls.defaults import *

urlpatterns = patterns('rmgweb.rmg',

    # RMG Simulation Homepage
    (r'^$', 'views.index'),

    # Convert Chemkin File to Output File
    (r'^chemkin','views.convertChemkin'),

    # Compare 2 RMG Models
    (r'^compare','views.compareModels'),
    
    # Merge 2 RMG Models
    (r'^merge_models','views.mergeModels'),

    # Generate Flux Diagram
    (r'^flux','views.generateFlux'),
    
    # Populate Reactions with an Input File
    (r'^populate_reactions','views.runPopulateReactions'),
    
    # RMG Input Form
    (r'^input', 'views.input'),
    
    # Plot Kinetics
    (r'^plot_kinetics', 'views.plotKinetics'),
    
    # Generate RMG-Java Kinetics Library
    (r'^java_kinetics_library', 'views.javaKineticsLibrary'),
    
    # Evaluate NASA Polynomial
    (r'^evaluate_nasa', 'views.evaluateNASA')


)
