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
import re
import sys
import urllib

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render
from django.template import loader
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from rmgpy.molecule.atomtype import allElements as SUPPORTED_ELEMENTS

from rmgweb.main.forms import *


ELEMENTS = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar',
            'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br',
            'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te',
            'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm',
            'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn',
            'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr',
            'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og', 'X']

VAL_ELEC = {'H': 1, 'He': 2, 'C': 4, 'N': 5, 'O': 6, 'F': 7, 'Ne': 8,
            'Si': 4, 'S': 6, 'Cl': 7, 'Ar': 8, 'Br': 7, 'I': 7, }

SUPPORTED_ELEMENTS_ONE_LETTER, SUPPORTED_ELEMENTS_TWO_LETTERS = [], []

for element in SUPPORTED_ELEMENTS:
    if len(element) == 1:
        SUPPORTED_ELEMENTS_ONE_LETTER.append(element)
    elif len(element) == 2:
        SUPPORTED_ELEMENTS_TWO_LETTERS.append(element)


def index(request):
    """
    The RMG website homepage.
    """
    from rmgpy import __version__
    return render(request, 'index.html', {'version': __version__})


def privacy(request):
    """
    The RMG privacy policy.
    """
    return render(request, 'privacy.html', {'admins': settings.ADMINS})


def version(request):
    """
    Version information for RMG-website, RMG-Py, and RMG-database
    """
    return render(request, 'version.html')


def resources(request):
    """
    Page for accessing RMG resources, including papers and presentations
    """
    folder = os.path.join(settings.STATIC_ROOT, 'presentations')
    files = []

    if os.path.isdir(folder):
        files = os.listdir(folder)
        to_remove = []
        for f in files:
            if not os.path.isfile(os.path.join(folder, f)):
                # Remove any directories
                to_remove.append(f)
            elif f[0] == '.':
                # Remove any hidden files
                to_remove.append(f)
        for item in to_remove:
            files.remove(item)

    # Parse file names for information to display on webpage
    presentations = []
    if files:
        files.sort()
        for f in files:
            name = os.path.splitext(f)[0]
            parts = name.split('_')
            date = parts[0]
            date = date[0:4] + '-' + date[4:6] + '-' + date[6:]
            title = ' '.join(parts[1:])
            title = title.replace('+', ' and ')
            presentations.append((title, date, f))

    return render(request, 'resources.html', {'presentations': presentations})


def signup(request):
    """
    Called when the user wishes to sign up for an account.
    """
    if request.method == 'POST':
        user_form = UserSignupForm(request.POST, error_class=DivErrorList)
        user_form.fields['first_name'].required = True
        user_form.fields['last_name'].required = True
        user_form.fields['email'].required = True
        profile_form = UserProfileSignupForm(request.POST, error_class=DivErrorList)
        password_form = PasswordCreateForm(request.POST, username='', error_class=DivErrorList)
        if user_form.is_valid() and profile_form.is_valid() and password_form.is_valid():
            username = user_form.cleaned_data['username']
            password = password_form.cleaned_data['password']
            user_form.save()
            password_form.username = username
            password_form.save()
            user = auth.authenticate(username=username, password=password)
            user_profile = UserProfile.objects.get_or_create(user=user)[0]
            profile_form2 = UserProfileSignupForm(request.POST, instance=user_profile, error_class=DivErrorList)
            profile_form2.save()
            auth.login(request, user)
            return HttpResponseRedirect('/')
    else:
        user_form = UserSignupForm(error_class=DivErrorList)
        profile_form = UserProfileSignupForm(error_class=DivErrorList)
        password_form = PasswordCreateForm(error_class=DivErrorList)

    return render(request, 'signup.html', {'userForm': user_form, 'profileForm': profile_form, 'passwordForm': password_form})


