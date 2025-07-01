from django_filters.rest_framework import (
    DjangoFilterBackend, FilterSet, NumberFilter,
    BooleanFilter, ModelMultipleChoiceFilter
)

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
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
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_fav(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite__author=self.request.user)
        return queryset.none() if value else queryset

    def filter_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shoppingcart__author=self.request.user)
        return queryset.none() if value else queryset
