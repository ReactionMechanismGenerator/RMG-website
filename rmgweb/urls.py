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
from django.conf import settings
import os

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('rmgweb',
    # Example:
    # (r'^website/', include('website.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    # Restart the django processes in the webserver
    (r'^restart$', 'main.views.restartWSGI'),
    # Show debug info
    (r'^debug$', 'main.views.debug'),
    
    # The RMG website homepage
    (r'^$', 'main.views.index'),
    
    # The privacy policy
    (r'^privacy$', 'main.views.privacy'),
    
    # User account management
    (r'^login$', 'main.views.login'),
    (r'^logout$', 'main.views.logout'),
    (r'^profile$', 'main.views.editProfile'),
    (r'^signup', 'main.views.signup'),
    
    (r'^user/(?P<username>\w+)$', 'main.views.viewProfile'),

    # Database
    (r'^database/', include('database.urls')),

    # Pressure dependence
    (r'^measure/', include('pdep.urls')),

    # Molecule drawing
    (r'^molecule/(?P<adjlist>[\S\s]+)$', 'main.views.drawMolecule'),
    (r'^group/(?P<adjlist>[\S\s]+)$', 'main.views.drawGroup'),
    
    (r'^adjacencylist/(?P<identifier>.*)$', 'main.views.getAdjacencyList'),
    (r'^cactus/(?P<query>.*)$', 'main.views.cactusResolver'),
    (r'^nistcas/(?P<inchi>.*)$', 'main.views.getNISTcas'),

    # Molecule and solvation search,  group drawing webpages
    (r'^molecule_search$', 'database.views.moleculeSearch'),
    (r'^group_draw$', 'database.views.groupDraw'),
    (r'^solvation_search', 'database.views.solvationSearch'),

    # RMG-Py Stuff
    (r'^simulate/', include('rmg.urls')),
    
    # Documentation auto-rebuild
    (r'^rebuild$', 'main.views.rebuild'),

    # Remember to update the /media/robots.txt file to keep web-crawlers out of pages you don't want indexed.
    
)

# When developing in Django we generally don't have a web server available to
# serve static media; this code enables serving of static media by Django
# DO NOT USE in a production environment!
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(settings.PROJECT_PATH, 'media'),
             'show_indexes': True, }
        ),
        (r'^database/export/(.*)$',
         'django.views.static.serve',
         {'document_root': os.path.join(settings.PROJECT_PATH,
                                        '..',
                                        'database',
                                        'export'),
          'show_indexes': True,
          },
         ),
        (r'^(robots\.txt)$', 'django.views.static.serve',
            {'document_root': os.path.join(settings.PROJECT_PATH, 'media')}
        ),
    )
