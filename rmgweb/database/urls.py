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
from rmgweb.database import views
urlpatterns = [ 

    # Database homepage
    url(r'^$', views.index),
    
    # Load the whole database into memory
    url(r'^load/?$', views.load),
    
    # Export to an RMG-Java database
    url(r'^export_(?P<type>zip|tar\.gz)/?$', views.export),

    # Thermodynamics database
    url(r'^thermo/$', views.thermo),
    url(r'^thermo/search/$', views.moleculeSearch),
    url(r'^thermo/molecule/(?P<adjlist>[\S\s]+)$', views.thermoData),
    url(r'^thermo/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/$', views.thermoEntry),
    url(r'^thermo/(?P<section>\w+)/(?P<subsection>.+)/(?P<adjlist>[\S\s]+)/new$', views.thermoEntryNew),
    url(r'^thermo/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/edit$', views.thermoEntryEdit),
    url(r'^thermo/(?P<section>\w+)/(?P<subsection>.+)/$', views.thermo),
    url(r'^thermo/(?P<section>\w+)/$', views.thermo),
    
    # Transport database
    url(r'^transport/$', views.transport),
    url(r'^transport/search/$', views.moleculeSearch),
    url(r'^transport/molecule/(?P<adjlist>[\S\s]+)$', views.transportData),
    url(r'^transport/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/$', views.transportEntry),
    url(r'^transport/(?P<section>\w+)/(?P<subsection>.+)/$', views.transport),
    url(r'^transport/(?P<section>\w+)/$', views.transport),    
    
    # solvation database
    url(r'^solvation/$', views.solvation),
    url(r'^solvation/search/$', views.solvationSearch),    
    url(r'^solvation/results/solute=(?P<solute_adjlist>[\S\s]+)__solvent=(?P<solvent>[\S\s]+)$', views.solvationData),    
    url(r'^solvation/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/$', views.solvationEntry),
    url(r'^solvation/(?P<section>\w+)/(?P<subsection>.+)/$', views.solvation),
    url(r'^solvation/(?P<section>\w+)/$', views.solvation),   
    
    # statmech database
    url(r'^statmech/$', views.statmech),
    url(r'^statmech/search/$', views.moleculeSearch),
    url(r'^statmech/molecule/(?P<adjlist>[\S\s]+)$', views.statmechData),
    url(r'^statmech/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/$', views.statmechEntry),
    url(r'^statmech/(?P<section>\w+)/(?P<subsection>.+)/$', views.statmech),
    url(r'^statmech/(?P<section>\w+)/$', views.statmech), 
    
    # Kinetics database
    url(r'^kinetics/$', views.kinetics),
    url(r'^kinetics/search/$', views.kineticsSearch),
    url(r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__product3=(?P<product3>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsResults),
    url(r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__product3=(?P<product3>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsResults),
    url(r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__reactant3=(?P<reactant3>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsResults),
    url(r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsResults),
    url(r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsResults),
    url(r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsResults),
    url(r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsResults),
    url(r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsResults),
    url(r'^kinetics/results/reactant1=(?P<reactant1>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsResults),
    url(r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__product3=(?P<product3>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsData),
    url(r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__product3=(?P<product3>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsData),
    url(r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__reactant3=(?P<reactant3>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsData),
    url(r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsData),
    url(r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsData),
    url(r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsData),
    url(r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsData),
    url(r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsData),
    url(r'^kinetics/reaction/reactant1=(?P<reactant1>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsData),
    
    url(r'^kinetics/families/(?P<family>[^/]+)/(?P<estimator>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsGroupEstimateEntry),
    url(r'^kinetics/families/(?P<family>[^/]+)/(?P<estimator>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__product1=(?P<product1>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsGroupEstimateEntry),
    url(r'^kinetics/families/(?P<family>[^/]+)/(?P<estimator>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__product2=(?P<product2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsGroupEstimateEntry),
    url(r'^kinetics/families/(?P<family>[^/]+)/(?P<estimator>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__product1=(?P<product1>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsGroupEstimateEntry),
    url(r'^kinetics/families/(?P<family>[^/]+)/(?P<estimator>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__reactant2=(?P<reactant2>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsGroupEstimateEntry),
    url(r'^kinetics/families/(?P<family>[^/]+)/(?P<estimator>[^/]+)/reactant1=(?P<reactant1>[\S\s]+)__res=(?P<resonance>[\S\s]+)$', views.kineticsGroupEstimateEntry),
    
    url(r'^kinetics/families/(?P<family>[^/]+)/(?P<type>\w+)/new$', views.kineticsEntryNew),
    url(r'^kinetics/families/(?P<family>[^/]+)/untrained/$', views.kineticsUntrained),
    
    url(r'^kinetics/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>\d+)/edit$', views.kineticsEntryEdit),
    url(r'^kinetics/(?P<section>\w+)/(?P<subsection>.+)/(?P<index>-?\d+)/$', views.kineticsEntry),
    url(r'^kinetics/(?P<section>\w+)/(?P<subsection>.+)/$', views.kinetics),
    url(r'^kinetics/(?P<section>\w+)/$', views.kinetics),
    
    # Molecule Information Page
    url(r'^molecule/(?P<adjlist>[\S\s]+)$', views.moleculeEntry),
    
    #Group Information Page
    url(r'^group/(?P<adjlist>[\S\s]+)$', views.groupEntry),

    # Eni detergent-dirt binding strength
    url(r'^eni', views.EniSearch),
    
    # Remember to update the /media/robots.txt file to keep web-crawlers out of pages you don't want indexed.
]
