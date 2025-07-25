"""
Views for Foodgram API.

This module contains viewsets and actions for users,
ingredients, tags, recipes, favorites, and shopping cart.
"""

import hashlib

from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import RetrieveAPIView
from rest_framework.mixins import ListModelMixin
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
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    DownloadShoppingCart,
    FollowerSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortLinkSerializer,
    RecipeWriteSerializer,
    ShortRecipe,
    TagSerializer,
)

User = get_user_model()


class PaginateMixin:
    """Mixin for paginating queryset and returning paginated response."""

    def paginate_and_respond(self, queryset, serializer_class, **kwargs):
        """
        Paginate the given queryset.

        It returns a paginated response using
        the specified serializer.

        If pagination is not applied, return
        a regular response with serialized data.
        """
        page = self.paginate_queryset(queryset)
        to_ser = page if page is not None else queryset
        serializer = serializer_class(
            to_ser, many=True, context={'request': self.request}, **kwargs)
        return self.get_paginated_response(
            serializer.data) if page is not None else Response(serializer.data)


class CustomUserViewSet(PaginateMixin, UserViewSet):
    """ViewSet for user actions: subscribe, subscriptions, avatar."""

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
            Follower.objects.get_or_create(
                follower=follower,
                followed=followed
            )
            serializer = FollowerSerializer(
                followed,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            Follower.objects.filter(
                follower=follower, followed=followed).delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Return a paginated list of users."""
        return self.paginate_and_respond(
            User.objects.filter(followers__follower=request.user),
            FollowerSerializer
        )

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
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

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
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    pagination_class = None

    def get_queryset(self):
        """Optionally filter ingredients by name using query parameters."""
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class TagViewSet(CDLViewSet):
    """ViewSet for listing tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """ViewSet for CRUD operations on recipes."""

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = RecipeFilter
    ordering_fields = ('-pub_date',)
    permission_classes = (IsAuthorOrReadOnly,)
    serializer_class = RecipeSerializer

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
            serializer = RecipeShortLinkSerializer(recipe)
            return Response(serializer.data)

        base_url = "https://foodgram-site.zapto.org/"
        short_hash = hashlib.md5(
            f"{recipe.id}-{recipe.name}".encode()).hexdigest()[:8]
        short_link = base_url + short_hash
        recipe.short_link = short_link
        recipe.save()

        serializer = RecipeShortLinkSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

        if request.method == 'POST' or request.method == 'DELETE':
            if Favorite.objects.filter(author=user, recipe=recipe).exists():
                favorite = Favorite.objects.filter(author=user,
                                                   recipe=recipe).first()
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            Favorite.objects.create(author=user, recipe=recipe)
            serializer = ShortRecipe(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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
