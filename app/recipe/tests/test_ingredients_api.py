"""
Tests for the ingredients API
"""
from decimal import Decimal
from sys import stdout
from unicodedata import decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, User, Recipe
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
    
    def test_deleting_ingredients(self):
        """Test for deleting ingredients with endpoint."""
        ingredient1 = Ingredient.objects.create(user=self.user, name="salt")
        ingredient2 = Ingredient.objects.create(user=self.user, name="pepper")

        self.assertEqual(Ingredient.objects.all().count(), 2)
        self.assertIn(ingredient1, Ingredient.objects.all())
            # Ensuring ingredient1 is in our list.

        delete_url = detail_url(ingredient1.pk)
        res = self.client.delete(delete_url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredient_list = Ingredient.objects.all()

        self.assertEqual(ingredient_list.count(), 1)
        self.assertNotIn(ingredient1, ingredient_list)
            # Ensuring ingredient1 is not in our list. 
    
    def test_filter_ingredients_assigned_to_recipe(self):
        """Test listing ingredients by those assigned to recipes."""
        in1 = Ingredient.objects.create(user=self.user, name="Apple")
        in2 = Ingredient.objects.create(user=self.user, name="Turkey")
        recipe = Recipe.objects.create(
            title="Apple Crumble",
            time_minutes=5,
            price=Decimal('9.99'),
            user=self.user,
        )
        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s1.data, res.data)

    def test_filtered_ingredients_are_unique(self):
        """Test filtered ingredients returns a unique list."""
        ing = Ingredient.objects.create(user=self.user, name="Berry")
        Ingredient.objects.create(user=self.user, name="Lentils")
        recipe1 = Recipe.objects.create(
            user=self.user,
            title="Berry Blast",
            time_minutes=60,
            price=Decimal("4.95"),
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="Berry Ice Cream",
            time_minutes=20,
            price=Decimal("5.99"),
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)