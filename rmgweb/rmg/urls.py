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

from django.conf.urls import url, include
from rmgweb.rmg import views
import rmgweb.database.views

urlpatterns = [
    # RMG Simulation Homepage
    url(r'^$', views.index),

    url(r'^group_draw', rmgweb.database.views.groupDraw),

    # Convert Chemkin File to Output File
    url(r'^chemkin', views.convertChemkin),

    # Compare 2 RMG Models
    url(r'^compare', views.compareModels),

    # Compare 2 RMG Models
    url(r'^adjlist_conversion', views.convertAdjlists),

    # Merge 2 RMG Models
    url(r'^merge_models', views.mergeModels),

    # Generate Flux Diagram
    url(r'^flux', views.generateFlux),

    # Populate Reactions with an Input File
    url(r'^populate_reactions', views.runPopulateReactions),

    # Plot Kinetics
    url(r'^plot_kinetics', views.plotKinetics),

    # Generate RMG-Java Kinetics Library
    url(r'^java_kinetics_library', views.javaKineticsLibrary),

    # Evaluate NASA Polynomial
    url(r'^evaluate_nasa', views.evaluateNASA),
    
]
