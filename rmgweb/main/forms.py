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

import re

from django import forms
from django.forms.util import ErrorList
from django.utils.safestring import mark_safe

from models import *

class DivErrorList(ErrorList):
    def __unicode__(self):
        return self.as_divs()
    def as_divs(self):
        if not self: return u''
        return mark_safe(u''.join([u'<div class="error">%s</div>' % e for e in self]))

################################################################################

class UserForm(forms.ModelForm):
    """
    A form for editing user profile information.
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class UserProfileForm(forms.ModelForm):
    """
    A form for editing user profile information.
    """
    class Meta:
        model = UserProfile
        fields = ('organization', 'website', 'bio')

################################################################################

class UserSignupForm(forms.ModelForm):
    """
    A form for editing user information when signing up for an account.
    """
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        
    def clean_username(self):
        username = self.cleaned_data['username']
        tokens = re.findall(r'[a-zA-Z][a-zA-Z0-9_]*', username)
        if len(tokens) != 1 or tokens[0] != username:
            raise forms.ValidationError('Invalid character(s) in username.')
        if User.objects.filter(username__exact=username).count() > 0:
            raise forms.ValidationError('Username already in use.')
        return username
    
class UserProfileSignupForm(forms.ModelForm):
    """
    A form for editing user profile information when signing up for an account.
    """
    class Meta:
        model = UserProfile
        fields = ('organization',)
