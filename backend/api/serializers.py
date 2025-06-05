from django.contrib.auth import get_user_model
from rest_framework import serializers

from recipes.models import Ingredients

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ('id',)
        model = Ingredients