def viewProfile(request, username):
    """
    Called when the user wishes to view another user's profile. The other user
    is identified by his/her `username`. Note that viewing user profiles does
    not require authentication.
    """
    from rmgweb.pdep.models import Network
    user0 = User.objects.get(username=username)
    user_profile = user0.userprofile
    networks = Network.objects.filter(user=user0)
    return render(request, 'viewProfile.html', {'user0': user0, 'userProfile': user_profile, 'networks': networks})


@login_required
def editProfile(request):
    """
    Called when the user wishes to edit his/her user profile.
    """
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user, error_class=DivErrorList)
        profile_form = UserProfileForm(request.POST, instance=user_profile, error_class=DivErrorList)
        password_form = PasswordChangeForm(request.POST, username=request.user.username, error_class=DivErrorList)
        if user_form.is_valid() and profile_form.is_valid() and password_form.is_valid():
            user_form.save()
            profile_form.save()
            password_form.save()
            return HttpResponseRedirect(reverse('view-profile', kwargs={'username': request.user.username}))  # Redirect after POST
    else:
        user_form = UserForm(instance=request.user, error_class=DivErrorList)
        profile_form = UserProfileForm(instance=user_profile, error_class=DivErrorList)
        password_form = PasswordChangeForm(error_class=DivErrorList)

    return render(request, 'editProfile.html', {'userForm': user_form, 'profileForm': profile_form, 'passwordForm': password_form})


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
    from rmgpy.molecule import Molecule
    from rmgpy.exceptions import AtomTypeError
    from ssl import SSLError

    known_names = {
        'o2': '[O][O]',
        'oxygen': '[O][O]',
        'benzyl': '[CH2]c1ccccc1',
        'phenyl': '[c]1ccccc1',
    }

    # Ensure that input is a string
    identifier = identifier.strip()

    # Return empty string for empty input
    if identifier == "":
        return HttpResponse("", content_type="text/plain", charset='utf-8')

    molecule = Molecule()

    # Check if identifier is an InChI string
    if identifier.startswith('InChI=1'):
        try:
            molecule.from_inchi(identifier)
        except AtomTypeError as e:
            return analyze_atomtype_error(f'{e}')
        except KeyError as e:
            return analyze_element_error(f'{e}')
    elif identifier.lower() in known_names:
        molecule.from_smiles(known_names[identifier.lower()])
    else:
        try:
            # Try parsing as a SMILES string
            molecule.from_smiles(identifier)
        except AtomTypeError as e:
            return analyze_atomtype_error(f'{e}')
        except KeyError as e:
            return analyze_element_error(f'{e}')
        except (IOError, ValueError):
            # Try converting it to a SMILES using the NCI chemical resolver
            url = "https://cactus.nci.nih.gov/chemical/structure/{0}/smiles".format(urllib.parse.quote(identifier))
            try:
                f = urllib.request.urlopen(url, timeout=5)
            except urllib.error.URLError as e:
                return HttpResponse(f'Could not identify {identifier}. NCI resolver responded with {e}.', status=404)
            except SSLError:
                return HttpResponse('NCI resolver timed out, please try again.', status=504)
            smiles = f.read().decode('utf-8')
            try:
                molecule.from_smiles(smiles)
            except AtomTypeError as e:
                return analyze_atomtype_error(f'{e}')
            except KeyError as e:
                return analyze_element_error(f'{e}')
            except ValueError as e:
                return HttpResponse(f'{e}. This can be due to a bad target returned from backend searching engine'
                                    f'(https://cactus.nci.nih.gov) or a bad structure input.', status=500)

    adjlist = molecule.to_adjacency_list(remove_h=False)
    return HttpResponse(adjlist, content_type="text/plain")


