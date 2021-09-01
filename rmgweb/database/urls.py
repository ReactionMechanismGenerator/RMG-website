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

import itertools

from django.urls import re_path

from rmgweb.database import views

app_name = 'database'

urlpatterns = [

    # Database homepage
    re_path(r'^$', views.index, name='index'),

    # Load the whole database into memory
    re_path(r'^load/?$', views.load, name='load'),

    # Export to an RMG-Java database
    re_path(r'^export_(?P<type>zip|tar\.gz)/?$', views.export, name='export'),

    # Thermodynamics database
    re_path(r'^thermo/$', views.thermo, name='thermo'),
    re_path(r'^thermo/search/$', views.moleculeSearch, name='thermo-search'),
    re_path(r'^thermo/molecule/(?P<adjlist>[\S\s]+)$', views.thermoData, name='thermo-data'),
    re_path(r'^thermo/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/$', views.thermoEntry, name='thermo-entry'),
    re_path(r'^thermo/(?P<section>\w+)/(?P<subsection>.+)/(?P<adjlist>[\S\s]+)/new$', views.thermoEntryNew, name='thermo-entry-new'),
    re_path(r'^thermo/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/edit$', views.thermoEntryEdit, name='thermo-entry-edit'),
    re_path(r'^thermo/(?P<section>\w+)/(?P<subsection>.+)/$', views.thermo, name='thermo'),
    re_path(r'^thermo/(?P<section>\w+)/$', views.thermo, name='thermo'),

    # Transport database
    re_path(r'^transport/$', views.transport, name='transport'),
    re_path(r'^transport/search/$', views.moleculeSearch, name='transport-search'),
    re_path(r'^transport/molecule/(?P<adjlist>[\S\s]+)$', views.transportData, name='transport-data'),
    re_path(r'^transport/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/$', views.transportEntry, name='transport-entry'),
    re_path(r'^transport/(?P<section>\w+)/(?P<subsection>.+)/$', views.transport, name='transport'),
    re_path(r'^transport/(?P<section>\w+)/$', views.transport, name='transport'),

    # solvation database
    re_path(r'^solvation/$', views.solvation, name='solvation'),
    re_path(r'^solvation/index/$', views.solvationIndex, name='solvation-index'),
    re_path(r'^solvation/search/$', views.solvationSearch, name='solvation-search'),
    re_path(r'^solvation/results/solute=(?P<solute_adjlist>[\S\s]+)__solvent=(?P<solvent>[\S\s]+)__'
            r'solventTemp=(?P<solvent_temp>[\S\s]+)__temp=(?P<temp>\d+\.\d+)$', views.solvationData, name='solvation-data'),
    re_path(r'^solvation/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/$', views.solvationEntry, name='solvation-entry'),
    re_path(r'^solvation/(?P<section>\w+)/(?P<subsection>.+)/$', views.solvation, name='solvation'),
    re_path(r'^solvation/(?P<section>\w+)/$', views.solvation, name='solvation'),

    # statmech database
    re_path(r'^statmech/$', views.statmech, name='statmech'),
    re_path(r'^statmech/search/$', views.moleculeSearch, name='statmech-search'),
    re_path(r'^statmech/molecule/(?P<adjlist>[\S\s]+)$', views.statmechData, name='statmech-data'),
    re_path(r'^statmech/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/$', views.statmechEntry, name='statmech-entry'),
    re_path(r'^statmech/(?P<section>\w+)/(?P<subsection>.+)/$', views.statmech, name='statmech'),
    re_path(r'^statmech/(?P<section>\w+)/$', views.statmech, name='statmech'),

    # Kinetics database
    re_path(r'^kinetics/$', views.kinetics, name='kinetics'),
    re_path(r'^kinetics/search/$', views.kineticsSearch, name='kinetics-search'),

    re_path(r'^kinetics/families/(?P<family>[^/]+)/(?P<type>\w+)/new$', views.kineticsEntryNew, name='kinetics-entry-new'),
    re_path(r'^kinetics/families/(?P<family>[^/]+)/untrained/$', views.kineticsUntrained, name='kinetics-untrained'),

    re_path(r'^kinetics/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>\d+)/edit$', views.kineticsEntryEdit, name='kinetics-entry-edit'),
    re_path(r'^kinetics/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/$', views.kineticsEntry, name='kinetics-entry'),
    re_path(r'^kinetics/(?P<section>\w+)/(?P<subsection>.+)/$', views.kinetics, name='kinetics'),
    re_path(r'^kinetics/(?P<section>\w+)/$', views.kinetics, name='kinetics'),

    # Molecule Information Page
    re_path(r'^molecule/(?P<adjlist>[\S\s]+)$', views.moleculeEntry, name='molecule-entry'),

    # Group Information Page
    re_path(r'^group/(?P<adjlist>[\S\s]+)$', views.groupEntry, name='group-entry'),

    # Generate Resonance Structure
    re_path(r'^resonance_structure/(?P<adjlist>[\S\s]+)$', views.generateResonanceStructure, name='resonance'),

    # Eni detergent-dirt binding strength
    re_path(r'^eni', views.EniSearch, name='eni-search'),

    # AJAX request url
    re_path(r'^ajax_adjlist_request', views.json_to_adjlist, name='json-to-adjlist'),

    # Remember to update the /media/robots.txt file to keep web-crawlers out of pages you don't want indexed.
]

