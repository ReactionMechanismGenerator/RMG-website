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

from django.contrib.auth.models import User
from django.test import TestCase

from rmgweb.main.models import UserProfile


class preLogInTest(TestCase):

    def test_login(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/login')

        self.assertEqual(response.status_code, 200)

    def test_login_post(self):
        """
        Test that a user is redirected upon login
        """

        User.objects.create_user('testuser', email='rmg_dev@mit.edu', password='12345678')

        response = self.client.post('/login', {'username': 'testuser', 'password': '12345678'})

        self.assertRedirects(response, '/')

    def test_signup(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/signup')

        self.assertEqual(response.status_code, 200)

    def test_signup_post(self):
        """
        Test that a user is redirected upon signup
        """

        response = self.client.post('/signup', {'username': 'testuser',
                                                'first_name': 'John',
                                                'last_name': 'Smith',
                                                'email': 'rmg_dev@mit.edu',
                                                'organization': 'MIT',
                                                'password': '12345678',
                                                'confirm_password': '12345678'})

        self.assertRedirects(response, '/')


class postLogInTest(TestCase):

    def setUp(self):
        user = User.objects.create_user('testuser', email='rmg_dev@mit.edu', password='12345678')
        UserProfile.objects.create(user=user)

        self.logged_in = self.client.login(username='testuser', password='12345678')

    def test_0(self):
        """
        Assert that login was successful
        """
        self.assertTrue(self.logged_in)

    def test_profile(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/user/testuser')

        self.assertEqual(response.status_code, 200)

    def test_profile_edit(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/profile')

        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        """
        Test that webpage gives expected response
        """

        response = self.client.get('/logout')

        self.assertEqual(response.status_code, 200)
