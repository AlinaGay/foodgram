from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from recipes.models import Ingredient, Recipe, Tag, User
from .permissions import (IsAdmin, IsAdminOrReadOnly,
                          IsAuthorAdminAuthorizedUserOrReadOnly)
from .serializers import IngredientSerializer, TagSerializer


User = get_user_model()


class CDLViewSet(RetrieveAPIView, ListModelMixin, GenericViewSet):
    pass


class IngredientViewSet(CDLViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)


class TagViewSet(CDLViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)

    
