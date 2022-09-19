"""
Tests for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

# returns full URL path
CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")

def create_user(**params):
    """Create and return a new User."""
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""
    def setUp(self):
        self.client = APIClient()
    
    def test_create_user_success(self):
        """Test creating a user is successful."""
        # Payload to pass in
        payload = {
            'email': 'test@example.com',
            'password': 'password+123',
            'name': 'John Doe',
        }
        # Post Data to endpoint
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.has_usable_password, 'Does not have usable password')
        self.assertNotEqual(user.password, payload['password'])
        self.assertTrue(
            user.check_password(payload['password']),
            f'{user.password}')
        self.assertNotIn('password', res.data)
    
    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists"""
        # same as previous payload / should we make it class variable?
        payload = {
            'email': 'test@example.com',
            'password': 'password+123',
            'name': 'John Doe',
        }
        # pass dictionary in as kwargs - defined above
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_too_short_error(self):
        """Test an error is returned if password is less than 5 characters."""
        payload = {
            'email': 'test@example.com',
            'password': 'abc',
            'name': 'John Doe',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)
    
    def test_create_token_for_user(self):
        """Test generate token for valid credentials."""
        user_detials = {
            'name': 'Jessica Jones',
            'email': 'test1@example.com',
            'password': 'TestWord#!9876',
        }
        create_user(**user_detials)
        # We don't need 'name' to login
        payload = {
            'email': user_detials['email'],
            'password': user_detials['password']
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)
    
    def test_create_token_bad_email(self):
        """Test returns error if email credentials are invalid."""
        user_detials = {
            'name': 'Matthew Murdock',
            'email': 'test2@example.com',
            'password': 'TestWord#!9876',
        }
        create_user(**user_detials)
        # We don't need 'name' to login
        # Testing Wrong Email
        payload = {
            'email': 'wrong_email@example.com',
            'password': user_detials['password'],
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

        # Blank Email?
        payload = {
            'email': '',
            'password': user_detials['password'],
        }
        res = self.client.post(TOKEN_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_bad_password(self):
        """Test returns error if Password credentials are invalid."""
        user_detials = {
            'name': 'Tony Stark',
            'email': 'test3@example.com',
            'password': 'TestWord#!9876',
        }

        create_user(**user_detials)
        # We don't need 'name' to login
        # Testing Wrong Password
        payload = {
            'email': user_detials['email'],
            'password': '$Wrong_Password=123',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

        # Blank Password?
        payload = {
            'email': user_detials['email'],
            'password': '',
        }
        res = self.client.post(TOKEN_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)
    
    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="testPass+123",
            name="Kali Linux",
        )
        # instantiate the APIClient to make requests
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })
    
    def test_POST_me_not_allowed(self):
        """Test POST is not allowed for the 'me' endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {
            'name': 'Updated Name',
            'password': 'Updated_Password+987',
        }

        res = self.client.patch(ME_URL, payload)
        # since we've changed the user, we need to grab the new value
        self.user.refresh_from_db()

        # Check that values have been updated
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
