"""
Serializers for recipe APIs.
"""

from rest_framework import serializers
from core.models import (Recipe, Tag)

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""
    class Meta:
        model = Recipe
        #fields = []
        exclude = ['user', 'description']
        read_only_fields = ['id']

class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""
    class Meta(RecipeSerializer.Meta):
        # fields = RecipeSerializer.Meta.fields + ['description']
        exclude = ['user']

class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']