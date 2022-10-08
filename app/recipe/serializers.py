"""
Serializers for recipe APIs.
"""

from attr import validate
from rest_framework import serializers
from core.models import (Recipe, Tag, Ingredient)

class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredients model."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name'] #'__all__' does not work w/endpoint
        read_only_fields = ['id']

class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        #fields = []
        exclude = ['user', 'description']
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)
    
    def _get_or_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredients as needed."""
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient,
            ) # Get or Create new ingredient
            recipe.ingredients.add(ingredient_obj)
                # Add incredient to ManyToManyField

    def create(self, validated_data) -> Recipe:
        """Create a recipe, allowing for nested TagSerializer."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
            # create recipe.
        self._get_or_create_tags(tags, recipe)
            # create or assign tags as needed
        self._get_or_create_ingredients(ingredients, recipe)
            # create or assign ingredients as needed
        return recipe
    
    def update(self, instance, validated_data) -> Recipe:
        """Update a recipe, allowing for nested TagSerializer."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.clear()
                # remove old tags
            self._get_or_create_tags(tags, instance)
                # create or assign tags as needed

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""
    class Meta(RecipeSerializer.Meta):
        # fields = RecipeSerializer.Meta.fields + ['description']
        exclude = ['user']