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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
import django.contrib.auth.views
from django.core.urlresolvers import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import urllib, urllib2

from forms import *

def index(request):
    """
    The RMG website homepage.
    """
    from rmgpy import __version__
    return render_to_response('index.html', {'version': __version__}, context_instance=RequestContext(request))

def privacy(request):
    """
    The RMG privacy policy.
    """
    return render_to_response('privacy.html',
                              {'admins': settings.ADMINS},
                              context_instance=RequestContext(request))

def version(request):
    """
    Version information for RMG-website, RMG-Py, and RMG-database
    """
    return render_to_response('version.html', context_instance=RequestContext(request))

def login(request):
    """
    Called when the user wishes to log in to his/her account.
    """
    return django.contrib.auth.views.login(request, template_name='login.html')

def logout(request):
    """
    Called when the user wishes to log out of his/her account.
    """
    return django.contrib.auth.views.logout(request, template_name='logout.html')

def signup(request):
    """
    Called when the user wishes to sign up for an account.
    """
    if request.method == 'POST':
        userForm = UserSignupForm(request.POST, error_class=DivErrorList)
        userForm.fields['first_name'].required = True
        userForm.fields['last_name'].required = True
        userForm.fields['email'].required = True
        profileForm = UserProfileSignupForm(request.POST, error_class=DivErrorList)
        passwordForm = PasswordCreateForm(request.POST, username='', error_class=DivErrorList)
        if userForm.is_valid() and profileForm.is_valid() and passwordForm.is_valid():
            username = userForm.cleaned_data['username']
            password = passwordForm.cleaned_data['password']
            userForm.save()
            passwordForm.username = username
            passwordForm.save()
            user = auth.authenticate(username=username, password=password)
            user_profile = UserProfile.objects.get_or_create(user=user)[0]
            profileForm2 = UserProfileSignupForm(request.POST, instance=user_profile, error_class=DivErrorList)
            profileForm2.save()
            auth.login(request, user)
            return HttpResponseRedirect('/')
    else:
        userForm = UserSignupForm(error_class=DivErrorList)
        profileForm = UserProfileSignupForm(error_class=DivErrorList)
        passwordForm = PasswordCreateForm(error_class=DivErrorList)
        
    return render_to_response('signup.html', {'userForm': userForm, 'profileForm': profileForm, 'passwordForm': passwordForm}, context_instance=RequestContext(request))

def viewProfile(request, username):
    """
    Called when the user wishes to view another user's profile. The other user
    is identified by his/her `username`. Note that viewing user profiles does
    not require authentication.
    """
    from rmgweb.pdep.models import Network
    user0 = User.objects.get(username=username)
    userProfile = user0.userprofile
    networks = Network.objects.filter(user=user0)
    return render_to_response('viewProfile.html', {'user0': user0, 'userProfile': userProfile, 'networks': networks}, context_instance=RequestContext(request))

@login_required
def editProfile(request):
    """
    Called when the user wishes to edit his/her user profile.
    """
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    if request.method == 'POST':
        userForm = UserForm(request.POST, instance=request.user, error_class=DivErrorList)
        profileForm = UserProfileForm(request.POST, instance=user_profile, error_class=DivErrorList)
        passwordForm = PasswordChangeForm(request.POST, username=request.user.username, error_class=DivErrorList)
        if userForm.is_valid() and profileForm.is_valid() and passwordForm.is_valid():
            userForm.save()
            profileForm.save()
            passwordForm.save()
            return HttpResponseRedirect(reverse(viewProfile, kwargs={'username': request.user.username})) # Redirect after POST
    else:
        userForm = UserForm(instance=request.user, error_class=DivErrorList)
        profileForm = UserProfileForm(instance=user_profile, error_class=DivErrorList)
        passwordForm = PasswordChangeForm(error_class=DivErrorList)
        
    return render_to_response('editProfile.html', {'userForm': userForm, 'profileForm': profileForm, 'passwordForm': passwordForm}, context_instance=RequestContext(request))

def getAdjacencyList(request, identifier):
    """
    Returns an adjacency list of the species corresponding to `identifier`.
    
    `identifier` should be something recognized by NCI resolver, eg.
    SMILES, InChI, CACTVS, chemical name, etc.
    
    The NCI resolver has some bugs regarding reading SMILES of radicals.
    E.g. it thinks CC[CH] is CCC, so we first try to use the identifier
    directly as a SMILES string, and only pass it through the resolver
    if that does not work. 
    
    For specific problematic cases, the NCI resolver is bypassed and the SMILES
    is returned from a dictionary of values. For O2, the resolver returns the singlet
    form which is inert in RMG. For oxygen, the resolver returns 'O' as the SMILES, which
    is the SMILES for water.
    """
    if identifier.strip() == '':
        return HttpResponse('', content_type="text/plain")
    from rmgpy.molecule.molecule import Molecule
    molecule = Molecule()
    try:
        # try using the string as a SMILES directly
        molecule.fromSMILES(str(identifier))
    except (IOError, ValueError):
        known_names = {'O2':'[O][O]',
                       'oxygen':'[O][O]'}
        key = str(identifier)
        if key in known_names:
            smiles = known_names[key]
        else:
            # try converting it to a SMILES using the NCI chemical resolver 
            url = "http://cactus.nci.nih.gov/chemical/structure/{0}/smiles".format(urllib.quote(identifier))
            try:
                f = urllib2.urlopen(url, timeout=5)
            except urllib2.URLError, e:
                return HttpResponseNotFound("404: Couldn't identify {0}. NCI resolver responded {1} to request for {2}".format(identifier, e, url))
            smiles = f.read()
        molecule.fromSMILES(smiles)
    
    adjlist = molecule.toAdjacencyList(removeH=False)
    return HttpResponse(adjlist, content_type="text/plain")

