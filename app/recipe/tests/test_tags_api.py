"""
Tests for the tags API.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def create_user(email='user@example.com', password='testpass123'):
    """Create and return a user."""
    return get_user_model().objects.create_user(email, password)

def detail_url(tag_id):
    """Create and return a tag detail url."""
    return reverse('recipe:tag-detail', args=[tag_id])

class PublicTagsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Test that Authorization is required for retieving tags."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self) -> None:
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')
            # Creating test tags
        
        res = self.client.get(TAGS_URL)
            # Sending GET request to Client
        
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
            # Fetch and serialize objects
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
    
    def test_tags_limited_to_user(self):
        """Test that list of tags is limited to authenticated user."""
        user2 = create_user(email="HotSause@example.com", password="Password!987")
        Tag.objects.create(user=user2, name='Fruity')
        tag = Tag.objects.create(user=self.user, name='Vegan')
            # Create tags from two different users.
        
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)
    
    def test_update_tag(self):
        """Test updating a tag."""
        tag = Tag.objects.create(user=self.user, name="Vegan")
            # Create initial Tag
        payload = {'name': 'Dessert'}
            # This is payload of new name to change to.
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)
            # Sending payload through PATCH method to update tag
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])
            # Testing response and data
    
    def test_delete_tag(self):
        """Test deleting a tag."""
        tag = Tag.objects.create(user=self.user, name="breakfast")

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
            # Check that we get HTTP 204 NO CONTENT
        tags = Tag.objects.filter(pk=tag.id)
        self.assertFalse(tags.exists())
            # check that our tag no longer exists.

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags to those assigned to recipes."""
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        tag2 = Tag.objects.create(user=self.user, name="Lunch")
        recipe = Recipe.objects.create(
            user=self.user,
            title="Overnight Oats",
            price=Decimal("1.99"),
            time_minutes=5,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_are_unique(self):
        """Test filtered tags returns a unique list."""
        tag = Tag.objects.create(user=self.user, name="Breakfast")
        Tag.objects.create(user=self.user, name="Dinner")
        recipe1 = Recipe.objects.create(
            user=self.user,
            title="Vegan Pancakes",
            time_minutes=25,
            price=Decimal("7.63"),
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="Overnight Oats",
            price=Decimal("1.99"),
            time_minutes=5,
        )
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)