"""
Custom filters for the Foodgram API.

This module defines filters for recipes,
including filtering by author, tags, favorites, and shopping cart.
"""

from django_filters.rest_framework import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    ModelMultipleChoiceFilter,
)

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """FilterSet for filtering ingredients."""

    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        """Meta option for IngredientFilter."""

        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    """FilterSet for filtering recipes."""

    is_favorited = BooleanFilter()
    is_in_shopping_cart = BooleanFilter()
    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        distinct=True
    )

    class Meta:
        """Meta class for RecipeFilter specifying model and fields."""

        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')
