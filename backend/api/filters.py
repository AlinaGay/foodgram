"""
Custom filters for the Foodgram API.

This module defines filters for recipes,
including filtering by author, tags, favorites, and shopping cart.
"""

from django_filters.rest_framework import (
    FilterSet, NumberFilter,
    BooleanFilter, ModelMultipleChoiceFilter
)

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    """FilterSet for filtering recipes."""

    author = NumberFilter(field_name='author__id')
    is_favorited = BooleanFilter(method='filter_fav')
    is_in_shopping_cart = BooleanFilter(method='filter_cart')
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

    def filter_fav(self, queryset, name, value):
        """Filter recipes that are favorited by the authenticated user."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite__author=self.request.user)
        return queryset.none() if value else queryset

    def filter_cart(self, queryset, name, value):
        """Filter recipes that are in the shopping cart."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(shoppingcart__author=self.request.user)
        return queryset.none() if value else queryset
