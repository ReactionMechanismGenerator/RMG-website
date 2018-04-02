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

import os.path
import subprocess
import rmgpy
import rmgweb

context = None

def getGitCommit(modulePath):
    """
    Get git commit hash for given repository path.
    """
    commit =''
    date = ''
    subject = ''
    body = ''
    
    if os.path.exists(os.path.join(modulePath,'..','.git')):
        try:
            lines = subprocess.check_output(['git', 'log',
                                            '--format=%H%n%cD%n%s%n%b', '-1'],
                                            cwd=modulePath).splitlines()
            commit = lines[0]
            date = lines[1]
            subject = lines[2]
            body = '\n'.join(lines[3:])
        except:
            pass
        
    return commit, date, subject, body

def getCommits(request):
    """
    Context processor to return git commits for RMG-Py, 
    RMG-database, and RMG-website.
    """
    
    global context
    
    if not context:
        pyPath = os.path.dirname(rmgpy.__file__)
        dataPath = rmgpy.settings['database.directory']
        webPath = os.path.dirname(rmgweb.__file__)
        
        pyCommit, pyDate, pySubject, pyBody = getGitCommit(pyPath)
        dataCommit, dataDate, dataSubject, dataBody = getGitCommit(dataPath)
        webCommit, webDate, webSubject, webBody = getGitCommit(webPath)
        
        pyDateShort = ' '.join(pyDate.split()[1:4])
        dataDateShort = ' '.join(dataDate.split()[1:4])
        webDateShort = ' '.join(webDate.split()[1:4])
        
        context = {'pc':pyCommit, 'pd':pyDate, 'pds':pyDateShort, 'ps':pySubject, 'pb':pyBody,
                   'dc':dataCommit, 'dd':dataDate, 'dds':dataDateShort, 'ds':dataSubject, 'db':dataBody,
                   'wc':webCommit, 'wd':webDate, 'wds':webDateShort, 'ws':webSubject, 'wb':webBody}
        
    return context

