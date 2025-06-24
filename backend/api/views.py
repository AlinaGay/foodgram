import hashlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import RetrieveAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from recipes.models import Favorite, Ingredient, Recipe, Tag
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (
    FavoriteRecipe,
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortLinkSerializer,
    RecipeWriteSerializer,
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

        if self.action == 'list':
            author = request.query_params.get('author')
            if author:
                queryset = queryset.filter(author=author)

            favorites = request.query_params.get('is_favorited')
            if favorites not in (None, '0', 'false', 'False'):
                user = request.user
                if user.is_authenticated:
                    queryset = queryset.filter(favorite__author=user)

            tags = request.query_params.getlist('tags')
            queryset = queryset.filter(tags__slug__in=tags).distinct()

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
        session = request.session
        cart = session.get('shopping_cart', [])
        recipe_id = int(pk)

        if request.method == 'POST':
            if recipe_id not in cart:
                cart.append(recipe_id)

        else:
            if recipe_id in cart:
                cart.remove(recipe_id)

        session['shopping_cart'] = cart
        session.modified = True

        return Response(status=status.HTTP_204_NO_CONTENT)
