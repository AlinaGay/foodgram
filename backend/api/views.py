"""
Views for Foodgram API.

This module contains viewsets and actions for users,
ingredients, tags, recipes, favorites, and shopping cart.
"""

import hashlib

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import RetrieveAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

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
    DownloadShoppingCart,
    FollowerSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    ShortRecipe,
    TagSerializer,
)

User = get_user_model()


class PageNumberPaginationConfig(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


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

        if follower == followed:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Follower.objects.filter(
                follower=follower,
                followed=followed
            ).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Follower.objects.create(follower=follower, followed=followed)
            serializer = FollowerSerializer(
                followed,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            follow_relation = Follower.objects.filter(
                follower=follower,
                followed=followed
            )
            if not follow_relation.exists():
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            follow_relation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)

            user.avatar = None
            user.save(update_fields=['avatar'])
            return Response(status=status.HTTP_204_NO_CONTENT)


class CDLViewSet(RetrieveAPIView, ListModelMixin, GenericViewSet):
    """Base viewset for read-only models."""

    pass


class IngredientViewSet(CDLViewSet):
    """ViewSet for listing and searching ingredients."""

    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    # pagination_class = None
    queryset = Ingredient.objects.all()


class TagViewSet(CDLViewSet):
    """ViewSet for listing tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    # pagination_class = None


class RecipeViewSet(ModelViewSet):
    """ViewSet for CRUD operations on recipes."""

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = RecipeFilter
    ordering_fields = ('-pub_date',)
    permission_classes = (IsAuthorOrReadOnly,)
    serializer_class = RecipeSerializer
    pagination_class = PageNumberPaginationConfig

    def perform_create(self, serializer):
        """Save a new recipe with the authenticated user as the author."""
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Return the appropriate serializer class depending on the action."""
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeWriteSerializer

    @action(detail=True, url_path='get-link', permission_classes=(AllowAny,))
    def get_link(self, request, pk=None):
        """Generate and return a short link for the specified recipe."""
        recipe = get_object_or_404(Recipe, id=pk)
        if recipe.short_link:
            return Response({"short-link": recipe.short_link})

        try:
            recipe.save(request=request)
            return Response({"short-link": recipe.short_link})

        except Exception as e:
            return Response(
                {"error": f"Ошибка генерации ссылки: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        """Add or remove the specified recipe from."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(author=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(author=user, recipe=recipe)
            serializer = ShortRecipe(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite = Favorite.objects.filter(author=user, recipe=recipe)
            if not favorite.exists():
                return Response(
                    {'errors': 'Рецепта нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        """Add or remove the specified recipe."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            obj, created = ShoppingCart.objects.get_or_create(author=user,
                                                              recipe=recipe)
            if not created:
                return Response({'detail': 'Рецепт уже в списке покупок'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = ShortRecipe(recipe)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted, _ = ShoppingCart.objects.filter(author=user,
                                                     recipe=recipe).delete()
            if deleted == 0:
                return Response(
                    {'detail': 'Рецепта не было в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Download the authenticated user's shopping cart."""
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(author=user)
        recipes = Recipe.objects.filter(
            id__in=shopping_cart.values_list('recipe_id', flat=True)
        )
        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values(
                name=F('ingredient__name'),
                measurement_unit=F('ingredient__measurement_unit')
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('name')
        )

        serializer = DownloadShoppingCart(ingredients, many=True)
        lines = [
            (
                f"- {item['name']} {item['total_amount']} "
                f"{item['measurement_unit']}"
            )
            for item in serializer.data
        ]

        response = HttpResponse("\n".join(lines), content_type="text/plain")
        response["Content-Disposition"] = (
            "attachment; filename=ingredients.txt"
        )
        return response
