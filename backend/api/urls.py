"""
URL configuration for Foodgram API.

Defines routes for users, ingredients,
tags, recipes, and authentication endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet
)

router = DefaultRouter()

router.register(r'users', CustomUserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