# Generate url patterns for kinetics search and results pages combinatorially
url_parts = [
    r'reactant1=(?P<reactant1>[\S\s]+)',
    r'__reactant2=(?P<reactant2>[\S\s]+)',
    r'__reactant3=(?P<reactant3>[\S\s]+)',
    r'__product1=(?P<product1>[\S\s]+)',
    r'__product2=(?P<product2>[\S\s]+)',
    r'__product3=(?P<product3>[\S\s]+)',
    r'__res=(?P<resonance>[\S\s]+)',
]

for r2, r3, p1, p2, p3, res in itertools.product([1, 0], repeat=6):
    url_pattern = r'^kinetics/results/'
    url_pattern += url_parts[0]
    if r2:
        url_pattern += url_parts[1]
    if r2 and r3:
        url_pattern += url_parts[2]
    if p1:
        url_pattern += url_parts[3]
    if p2:
        url_pattern += url_parts[4]
    if p2 and p3:
        url_pattern += url_parts[5]
    if res:
        url_pattern += url_parts[6]
    url_pattern += r'$'

    urlpatterns.append(re_path(url_pattern, views.kineticsResults, name='kinetics-results'))

for r2, r3, p1, p2, p3, res in itertools.product([1, 0], repeat=6):
    url_pattern = r'^kinetics/reaction/'
    url_pattern += url_parts[0]
    if r2:
        url_pattern += url_parts[1]
    if r2 and r3:
        url_pattern += url_parts[2]
    if p1:
        url_pattern += url_parts[3]
    if p2:
        url_pattern += url_parts[4]
    if p2 and p3:
        url_pattern += url_parts[5]
    if res:
        url_pattern += url_parts[6]
    url_pattern += r'$'

    urlpatterns.append(re_path(url_pattern, views.kineticsData, name='kinetics-data'))

for r2, r3, p2, p3, res in itertools.product([1, 0], repeat=5):
    url_pattern = r'^kinetics/families/(?P<family>[^/]+)/(?P<estimator>[^/]+)/'
    url_pattern += url_parts[0]
    if r2:
        url_pattern += url_parts[1]
    if r2 and r3:
        url_pattern += url_parts[2]
    url_pattern += url_parts[3]
    if p2:
        url_pattern += url_parts[4]
    if p2 and p3:
        url_pattern += url_parts[5]
    if res:
        url_pattern += url_parts[6]
    url_pattern += r'$'

    urlpatterns.append(re_path(url_pattern, views.kineticsGroupEstimateEntry, name='kinetics-group'))
