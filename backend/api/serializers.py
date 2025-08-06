"""
Serializers for Foodgram API.

This module defines custom and model serializers
for users, recipes, ingredients, tags, favorites, followers, and shopping cart.
"""

from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Follower,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from .serializer_fields import Base64ImageField

User = get_user_model()


class UserConfigSerializer(UserSerializer):
    """Serializer for user representation with subscription and avatar."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        """Meta class for UserConfigSerializer."""

        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'is_subscribed', 'avatar')
        read_only_fields = ('id', 'email')

    def get_is_subscribed(self, obj):
        """Return True if the current user is subscribed to obj."""
        request = self.context.get('request')
        return (
            bool(request)
            and request.user.is_authenticated
            and Follower.objects.filter(
                follower=request.user, followed=obj).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer for user avatar."""

    avatar = Base64ImageField()

    class Meta:
        """Meta class for AvatarSerializer."""

        model = User
        fields = ('avatar',)
        extra_kwargs = {
            'avatar': {'required': True},
        }


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

    author = UserConfigSerializer(read_only=True)
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

    def validate_amount(self, value):
        """Return recipes for the given user."""
        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше нуля.'
            )
        return value


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Serializer for writing recipes."""

    author = UserConfigSerializer(read_only=True)
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=True, allow_null=False)

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


class ShortRecipe(serializers.ModelSerializer):
    """Serializer for short recipe representation."""

    class Meta:
        """Meta class for ShortRecipe."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowerSerializer(UserSerializer):
    """Serializer for user followers."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
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

    def get_recipes(self, obj):
        """Return recipes with optional limit from query params."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        recipes_queryset = obj.recipe_set.all()

        if recipes_limit and recipes_limit.isdigit():
            recipes_queryset = recipes_queryset[:int(recipes_limit)]

        serializer = ShortRecipe(
            recipes_queryset, many=True, context={'request': request})
        return serializer.data
