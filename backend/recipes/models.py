"""
Models for the Foodgram project.

Defines custom user, ingredient, tag, recipe,
favorite, shopping cart, and follower models.
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

# User
USER_NAME_MAX_LENGTH = 150
USER_EMAIL_MAX_LENGTH = 254
USERNAME_REGEX = r'^[\w.@+-]+$'

# Ingredient
INGREDIENT_NAME_MAX_LENGTH = 128
INGREDIENT_MESUREMENT_MAX_LENGTH = 64

# Tag
TAG_MAX_LENGTH = 32

# Recipe
RECIPE_NAME_MAX_LENGTH = 256


class User(AbstractUser):
    """Custom user model for Foodgram."""

    first_name = models.CharField(max_length=USER_NAME_MAX_LENGTH)
    last_name = models.CharField(max_length=USER_NAME_MAX_LENGTH)
    username = models.CharField(
        max_length=USER_NAME_MAX_LENGTH,
        unique=True,
        blank=False,
        null=False,
        validators=[
            RegexValidator(
                regex=USERNAME_REGEX,
                message=(
                    'Имя пользователя может содержать только буквы, '
                    'цифры и @/./+/-/_'
                )
            )
        ]
    )
    email = models.EmailField(
        max_length=USER_EMAIL_MAX_LENGTH,
        unique=True,
        blank=False,
        null=False
    )
    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(
        upload_to='users/avatars/',
        null=True,
        blank=True,
        default=None
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'fist_name', 'last_name']

    class Meta:
        """Meta class for User model."""

        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Ingredient(models.Model):
    """Model for ingredients."""

    name = models.CharField(max_length=INGREDIENT_NAME_MAX_LENGTH)
    measurement_unit = models.CharField(
        max_length=INGREDIENT_MESUREMENT_MAX_LENGTH)


class Tag(models.Model):
    """Model for tags."""

    name = models.CharField(max_length=TAG_MAX_LENGTH)
    slug = models.SlugField(
        max_length=TAG_MAX_LENGTH,
        unique=True,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]+$',
                message=('Слаг может содержать только буквы,',
                         'цифры, дефис и нижнее подчёркивание.')
            )
        ]
    )

    def __str__(self):
        """Return string representation of the tag."""
        return self.name


class Recipe(models.Model):
    """Model for recipes."""

    tags = models.ManyToManyField(Tag, through='RecipeTag',
                                  through_fields=('recipe', 'tag'))
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         through_fields=('recipe',
                                                         'ingredient'))
    is_in_shopping_cart = models.BooleanField(default=False)
    name = models.CharField(max_length=RECIPE_NAME_MAX_LENGTH, blank=False)
    image = models.ImageField(
        upload_to='recipes/images/',
        blank=False,
        null=False
    )
    text = models.TextField(blank=False)
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Время приготовления (в минутах), целое число ≥ 1."
    )
    short_link = models.URLField(null=True, blank=True)


class RecipeIngredient(models.Model):
    """Model for ingredients in a recipe."""

    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL,
                               blank=True, null=True)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.SET_NULL,
                                   blank=True, null=True)
    amount = models.PositiveIntegerField(null=True)


class RecipeTag(models.Model):
    """Model for tags in a recipe."""

    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL,
                               blank=True, null=True)
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL,
                            blank=True, null=True)


class Favorite(models.Model):
    """Model for user's favorite recipes."""

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL,
                               blank=True, null=True)


class ShoppingCart(models.Model):
    """Model for user's shopping cart."""

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL,
                               blank=True, null=True)


class Follower(models.Model):
    """Model for user subscriptions."""

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    followed = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers'
    )

    class Meta:
        """Meta class for Follower model."""

        unique_together = ('follower', 'followed')
