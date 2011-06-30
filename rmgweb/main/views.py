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
from django.http import HttpResponse, HttpResponseRedirect
import django.contrib.auth.views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from forms import *

def index(request):
    """
    The RMG website homepage.
    """
    return render_to_response('index.html', context_instance=RequestContext(request))

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
        if userForm.is_valid() and profileForm.is_valid():
            #userForm.save()
            #profileForm.save()
            return HttpResponseRedirect('/')
    else:
        userForm = UserSignupForm(error_class=DivErrorList)
        profileForm = UserProfileSignupForm(error_class=DivErrorList)

    return render_to_response('signup.html', {'userForm': userForm, 'profileForm': profileForm}, context_instance=RequestContext(request))

def viewProfile(request, username):
    """
    Called when the user wishes to view another user's profile. The other user
    is identified by his/her `username`. Note that viewing user profiles does
    not require authentication.
    """
    from rmgweb.pdep.models import Network
    user0 = User.objects.get(username=username)
    userProfile = user0.get_profile()
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
        if userForm.is_valid() and profileForm.is_valid():
            userForm.save()
            profileForm.save()
            return HttpResponseRedirect('/') # Redirect after POST
    else:
        userForm = UserForm(instance=request.user, error_class=DivErrorList)
        profileForm = UserProfileForm(instance=user_profile, error_class=DivErrorList)

    return render_to_response('editProfile.html', {'userForm': userForm, 'profileForm': profileForm}, context_instance=RequestContext(request))

def drawMolecule(request, adjlist):
    """
    Returns an image of the provided adjacency list `adjlist` for a molecule.
    Note that the newline character cannot be represented in a URL;
    semicolons should be used instead.
    """
    from rmgpy.molecule import Molecule
    from rmgpy.molecule_draw import drawMolecule

    response = HttpResponse(mimetype="image/png")

    adjlist = str(adjlist.replace(';', '\n'))
    molecule = Molecule().fromAdjacencyList(adjlist)
    surface, cr, rect = drawMolecule(molecule, surface='png')
    surface.write_to_png(response)

    return response

def drawGroup(request, adjlist):
    """
    Returns an image of the provided adjacency list `adjlist` for a molecular
    pattern. Note that the newline character cannot be represented in a URL;
    semicolons should be used instead.
    """
    from rmgpy.group import Group
    import pydot

    response = HttpResponse(mimetype="image/png")

    adjlist = str(adjlist.replace(';', '\n'))
    pattern = Group().fromAdjacencyList(adjlist)

    graph = pydot.Dot(graph_type='graph', dpi=52)
    for index, atom in enumerate(pattern.atoms):
        atomType = '%s ' % atom.label if atom.label != '' else ''
        atomType += ','.join([atomType.label for atomType in atom.atomType])
        graph.add_node(pydot.Node(name='%i' % (index+1), label=atomType, fontname='Helvetica', fontsize=16))
    for atom1, bonds in pattern.bonds.iteritems():
        for atom2, bond in bonds.iteritems():
            index1 = pattern.atoms.index(atom1)
            index2 = pattern.atoms.index(atom2)
            if index1 < index2:
                bondType = ','.join([order for order in bond.order])
                graph.add_edge(pydot.Edge(
                    src = '%i' % (index1+1),
                    dst = '%i' % (index2+1),
                    label = bondType,
                    fontname='Helvetica', fontsize = 16,
                ))

    response.write(graph.create(prog='neato', format='png'))

    return response