def getNISTcas(request, inchi):
    """
    Get the CAS number as used by NIST, from an InChI
    """
    url = "http://webbook.nist.gov/cgi/inchi/{0}".format(urllib.parse.quote(inchi))
    searcher = re.compile('<li><a href="/cgi/inchi\?GetInChI=C(\d+)')
    try:
        with urllib.request.urlopen(url, timeout=5) as f:
            for line in f:
                m = searcher.match(line.decode('utf-8'))
                if m:
                    number = m.group(1)
                    return HttpResponse(number, content_type="text/plain")
            return HttpResponseNotFound("404: Couldn't identify {0}. Couldn't locate CAS number in page at {1}".format(inchi, url))
    except urllib.error.URLError as e:
        return HttpResponseNotFound("404: Couldn't identify {0}. NIST responded {1} to request for {2}".format(inchi, e, url))


def cactusResolver(request, query):
    """
    Forwards the query to the cactus.nci.nih.gov/chemical/structure resolver.

    The reason we have to forward the request from our own server is so that we can
    use it via ajax, avoiding cross-domain scripting security constraints.
    """
    from ssl import SSLError

    if query.strip() == '':
        return HttpResponse('', content_type="text/plain")

    url = "https://cactus.nci.nih.gov/chemical/structure/{0}".format(urllib.parse.quote(query))
    try:
        f = urllib.request.urlopen(url, timeout=5)
    except urllib.error.URLError as e:
        return HttpResponse("Could not process request. NCI resolver responded with {0}.".format(e), status=404)
    except SSLError:
        return HttpResponse('NCI resolver timed out, please try again.', status=504)
    response = f.read()
    return HttpResponse(response, content_type="text/plain")


def drawMolecule(request, adjlist, format='png'):
    """
    Returns an image of the provided adjacency list `adjlist` for a molecule.
    urllib is used to quote/unquote the adjacency list.
    """
    import io
    from rmgpy.molecule import Molecule
    from rmgpy.molecule.draw import MoleculeDrawer
    from rmgpy.molecule.adjlist import InvalidAdjacencyListError

    adjlist = urllib.parse.unquote(adjlist)

    try:
        molecule = Molecule().from_adjacency_list(adjlist)
    except (InvalidAdjacencyListError, ValueError):
        response = HttpResponseRedirect(static('img/invalid_icon.png'))
    else:
        if format == 'png':
            response = HttpResponse(content_type="image/png")
            surface, _, _ = MoleculeDrawer().draw(molecule, file_format='png')
            response.write(surface.write_to_png())
        elif format == 'svg':
            response = HttpResponse(content_type="image/svg+xml")
            svg_data = io.BytesIO()
            MoleculeDrawer().draw(molecule, file_format='svg', target=svg_data)
            response.write(svg_data.getvalue())
        else:
            response = HttpResponse('Image format not implemented.', status=501)

    return response


def drawGroup(request, adjlist, format='png'):
    """
    Returns an image of the provided adjacency list `adjlist` for a molecular
    group.  urllib is used to quote/unquote the adjacency list.
    """
    from rmgpy.molecule.group import Group
    from rmgpy.molecule.adjlist import InvalidAdjacencyListError

    adjlist = urllib.parse.unquote(adjlist)

    try:
        group = Group().from_adjacency_list(adjlist)
    except (InvalidAdjacencyListError, ValueError):
        response = HttpResponseRedirect(static('img/invalid_icon.png'))
    else:
        if format == 'png':
            response = HttpResponse(content_type="image/png")
            response.write(group.draw('png'))
        elif format == 'svg':
            response = HttpResponse(content_type="image/svg+xml")
            svg_data = group.draw('svg')
            # Remove the scale and rotate transformations applied by pydot
            svg_data = re.sub(r'scale\(0\.722222 0\.722222\) rotate\(0\) ', '', svg_data)
            response.write(svg_data)
        else:
            response = HttpResponse('Image format not implemented.', status=501)

    return response


@login_required
def restartWSGI(request):
    if request.META['mod_wsgi.process_group'] != '':
        restart_filename = os.path.join(os.path.dirname(request.META['SCRIPT_FILENAME']), 'restart')
        print("Touching {0} to trigger a restart all daemon processes".format(restart_filename), file=sys.stderr)
        with file(restart_filename, 'a'):
            os.utime(restart_filename, None)
        # os.kill(os.getpid(), signal.SIGINT)
    return HttpResponseRedirect('/')


