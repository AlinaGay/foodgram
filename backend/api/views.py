from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import RetrieveAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from recipes.models import Ingredient, Recipe, Tag, User
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import IngredientSerializer, RecipeSerializer, TagSerializer


User = get_user_model()


class CDLViewSet(RetrieveAPIView, ListModelMixin, GenericViewSet):
    pass


class IngredientViewSet(CDLViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    pagination_class = None


class TagViewSet(CDLViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (OrderingFilter,)
    ordering_fields = ('-pub_date',)
    permission_classes = (IsAuthorOrReadOnly,)
    serializer_class = RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
