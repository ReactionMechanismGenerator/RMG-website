from django.test import TestCase
from django.contrib.auth.models import User
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
