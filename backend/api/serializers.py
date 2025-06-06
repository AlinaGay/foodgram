from django.contrib.auth import get_user_model
from rest_framework import serializers

from recipes.models import Ingredient

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
