"""
Serializers for Foodgram API.

This module defines custom and model serializers
for users, recipes, ingredients, tags, favorites, followers, and shopping cart.
"""

import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (
    Favorite,
    Follower,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import serializers

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Custom image field for handling base64-encoded images."""

    def to_internal_value(self, data):
        """Convert base64 string to image file."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Serializer for creating a user."""

    class Meta(UserCreateSerializer.Meta):
        """Meta class for CustomUserCreateSerializer."""

        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')
        read_only_fields = ['id']


class CustomUserSerializer(UserSerializer):
    """Serializer for user representation with subscription and avatar."""

    class Meta(UserSerializer.Meta):
        """Meta class for CustomUserSerializer."""

        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'is_subscribed', 'avatar')
        read_only_fields = ('id', 'email')


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer for user avatar."""

    avatar = Base64ImageField()

    class Meta:
        """Meta class for AvatarSerializer."""

        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag model."""

    class Meta:
        """Meta class for TagSerializer."""

        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient model."""

    class Meta:
        """Meta class for IngredientSerializer."""

        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for reading ingredients in a recipe."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        """Meta class for RecipeIngredientSerializer."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for reading recipes."""

    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        """Meta class for RecipeSerializer."""

        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_ingredients(self, obj):
        """Return ingredients for the given recipe."""
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        """Return True if recipe is favorited by the user."""
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return Favorite.objects.filter(author=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Return True if recipe is in the user's shopping cart."""
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(author=user, recipe=obj).exists()


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Serializer for writing ingredients in a recipe."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        """Meta class for RecipeIngredientWriteSerializer."""

        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Serializer for writing recipes."""

    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        """Meta class for RecipeWriteSerializer."""

        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate(self, data):
        """Validate recipe data before saving."""
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент'}
            )
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться'}
            )

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Нужен хотя бы один тег'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться'}
            )

        cooking_time = data.get('cooking_time')
        if cooking_time <= 0:
            raise serializers.ValidationError(
                {'cooking_time': 'Время приготовления должно быть больше 0'}
            )

        return data

    def create_ingredients(self, ingredients, recipe):
        """Bulk create RecipeIngredient objects for a recipe."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        """Create a new recipe instance."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update an existing recipe instance."""
        instance.image = validated_data.get('image', instance.image)
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(validated_data['tags'])

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Return the serialized representation of the recipe."""
        return RecipeSerializer(instance, context=self.context).data


class RecipeShortLinkSerializer(serializers.ModelSerializer):
    """Serializer for recipe short link."""

    short_link = serializers.SerializerMethodField()

    class Meta:
        """Meta class for RecipeShortLinkSerializer."""

        model = Recipe
        fields = ('short_link',)

    def get_short_link(self, obj):
        """Return the short link for the recipe."""
        return obj.short_link

    def to_representation(self, instance):
        """Return the serialized representation with 'short-link' key."""
        data = super().to_representation(instance)
        data['short-link'] = data.pop('short_link')
        return data


class ShortRecipe(serializers.ModelSerializer):
    """Serializer for short recipe representation."""

    class Meta:
        """Meta class for ShortRecipe."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class DownloadShoppingCart(serializers.Serializer):
    """Serializer for shopping cart download."""

    name = serializers.CharField()
    total_amount = serializers.FloatField()
    measurement_unit = serializers.CharField()


class FollowerSerializer(UserSerializer):
    """Serializer for user followers."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = ShortRecipe(source='recipe_set', read_only=True, many=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        """Meta class for FollowerSerializer."""

        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name',
                  'is_subscribed', 'recipes',
                  'recipes_count', 'avatar')
        read_only_fields = ('id', 'email')

    def get_is_subscribed(self, obj):
        """Return True if the user is subscribed to the given user."""
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return Follower.objects.filter(followed=obj, follower=user).exists()

    def get_recipes_count(self, obj):
        """Return the number of recipes for the given user."""
        return obj.recipe_set.count()
