from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework.mixins import ListModelMixin
from rest_framework.generics import RetrieveAPIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from recipes.models import Ingredient, Recipe, Tag, User
from .serializers import IngredientSerializer


# User = get_user_model()


class CDLViewSet(RetrieveAPIView, ListModelMixin, GenericViewSet):
    pass


class IngredientViewSet(CDLViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