def debug(request):
    import scipy
    import numpy as np
    print("scipy module is {0}".format(scipy), file=sys.stderr)
    print("numpy.finfo(float) = {0}".format(np.finfo(float)), file=sys.stderr)
    print("Failing on purpose to trigger a debug screen", file=sys.stderr)
    assert False, "Intentional failure to trigger debug screen."


@csrf_exempt
def rebuild(request):
    rebuild_filename = os.path.join(os.path.dirname(request.META['DOCUMENT_ROOT']), 'trigger/rebuild')
    with file(rebuild_filename, 'a'):
        os.utime(rebuild_filename, None)
    return HttpResponseRedirect('/')


def custom500(request):
    import traceback
    template = loader.get_template('500.html')
    etype, value = sys.exc_info()[:2]
    exception = ''.join(traceback.format_exception_only(etype, value)).strip()
    return HttpResponseServerError(template.render(context={'exception': exception}))


def analyze_element_error(error_message):
    # This should be a KeyError, the symbol of the element
    # is the only message it contains
    element = error_message.strip("'")
    if element in ELEMENTS:
        return HttpResponse(f'Element {element} has not been implemented in RMG-Py', status=501)
    else:
        return HttpResponse(f'Invalid element {error_message}, which cannot be found in the periodic table', status=400)


def analyze_atomtype_error(error_message):
    # This should be a AtomTypeError, which is raised during constructing the molecule instance
    # It could be either the AtomType is truly missing from RMG-database or the molecule information is fake
    # An Example of the error message:
    # Unable to determine atom type for atom O., which has 0 single bonds, 1 double bonds to C, 0 double bonds
    # to O, 0 double bonds to S, 0 triple bonds, 0 benzene bonds, 0 lone pairs, and 1 charge.
    # Example: Unable to determine atom type for atom N
    atom_type = error_message.split(',')[0].split()[7]
    for element in SUPPORTED_ELEMENTS_TWO_LETTERS + SUPPORTED_ELEMENTS_ONE_LETTER:
        if element.title() in atom_type:
            break
    if element not in VAL_ELEC:
        # May be worth to add the new atom type
        return HttpResponse('Invalid molecule with an unsupported atomtype', status=501)

    val_elec = VAL_ELEC[element]
    # Example: which has 4 single bonds, 0 double bonds to C, 0 double bonds to O,
    # 0 double bonds to S, 0 triple bonds, 0 quadruple bonds, 0 benzene bonds, 0
    # lone pairs, and 0 charge.
    single, r_double, o_double, s_double, triple, quadruple, benzene, lone_pairs, charge \
        = [int(item) for item in re.findall('\s-?\d\s', ','.join(error_message.split(',')[1:]))]
    orbital_num = single + 2 * (r_double + o_double + s_double) + 3 * triple + 4 * quadruple \
        + 1.5 * benzene + lone_pairs
    if element in ['C', 'N', 'O', 'F', 'Ne'] and orbital_num > 4:
        return HttpResponse(f'Invalid molecule with an invalid atomtype of {element} which does '
                            f'not satisfy the Octet rule. Please check input identifier.',
                            status=400)
    elif orbital_num > 6:
        return HttpResponse(f'Invalid molecule with an invalid atomtype of {element} which does '
                            f'not satisfy the expanded-octet rule. Please check input identifier.',
                            status=400)

    elec_balance = val_elec - orbital_num - lone_pairs - charge  # lone_pairs need to subtract twice

    if elec_balance != 0:
        return HttpResponse(f'Invalid molecule with an invalid atomtype of {element} which has '
                            f'unbalanced valence electrons. Please check input identifier.',
                            status=400)

    return HttpResponse('Invalid Molecule with an unsupported atomtype', status=501)
