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

"""
This module contains custom context processors and related functions.
These are activated in the `context_processors` block of `settings.py`.
"""

import os.path
import subprocess

import rmgpy

import rmgweb
from rmgweb.settings import PROJECT_PATH

context = None


def get_announcement(request):
    """
    Context processor to get an announcement message if it exists.
    """

    path = os.path.join(os.path.dirname(PROJECT_PATH), 'announcement.txt')
    msg_context = {}

    if os.path.isfile(path):
        with open(path, 'r') as f:
            lines = f.readlines()
        message = '<br>'.join(lines).strip()
        if message:
            msg_context = {'announcement': message}

    return msg_context


def get_git_commit(modulePath):
    """
    Get git commit hash for given repository path.
    """
    commit = ''
    date = ''
    subject = ''
    body = ''

    if os.path.exists(os.path.join(modulePath, '..', '.git')):
        try:
            lines = subprocess.check_output(['git',
                                             'log',
                                             '--format=%H%n%cD%n%s%n%b', '-1'],
                                            cwd=modulePath).decode('utf-8').splitlines()
            commit = lines[0]
            date = lines[1]
            subject = lines[2]
            body = '\n'.join(lines[3:])
        except:
            pass

    return commit, date, subject, body


def get_commits(request):
    """
    Context processor to return git commits for RMG-Py,
    RMG-database, and RMG-website.
    """

    global context

    if not context:
        py_path = os.path.dirname(rmgpy.__file__)
        data_path = rmgpy.settings['database.directory']
        web_path = os.path.dirname(rmgweb.__file__)

        py_commit, py_date, py_subject, py_body = get_git_commit(py_path)
        data_commit, data_date, data_subject, data_body = get_git_commit(data_path)
        web_commit, web_date, web_subject, web_body = get_git_commit(web_path)

        py_date_short = ' '.join(py_date.split()[1:4])
        data_date_short = ' '.join(data_date.split()[1:4])
        web_date_short = ' '.join(web_date.split()[1:4])

        context = {'pc': py_commit, 'pd': py_date, 'pds': py_date_short, 'ps': py_subject, 'pb': py_body,
                   'dc': data_commit, 'dd': data_date, 'dds': data_date_short, 'ds': data_subject, 'db': data_body,
                   'wc': web_commit, 'wd': web_date, 'wds': web_date_short, 'ws': web_subject, 'wb': web_body}

    return context
