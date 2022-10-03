"""
Tests for the ingredients API
"""

from sys import stdout
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, User
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')

def create_payload(**kwargs):
    """Creates and returns a dictionary."""
    return kwargs

def detail_url(ingredient_id):
    """Create and return an ingredient detail URL."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email="email@example.com", password="TestPass+123") -> User:
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)

class PublicIngredientsApiTests(TestCase):
    """Test unauthenticated API requests."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving ingredients list."""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientsApiTests(TestCase):
    """Test authenticated API requests."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
    
    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name="Garlic")
        Ingredient.objects.create(user=self.user, name="Tomato")
        Ingredient.objects.create(user=self.user, name="Kale")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.all().order_by('-name')
        serialized_ingredients = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serialized_ingredients.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients is limited to Authenticated user."""
        user2 = create_user(email="user2@example.com", password="Abc123")

        ingredient1 = Ingredient.objects.create(user=self.user, name="salt")
        ingredient2 = Ingredient.objects.create(user=user2, name="pepper")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
            # check that there is only one ingredient returned, not two
        self.assertEqual(res.data[0]['name'], ingredient1.name)
        self.assertEqual(res.data[0]['id'], ingredient1.id)
            # Check data of ingredient returned. 
    
    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name='Garlic')
            # Create init ingredient
        payload = create_payload(name='Ginger')
            # Create payload to send
        update_url = detail_url(ingredient.pk)
            # Create PATH with PK value
        res = self.client.patch(update_url, payload, format='json')
            # PATCH update to endpoint
        # stdout.write(f'{dir(res.data)}\n')
        # stdout.write(f'{res.data.items()}\n')
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
            # Check the status returned is 200
        ingredient.refresh_from_db()
            # update value from DB
        self.assertEqual(payload['name'], ingredient.name)
        self.assertEqual(res.data.get('id'), ingredient.pk)
        