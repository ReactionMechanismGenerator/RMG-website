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

import os

import django
import django.views.defaults
import django.views.static
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import include, reverse_lazy, re_path

import rmgweb
import rmgweb.database.views
import rmgweb.main.views
import rmgweb.rmg.views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # Example:
    # url(r'^website/', 'website.foo.urls'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', 'django.contrib.admindocs.urls'),
    # Uncomment the next line to enable the admin:
    re_path(r'^admin/', admin.site.urls),

    # Restart the django processes in the webserver
    re_path(r'^restart$', rmgweb.main.views.restartWSGI, name='restart-wsgi'),

    # Show debug info
    re_path(r'^debug$', rmgweb.main.views.debug, name='debug'),

    # The RMG website homepage
    re_path(r'^$', rmgweb.main.views.index, name='index'),

    # The terms of use
    re_path(r'^terms$', rmgweb.main.views.terms),

    # The privacy policy
    re_path(r'^privacy$', rmgweb.main.views.privacy, name='privacy'),

    # Version information
    re_path(r'^version$', rmgweb.main.views.version, name='version'),

    # Additional resources page
    re_path(r'^resources$', rmgweb.main.views.resources, name='resources'),

    # User account management
    re_path(r'^login$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    re_path(r'^logout$', auth_views.LogoutView.as_view(template_name='logout.html'),
            name='logout'),
    re_path(r'^profile$', rmgweb.main.views.editProfile, name='edit-profile'),
    re_path(r'^signup', rmgweb.main.views.signup, name='signup'),

    re_path(r'^user/(?P<username>\w+)$', rmgweb.main.views.viewProfile, name='view-profile'),

    # User password reset
    re_path(r'^password_reset$',
            auth_views.PasswordResetView.as_view(template_name='password_reset_form.html',
                                                 email_template_name='password_reset_email.html',
                                                 subject_template_name='password_reset_subject.txt',
                                                 success_url=reverse_lazy('password_reset_done')),
            name='password_reset'),
    re_path(r'^password_reset/done$',
            auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
            name='password_reset_done'),
    re_path(r'^password_reset/confirm/(?P<uidb64>\S+)/(?P<token>\S+)/$',
            auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
            name='password_reset_confirm'),
    re_path(r'^password_reset/complete$',
            auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
            name='password_reset_complete'),

    # Database
    re_path(r'^database/', include("rmgweb.database.urls")),

    # Pressure dependence
    re_path(r'^pdep/', include("rmgweb.pdep.urls")),

    # Molecule drawing
    re_path(r'^molecule/(?P<adjlist>[\S\s]+)/(?P<format>\w+)$', rmgweb.main.views.drawMolecule, name='draw-molecule'),
    re_path(r'^molecule/(?P<adjlist>[\S\s]+)$', rmgweb.main.views.drawMolecule, name='draw-molecule'),
    re_path(r'^group/(?P<adjlist>[\S\s]+)/(?P<format>\w+)$', rmgweb.main.views.drawGroup, name='draw-group'),
    re_path(r'^group/(?P<adjlist>[\S\s]+)$', rmgweb.main.views.drawGroup, name='draw-group'),

    re_path(r'^adjacencylist/(?P<identifier>.*)$', rmgweb.main.views.getAdjacencyList, name='get-adjacency-list'),
    re_path(r'^cactus/(?P<query>.*)$', rmgweb.main.views.cactusResolver, name='cactus-resolver'),
    re_path(r'^nistcas/(?P<inchi>.*)$', rmgweb.main.views.getNISTcas, name='get-nist-cas'),

    # Molecule search,  group drawing webpages
    re_path(r'^molecule_search$', rmgweb.database.views.moleculeSearch, name='molecule-search'),

    # RMG-Py Stuff
    re_path(r'^tools/', include("rmgweb.rmg.urls")),

    # Documentation auto-rebuild
    re_path(r'^rebuild$', rmgweb.main.views.rebuild, name='rebuild'),

    # Remember to update the /media/robots.txt file to keep web-crawlers out of pages you don't want indexed.
]

# Set custom 500 handler
handler500 = 'rmgweb.main.views.custom500'

# When developing in Django we generally don't have a web server available to
# serve static media; this code enables serving of static media by Django
# DO NOT USE in a production environment!
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(.*)$', django.views.static.serve,
            {'document_root': settings.MEDIA_ROOT,
             'show_indexes': True, }
            ),
        re_path(r'^static/(.*)$', django.views.static.serve,
            {'document_root': settings.STATIC_ROOT,
             'show_indexes': True, }
            ),
        re_path(r'^database/export/(.*)$', django.views.static.serve,
            {'document_root': os.path.join(settings.PROJECT_PATH,
                                           '..',
                                           'database',
                                           'export'),
             'show_indexes': True, },
            ),
        re_path(r'^(robots\.txt)$', django.views.static.serve,
            {'document_root': settings.STATIC_ROOT}
            ),
        re_path(r'^500/$', django.views.defaults.server_error),
        re_path(r'^404/$', django.views.defaults.page_not_found),
    ]
