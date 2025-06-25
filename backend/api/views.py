import hashlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, get_list_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import RetrieveAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (
    FavoriteRecipe,
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortLinkSerializer,
    RecipeWriteSerializer,
    ShoppingCartRecipe,
    TagSerializer
)


User = get_user_model()


class CDLViewSet(RetrieveAPIView, ListModelMixin, GenericViewSet):
    pass


class IngredientViewSet(CDLViewSet):
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class TagViewSet(CDLViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    filter_backends = (OrderingFilter,)
    ordering_fields = ('-pub_date',)
    permission_classes = (IsAuthorOrReadOnly,)
    serializer_class = RecipeSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        request = self.request
        user = request.user
        applied = False

        if self.action == 'list':
            author = request.query_params.get('author')
            if author:
                queryset = queryset.filter(author=author)
                applied = True

            favorites = request.query_params.get('is_favorited')
            if (
                favorites not in (None, '0', 'false', 'False')
                and request.user.is_authenticated
            ):
                queryset = queryset.filter(favorite__author=user)
                applied = True

            in_cart = request.query_params.get('is_in_shopping_cart')
            if (
                in_cart not in (None, '0', 'false', 'False')
                and request.user.is_authenticated
            ):
                queryset = queryset.filter(shoppingcart__author=user)
                applied = True

            tags = request.query_params.getlist('tags')
            if tags:
                queryset = queryset.filter(tags__slug__in=tags).distinct()
                applied = True
            else:
                applied = False

            if not applied:
                return queryset.none()

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeWriteSerializer

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if recipe.short_link:
            serializer = RecipeShortLinkSerializer(recipe)
            return Response(serializer.data)

        # base_url = "https://foodgram.example.org/r/"
        short_link = hashlib.md5(
            f"{recipe.id}-{recipe.name}".encode()).hexdigest()[:8]
        # short_url = base_url + short_hash
        print(short_link)
        recipe.short_link = short_link
        recipe.save()

        serializer = RecipeShortLinkSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST' or request.method == 'DELETE':
            if Favorite.objects.filter(author=user, recipe=recipe).exists():
                favorite = Favorite.objects.filter(author=user,
                                                   recipe=recipe).first()
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            Favorite.objects.create(author=user, recipe=recipe)
            serializer = FavoriteRecipe(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            obj, created = ShoppingCart.objects.get_or_create(author=user,
                                                              recipe=recipe)
            if not created:
                return Response({'detail': 'Рецепт уже в списке покупок'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = ShoppingCartRecipe(recipe)

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

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(author=user)
        recipes = Recipe.objects.filter(
            id__in=shopping_cart.values_list('recipe_id', flat=True)
        )
        serializer = RecipeSerializer(recipes, many=True,
                                      context={'request': request})
        return Response(serializer.data)
