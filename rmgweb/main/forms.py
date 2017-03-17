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
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from django.contrib import auth

from models import *

class DivErrorList(ErrorList):
    def __unicode__(self):
        return self.as_divs()
    def as_divs(self):
        if not self: return u''
        return mark_safe(u'<div>%s</div>' % (''.join([u'<div class="error">%s</div>' % e for e in self])))

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
        fields = ('organization', 'website', 'bio', 'energyUnits', 'heatCapacityUnits', 'rateCoefficientUnits', 'temperatureUnits', 'pressureUnits')

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

class PasswordCreateForm(forms.Form):
    """
    A form for creating your password.
    """
    password = forms.CharField(min_length=5, max_length=30, widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(max_length=30, widget=forms.PasswordInput(render_value=False))

    def __init__(self, *args, **kwargs):
        if 'username' in kwargs:
            self.username = kwargs['username']
            del kwargs['username']
        else:
            self.username = ''
        super(PasswordCreateForm, self).__init__(*args, **kwargs)
        
    def clean(self):
        password1 = self.cleaned_data.get('password', '')
        password2 = self.cleaned_data.get('confirm_password', '')
        if password1 != password2:
            raise forms.ValidationError('Passwords do not match.') 
        return self.cleaned_data
    
    def save(self):
        user = User.objects.get(username__exact=self.username)
        user.set_password(self.cleaned_data['password'])
        user.save()

class PasswordChangeForm(PasswordCreateForm):
    """
    A form for creating your password.
    """
    current_password = forms.CharField(required=False, min_length=5, max_length=30, widget=forms.PasswordInput(render_value=False))
    
    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['current_password', 'password', 'confirm_password']
        self.fields['password'].label = mark_safe('New&nbsp;password')
        self.fields['confirm_password'].label = mark_safe('Confirm&nbsp;new&nbsp;password')
        self.fields['password'].required = False
        self.fields['confirm_password'].required = False
    
    def clean(self):
        passwords = [
            self.cleaned_data.get('current_password', ''),
            self.cleaned_data.get('password', ''),
            self.cleaned_data.get('confirm_password', ''),
        ]
        if any([p != '' for p in passwords]) and not all([p != '' for p in passwords]):
            raise forms.ValidationError('To change your password, all three fields must be given.') 
        password1 = self.cleaned_data.get('password', '')
        password2 = self.cleaned_data.get('confirm_password', '')
        if password1 != password2:
            raise forms.ValidationError('New passwords do not match.') 
        return self.cleaned_data
    
    def clean_current_password(self):
        password = self.cleaned_data['current_password']
        if password != '':
            user = auth.authenticate(username=self.username, password=password)
            if user is None:
                raise forms.ValidationError('Current password is incorrect.') 
        return password
    
    def save(self):
        if self.cleaned_data['password'] != '':
            user = User.objects.get(username__exact=self.username)
            user.set_password(self.cleaned_data['password'])
            user.save()
