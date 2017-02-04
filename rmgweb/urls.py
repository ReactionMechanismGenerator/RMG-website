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
from django.conf import settings
import django
import django.views.static
import django.views.defaults
import os

import rmgweb
import rmgweb.main.views
import rmgweb.database.views
import rmgweb.rmg.views


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # Example:
    # url(r'^website/', include('website.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    
    # Restart the django processes in the webserver
    url(r'^restart$', rmgweb.main.views.restartWSGI),
    # Show debug info
    url(r'^debug$', rmgweb.main.views.debug),
    
    # The RMG website homepage
    url(r'^$', rmgweb.main.views.index),
    
    # The privacy policy
    url(r'^privacy$', rmgweb.main.views.privacy),
    
    # Version information
    url(r'^version$', rmgweb.main.views.version),
    
    # Additional resources page
    url(r'^resources$', rmgweb.main.views.resources),

    # User account management
    url(r'^login$', rmgweb.main.views.login),
    url(r'^logout$', rmgweb.main.views.logout),
    url(r'^profile$', rmgweb.main.views.editProfile),
    url(r'^signup', rmgweb.main.views.signup),
    
    url(r'^user/(?P<username>\w+)$', rmgweb.main.views.viewProfile),

    # Database
    url(r'^database/', include('rmgweb.database.urls')),

    # Pressure dependence
    url(r'^pdep/', include('rmgweb.pdep.urls')),

    # Molecule drawing
    url(r'^molecule/(?P<adjlist>[\S\s]+)$', rmgweb.main.views.drawMolecule),
    url(r'^group/(?P<adjlist>[\S\s]+)$', rmgweb.main.views.drawGroup),
    
    url(r'^adjacencylist/(?P<identifier>.*)$', rmgweb.main.views.getAdjacencyList),
    url(r'^cactus/(?P<query>.*)$', rmgweb.main.views.cactusResolver),
    url(r'^nistcas/(?P<inchi>.*)$', rmgweb.main.views.getNISTcas),

    # Molecule and solvation search,  group drawing webpages
    url(r'^molecule_search$', rmgweb.database.views.moleculeSearch),
    url(r'^solvation_search', rmgweb.database.views.solvationSearch),

    # RMG-Py Stuff
    url(r'^tools/', include('rmgweb.rmg.urls')),
    
    # RMG Input Form
    url(r'^input', rmgweb.rmg.views.input),
    
    # Documentation auto-rebuild
    url(r'^rebuild$', rmgweb.main.views.rebuild),

    # RMG regression tests Stuff
    url(r'^regression_tests/', include('rmgweb.regression_tests.urls')),

    # Remember to update the /media/robots.txt file to keep web-crawlers out of pages you don't want indexed.
    
]

# When developing in Django we generally don't have a web server available to
# serve static media; this code enables serving of static media by Django
# DO NOT USE in a production environment!
if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(.*)$', django.views.static.serve,
            {'document_root': settings.MEDIA_ROOT,
             'show_indexes': True, }
            ),
        url(r'^static/(.*)$', django.views.static.serve,
            {'document_root': settings.STATIC_ROOT,
             'show_indexes': True, }
            ),
        url(r'^database/export/(.*)$', django.views.static.serve,
            {'document_root': os.path.join(settings.PROJECT_PATH,
                                           '..',
                                           'database',
                                           'export'),
             'show_indexes': True, },
            ),
        url(r'^(robots\.txt)$', django.views.static.serve,
            {'document_root': settings.STATIC_ROOT}
            ),
        url(r'^500/$', django.views.defaults.server_error),
        url(r'^404/$', django.views.defaults.page_not_found),
    ]
