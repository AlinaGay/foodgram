"""
Views for Foodgram API.

This module contains viewsets and actions for users,
ingredients, tags, recipes, favorites, and shopping cart.
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Exists, F, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (
    Favorite,
    Follower,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    FollowerSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    ShortRecipe,
    TagSerializer,
)
from .utils import PageNumberPaginationConfig, add_object, remove_object

User = get_user_model()


class UserActionsViewSet(UserViewSet):
    """ViewSet for user actions: subscribe, subscriptions, avatar."""
    pagination_class = PageNumberPaginationConfig

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """
        Return the authenticated user's information.

        Only available to authenticated users.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """
        Subscribe or unsubscribe the authenticated user to another user.

        POST: Subscribe to the user with the given id.
        DELETE: Unsubscribe from the user with the given id.
        """
        followed = get_object_or_404(User, pk=id)
        follower = request.user

        if request.method == 'POST':
            if follower == followed:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return add_object(
                model=Follower,
                serializer_instance=followed,
                serializer_class=FollowerSerializer,
                already_added_message=(
                    'Вы уже подписаны на этого пользователя.'),
                context={'request': request},
                follower=follower,
                followed=followed
            )

        return remove_object(
            model=Follower,
            not_found_message='Вы не подписаны на этого пользователя.',
            follower=follower,
            followed=followed
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Return a paginated list of users."""
        queryset = User.objects.filter(followers__follower=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FollowerSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = FollowerSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def add_avatar(self, request, id=None):
        """
        Add or remove an avatar for the authenticated user.

        PUT: Update the user's avatar.
        DELETE: Remove the user's avatar.
        """
        user = request.user

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                instance=user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)

        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet for listing and searching ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    """ViewSet for listing tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(ModelViewSet):
    """ViewSet for CRUD operations on recipes."""

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = RecipeFilter
    ordering_fields = ('-pub_date',)
    permission_classes = (IsAuthorOrReadOnly,)
    serializer_class = RecipeSerializer
    pagination_class = PageNumberPaginationConfig

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        if user.is_authenticated:
            favorited_subquery = Favorite.objects.filter(
                author=user, recipe=OuterRef('pk')
            )
            cart_subquery = ShoppingCart.objects.filter(
                author=user, recipe=OuterRef('pk')
            )
            queryset = queryset.annotate(
                is_favorited=Exists(favorited_subquery),
                is_in_shopping_cart=Exists(cart_subquery)
            )
        else:
            queryset = queryset.annotate(
                is_favorited=models.Value(
                    False, output_field=models.BooleanField()),
                is_in_shopping_cart=models.Value(
                    False, output_field=models.BooleanField()),
            )
        return queryset

    def get_serializer_class(self):
        """Return the appropriate serializer class depending on the action."""
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeWriteSerializer

    @action(detail=True, url_path='get-link', permission_classes=(AllowAny,))
    def get_link(self, request, pk=None):
        """Generate and return a short link for the specified recipe."""
        recipe = get_object_or_404(Recipe, id=pk)
        if not recipe.short_link:
            recipe.save(request=request)
        url = request.build_absolute_uri(f'/r/{recipe.short_link}/')

        return Response({"short-link": url})

    @action(detail=True, methods=['post', 'delete'],
            url_path='favorite', permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        """Add or remove the specified recipe from favorites."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            return add_object(
                model=Favorite,
                serializer_instance=recipe,
                serializer_class=ShortRecipe,
                already_added_message='Рецепт уже в избранном.',
                context={'request': request},
                author=user,
                recipe=recipe
            )

        return remove_object(
            model=Favorite,
            not_found_message='Рецепта нет в избранном.',
            author=user,
            recipe=recipe
        )

    @action(detail=True, methods=['post', 'delete'],
            url_path='shopping_cart', permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        """Add or remove the specified recipe from shopping cart."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            return add_object(
                model=ShoppingCart,
                serializer_instance=recipe,
                serializer_class=ShortRecipe,
                already_added_message='Рецепт уже в списке покупок.',
                context={'request': request},
                author=user,
                recipe=recipe
            )

        return remove_object(
            model=ShoppingCart,
            not_found_message='Рецепта не было в списке покупок.',
            author=user,
            recipe=recipe
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Download the authenticated user's shopping cart."""
        user = request.user
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcart__author=user)
            .values(
                name=F('ingredient__name'),
                measurement_unit=F('ingredient__measurement_unit')
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('name')
        )

        lines = [
            (
                f"- {item['name']} {item['total_amount']} "
                f"{item['measurement_unit']}"
            )
            for item in ingredients
        ]

        response = HttpResponse("\n".join(lines), content_type="text/plain")
        response["Content-Disposition"] = (
            "attachment; filename=ingredients.txt"
        )
        return response