def getNISTcas(request, inchi):
    """
    Get the CAS number as used by NIST, from an InChI
    """
    url = "http://webbook.nist.gov/cgi/inchi/{0}".format(urllib.quote(inchi))
    try:
        f = urllib2.urlopen(url, timeout=5)
    except urllib2.URLError, e:
        return HttpResponseNotFound("404: Couldn't identify {0}. NIST responded {1} to request for {2}".format(inchi, e, url))
    searcher = re.compile('<li><a href="/cgi/inchi\?GetInChI=C(\d+)')
    for line in f:
        m = searcher.match(line)
        if m:
            number = m.group(1)
            break
    else:
        return HttpResponseNotFound("404: Couldn't identify {0}. Couldn't locate CAS number in page at {1}".format(inchi, url))
    return HttpResponse(number, content_type="text/plain")
    
def cactusResolver(request, query):
    """
    Forwards the query to the cactus.nci.nih.gov/chemical/structure resolver.
    
    The reason we have to forward the request from our own server is so that we can 
    use it via ajax, avoiding cross-domain scripting security constraints.
    """
    if query.strip() == '':
        return HttpResponse('', content_type="text/plain")
   
    url = "http://cactus.nci.nih.gov/chemical/structure/{0}".format(urllib.quote(query))
    try:
        f = urllib2.urlopen(url, timeout=5)
    except urllib2.URLError, e:
        return HttpResponseNotFound("404: Couldn't identify {0}. NCI resolver responded {1} to request for {2}".format(query, e, url))
    response = f.read()
    return HttpResponse(response, content_type="text/plain")
    
def drawMolecule(request, adjlist):
    """
    Returns an image of the provided adjacency list `adjlist` for a molecule.
    urllib is used to quote/unquote the adjacency list.
    """
    from rmgpy.molecule import Molecule
    from rmgpy.molecule.draw import MoleculeDrawer

    adjlist = str(urllib.unquote(adjlist))
    molecule = Molecule().fromAdjacencyList(adjlist)

    surface, cr, rect = MoleculeDrawer().draw(molecule, format='png')
    response = HttpResponse(content_type="image/png")
    surface.write_to_png(response)
    return response

def drawGroup(request, adjlist):
    """
    Returns an image of the provided adjacency list `adjlist` for a molecular
    pattern.  urllib is used to quote/unquote the adjacency list.
    """
    from rmgpy.molecule.group import Group
    import pydot

    response = HttpResponse(content_type="image/png")

    adjlist = str(urllib.unquote(adjlist))
    pattern = Group().fromAdjacencyList(adjlist)

    graph = pydot.Dot(graph_type='graph', dpi="52")
    for index, atom in enumerate(pattern.atoms):
        atomType = '%s ' % atom.label if atom.label != '' else ''
        atomType += ','.join([atomType.label for atomType in atom.atomType])
        graph.add_node(pydot.Node(name='%i' % (index+1), label=atomType, fontname='Helvetica', fontsize="16"))
    for atom1 in pattern.atoms:
        for atom2, bond in atom1.bonds.iteritems():
            index1 = pattern.atoms.index(atom1)
            index2 = pattern.atoms.index(atom2)
            if index1 < index2:
                bondType = ','.join([order for order in bond.order])
                graph.add_edge(pydot.Edge(
                    src = '%i' % (index1+1),
                    dst = '%i' % (index2+1),
                    label = bondType,
                    fontname='Helvetica', fontsize = "16",
                ))

    response.write(graph.create(prog='neato', format='png'))

    return response

@login_required
def restartWSGI(request):
    if request.META['mod_wsgi.process_group'] != '':
        import signal, os, sys
        restart_filename = os.path.join(os.path.dirname(request.META['SCRIPT_FILENAME']), 'restart')
        print >> sys.stderr, "Touching {0} to trigger a restart all daemon processes".format(restart_filename)
        with file(restart_filename, 'a'):
            os.utime(restart_filename, None)
        #os.kill(os.getpid(), signal.SIGINT)
    return HttpResponseRedirect('/')

def debug(request):
    import sys
    import scipy, numpy
    print >> sys.stderr, "scipy module is {0}".format(scipy)
    print >> sys.stderr, "numpy.finfo(float) = {0}".format(numpy.finfo(float))
    print >> sys.stderr, "Failing on purpose to trigger a debug screen"
    assert False, "Intentional failure to trigger debug screen."

@csrf_exempt
def rebuild(request):
    import os
    rebuild_filename = os.path.join(os.path.dirname(request.META['DOCUMENT_ROOT']), 'trigger/rebuild')
    with file(rebuild_filename, 'a'):
            os.utime(rebuild_filename, None)
    return HttpResponseRedirect('/')
