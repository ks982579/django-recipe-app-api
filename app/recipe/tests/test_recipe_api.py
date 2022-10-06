"""
Test for recipe APIs.
"""

from decimal import Decimal
from typing import Reversible

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (Recipe, Tag, Ingredient)
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)
import sys

RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """create and return a recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal(10.69),
        'description': 'Sample Description, super yummy.',
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests."""
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpass123',
        )
        self.client.force_authenticate(self.user)
    
    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user, title='second recipe')
        create_recipe(user=self.user, title='third recipe', time_minutes=20)
        
        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
    
    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""
        other_user = create_user(
            email='other_guy@example.com',
            password='testpass1234',
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user, title='second recipe')
        create_recipe(user=self.user, title='third recipe', time_minutes=20)

        # Make GET request to RECIPES_URL
        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serialized_recipes = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serialized_recipes.data)

    def test_get_recipe_detail(self):
        """Test getting recipe details."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)

        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)
    
    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            'title': 'Vegan Sample Recipe',
            'time_minutes': 35,
            'price': Decimal('13.49'),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(pk=res.data['id'])
        for _k, _v in payload.items():
            self.assertEqual(getattr(recipe, _k), _v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial updated of a recipe."""
        og_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=og_link,
        )
        payload = {'title':'Updated Recipe Title'}
        url = detail_url(recipe.id)
            # Create dynamic URL with helper function
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
            # Pulls from DB again, after our update.
        self.assertEqual(recipe.title, payload['title'])
            # Testing the title DID change.
        self.assertEqual(recipe.link, og_link)
            # Ensuring the link did NOT change. 
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of recipe."""
        recipe = create_recipe(
            user=self.user,
            title='Initial Recipe Title',
            link='http://example.com/recipe01',
            description='Initial recipe description, yummy',
        ) # creating Recipe in database

        def create_payload(**kwargs):
            return kwargs

        payload = create_payload(
            title='Updated Recipe Title',
            link='https://example.com/recipe02',
            description='Updated recipe description',
            time_minutes=15,
            price=Decimal('13.99'),
        ) # Creating updated Payload

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for _k, _v in payload.items():
            self.assertEqual(getattr(recipe, _k), _v)
        self.assertEqual(recipe.user, self.user)
    
    def test_update_user_returns_error(self):
        """Test changing the recipe user resulting in an error."""
        new_user = create_user(email='Elisa@example.com', password="weakpw02")
        recipe = create_recipe(user=self.user)

        payload = {
            'user': new_user.id,
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
            # Sending PATCH to update user
        # sys.stdout.write(f'Update User: HTTP_{res.status_code}')
            # Returns HTTP_200_OK???

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
    
    def test_delete_recipe(self):
        """Test deleting a recipe successfully."""
        recipe = create_recipe(user=self.user)
            # create a recipe.
        url = detail_url(recipe.id)
            # create dynamic URL to reference recipe.
        res = self.client.delete(url)
            # Send DELETE to correct endpoint.
        
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())
    
    def test_delete_other_user_recipe_error(self):
        """Test trying to delete other user's recipe gives error."""
        new_user = create_user(
            email="Yaml@example.com",
            password="a5e£^6Dv8V}dQ@4",
        )
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(pk=recipe.id).exists())
    
    def test_create_recipe_with_new_tags(self) -> None:
        """Test creating a recipe with new tags."""
        def payload_maker(**kwargs) -> dict:
            return kwargs
        payload = payload_maker(
            title='Thai Prawn Curry',
            time_minutes=30,
            price=Decimal('12.50'),
            tags=[{'name': 'Thai'}, {'name': 'Dinner'}]
        )
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)
    
    def test_create_recipe_with_existing_tags(self) -> None:
        """Test creating a recipe with existing tag."""
        tag_vegan = Tag.objects.create(user=self.user, name='Vegan')
        def payload_maker(**kwargs) -> dict:
            return kwargs
        payload = payload_maker(
            title='Tofu Stir-Fry',
            time_minutes=20,
            price=Decimal('9.99'),
            tags=[{'name': 'Vegan'}, {'name': 'Dinner'}]
        )
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_vegan, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)
    
    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {'tags':[{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        # recipe.refresh_from_db() Not necessary for ManyToManyField fields. 
        self.assertIn(new_tag, recipe.tags.all())
    
    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)
            # Adding "Breakfast" tag to the recipe
        
        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
            # Check that "Lunch" is an included tag.
        self.assertNotIn(tag_breakfast, recipe.tags.all())
            # Check the "Breakfast" was removed from the recipe tags. 
    
    def test_clear_recipe_tags(self):
        """Test clearing a recipe tags."""
        tag = Tag.objects.create(user=self.user, name="Dessert")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
            # Empty "tags" payload to clear out tags. 
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
    
    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""
        def payload_maker(**kwargs) -> dict:
            return kwargs
        ingredient_list = [{'name': 'salt'}, {'name': 'pepper'}, {'name': 'onion'}, {'name': 'apple'},]
        payload = payload_maker(
            title='Tofu Stir-Fry',
            time_minutes=20,
            price=Decimal('9.99'),
            tags=[{'name': 'Vegan'}, {'name': 'Dinner'}],
            ingredients=ingredient_list,
        )

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 4)
        for _ing in payload['ingredients']:
            # Loop through all in payload, and ensure they exist in recipe
            exists = recipe.ingredients.filter(
                name=_ing['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating a new recipe with existing ingredients."""
        ingredient1 = Ingredient.objects.create(user=self.user, name="broccoli")
        ingredient2 = Ingredient.objects.create(user=self.user, name="noodles")

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertEqual(ingredients.count(), 2)

        def payload_maker(**kwargs) -> dict:
            return kwargs
        payload = payload_maker(
            title='Tofu Stir-Fry',
            time_minutes=20,
            price=Decimal('9.99'),
            tags=[{'name': 'Vegan'}, {'name': 'Dinner'}],
            ingredients=[
                {'name':'broccoli'},
                {'name':'onion'},
                {'name':'pepper'},
                {'name':'noodles'}]
        )
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 4)

        self.assertIn(ingredient1, recipe.ingredients.all())
        self.assertIn(ingredient2, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)
        
        self.assertEqual(Ingredient.objects.filter(user=self.user).count(), 4)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'Lime'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Lime')
        self.assertIn(new_ingredient, recipe.ingredients.all())
            # Checking our ingredient is in the recipe. 

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient with updating a recipe."""
        ingredient1 = Ingredient.objects.create(user=self.user, name='pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='salt')
            # create second ingredient
        payload = {'ingredients': {'name': 'salt'}}
            # reference second ingredient
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())
            # we remove ingredients when we update. 