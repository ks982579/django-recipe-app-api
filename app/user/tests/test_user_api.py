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
        # pass dictionary in as kwargs
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