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

from django.urls import re_path

import rmgweb.database.views
from rmgweb.rmg import views


app_name = 'rmg'

urlpatterns = [
    # RMG Simulation Homepage
    re_path(r'^$', views.index, name='index'),

    re_path(r'^group_draw', rmgweb.database.views.groupDraw, name='group-draw'),

    # Convert Chemkin File to Output File
    re_path(r'^chemkin', views.convertChemkin, name='convert-chemkin'),

    # Compare 2 RMG Models
    re_path(r'^compare', views.compareModels, name='compare-models'),

    # Merge 2 RMG Models
    re_path(r'^merge_models', views.mergeModels, name='merge-models'),

    # Generate Flux Diagram
    re_path(r'^flux', views.generateFlux, name='generate-flux'),

    # Populate Reactions with an Input File
    re_path(r'^populate_reactions', views.runPopulateReactions, name='run-populate-reactions'),

    # Plot Kinetics
    re_path(r'^plot_kinetics', views.plotKinetics, name='plot-kinetics'),

    # Evaluate NASA Polynomial
    re_path(r'^evaluate_nasa', views.evaluateNASA, name='evaluate-nasa'),
]
