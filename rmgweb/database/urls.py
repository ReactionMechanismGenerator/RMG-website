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

urlpatterns = patterns('rmgweb.database',

    # Database homepage
    (r'^$', 'views.index'),
    
    # Load the whole database into memory
    (r'^load/?$', 'views.load'),
    
    # History
    # These are up front to avoid it being interpreted as the 'history' section or subsection.
    (r'^history', 'views.gitHistory'),
    (r'^(?P<dbtype>kinetics|thermo)/history', 'views.gitHistory'),
    (r'^(?P<dbtype>kinetics|thermo)/(?P<section>\w+)/history', 'views.gitHistory'),
    (r'^(?P<dbtype>kinetics|thermo)/(?P<section>\w+)/(?P<subsection>.+)/history', 'views.gitHistory'),

    # Thermodynamics database
    (r'^thermo/$', 'views.thermo'),
    (r'^thermo/search/$', 'views.thermoSearch'),
    (r'^thermo/molecule/(?P<adjlist>[\S\s]+)$', 'views.thermoData'),
    (r'^thermo/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>\d+)/$', 'views.thermoEntry'),
    (r'^thermo/(?P<section>\w+)/(?P<subsection>.+)/$', 'views.thermo'),
    (r'^thermo/(?P<section>\w+)/$', 'views.thermo'),
    
    # Kinetics database
    (r'^kinetics/$', 'views.kinetics'),
    (r'^kinetics/search/$', 'views.kineticsSearch'),
    (r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__product3=(?P<product3>[\S\s]+)$', 'views.kineticsResults'),
    (r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__product3=(?P<product3>[\S\s]+)$', 'views.kineticsResults'),
    (r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__reactant3=(?P<reactant3>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)$', 'views.kineticsResults'),
    (r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)$', 'views.kineticsResults'),
    (r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)$', 'views.kineticsResults'),
    (r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)$', 'views.kineticsResults'),
    (r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)$', 'views.kineticsResults'),
    (r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)$', 'views.kineticsResults'),
    (r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)$', 'views.kineticsResults'),
    (r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__product3=(?P<product3>[\S\s]+)$', 'views.kineticsData'),
    (r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__product3=(?P<product3>[\S\s]+)$', 'views.kineticsData'),
    (r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__reactant3=(?P<reactant3>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)$', 'views.kineticsData'),
    (r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)$', 'views.kineticsData'),
    (r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)$', 'views.kineticsData'),
    (r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)$', 'views.kineticsData'),
    (r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)$', 'views.kineticsData'),
    (r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)$', 'views.kineticsData'),
    (r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)$', 'views.kineticsData'),
    
    (r'^kinetics/families/(?P<family>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)$', 'views.kineticsGroupEstimateEntry'),
    (r'^kinetics/families/(?P<family>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)$', 'views.kineticsGroupEstimateEntry'),
    (r'^kinetics/families/(?P<family>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)$', 'views.kineticsGroupEstimateEntry'),
    (r'^kinetics/families/(?P<family>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)$', 'views.kineticsGroupEstimateEntry'),
    (r'^kinetics/families/(?P<family>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)$', 'views.kineticsGroupEstimateEntry'),
    (r'^kinetics/families/(?P<family>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)$', 'views.kineticsGroupEstimateEntry'),
    
    (r'^kinetics/families/(?P<family>[^/]+)/training/new$', 'views.kineticsEntryNewTraining'),
    
    (r'^kinetics/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>\d+)/edit$', 'views.kineticsEntryEdit'),
    (r'^kinetics/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>\d+)/$', 'views.kineticsEntry'),
    (r'^kinetics/(?P<section>\w+)/(?P<subsection>.+)/$', 'views.kinetics'),
    (r'^kinetics/(?P<section>\w+)/$', 'views.kinetics'),
    
)
