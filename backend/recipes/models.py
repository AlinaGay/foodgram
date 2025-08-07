"""
Models for the Foodgram project.

Defines custom user, ingredient, tag, recipe,
favorite, shopping cart, and follower models.
"""


import hashlib

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import (
    INGREDIENT_MESUREMENT_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    MIN_VALUE,
    RECIPE_NAME_MAX_LENGTH,
    TAG_MAX_LENGTH,
    USER_EMAIL_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USERNAME_REGEX,
)


class User(AbstractUser):
    """Custom user model for Foodgram."""

    first_name = models.CharField(
        max_length=USER_NAME_MAX_LENGTH, verbose_name='Имя')
    last_name = models.CharField(
        max_length=USER_NAME_MAX_LENGTH, verbose_name='Фамилия')
    username = models.CharField(
        max_length=USER_NAME_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=USERNAME_REGEX,
                message=(
                    'Имя пользователя может содержать только буквы, '
                    'цифры и @/./+/-/_'
                )
            )
        ],
        verbose_name='Ник'
    )
    email = models.EmailField(
        max_length=USER_EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='Электронная почта'
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        null=True,
        blank=True,
        default=None,
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        """Meta class for User model."""

        ordering = ['first_name', 'last_name', 'username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Return a string representation of the User model."""
        return f"{self.first_name} {self.last_name}"


class Ingredient(models.Model):
    """Model for ingredients."""

    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH, verbose_name='Наименование')
    measurement_unit = models.CharField(
        max_length=INGREDIENT_MESUREMENT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        """Meta class for Ingredient model."""

        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_name_unit'
            )
        ]
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        """Return a string representation of the Ingredient model."""
        return f"{self.name} ({self.measurement_unit})"


class Tag(models.Model):
    """Model for tags."""

    name = models.CharField(
        max_length=TAG_MAX_LENGTH, unique=True, verbose_name='Наименование')
    slug = models.SlugField(
        max_length=TAG_MAX_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        """Meta class for Tag model."""

        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """Return a string representation of the Tag model."""
        return f"{self.name} ({self.slug})"


class Recipe(models.Model):
    """Model for recipes."""

    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         through_fields=('recipe',
                                                         'ingredient'),
                                         verbose_name='Ингредиенты')
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH, verbose_name='Наименование')
    image = models.ImageField(
        upload_to='recipes/images/',
        null=False,
        verbose_name='Изображение'
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_VALUE)],
        help_text="Время приготовления (в минутах), целое число ≥ 1.",
        verbose_name='Время приготовления'
    )
    short_link = models.URLField(null=True, blank=True)

    class Meta:
        """Meta class for Recipe model."""

        ordering = ['name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def save(self, *args, **kwargs):
        """
        Saves the Recipe instance to the database.

        If the instance is being created and does
        not have a short_link, generates a unique short_link
        using an MD5 hash of the primary key and name.
        The short_link is constructed using either the
        request's absolute URI or a default domain
        from settings. If a Recipe with the same short_link
        already exists, raises a ValidationError.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
            May include 'request' for building absolute URI.

        Raises:
            ValidationError: If the generated
            short_link already exists in the database.
        """
        if not self.pk and not self.short_link:
            super().save(*args, **kwargs)
            short_hash = hashlib.md5(
                f"{self.pk}-{self.name}".encode()
            ).hexdigest()[:8]
            request = kwargs.pop('request', None)

            if request:
                self.short_link = request.build_absolute_uri(
                    f'/r/{short_hash}/')
            else:
                domain = getattr(settings, 'DEFAULT_DOMAIN', 'localhost:8000')
                self.short_link = f'http://{domain}/{short_hash}/'
            if Recipe.objects.filter(short_link=self.short_link).exists():
                raise ValidationError("Короткая ссылка уже существует.")

            super().save(update_fields=['short_link'])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        """Return a string representation of the Recipe model."""
        return f"{self.name} ({self.author})"


class RecipeIngredient(models.Model):
    """Model for ingredients in a recipe."""

    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL,
                               blank=True, null=True)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.SET_NULL,
                                   blank=True, null=True)
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_VALUE)]
    )

    class Meta:
        """Meta class for RecipeIngredient model."""

        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]
        verbose_name = 'Ингредиент для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'

    def __str__(self):
        """Return a string representation of the RecipeIngredient model."""
        return f"{self.ingredient} ({self.recipe})"


class UserRecipeRelation(models.Model):
    """
    Abstract base model for user-recipe relationships.

    Provides common fields and unique constraints for derived models.
    """

    author = models.ForeignKey('User', on_delete=models.CASCADE)
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)

    class Meta:
        """Meta class for UserRecipeRelation model."""

        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'recipe'],
                name='unique_%(app_label)s_%(class)s_author_recipe'
            )
        ]

    def __str__(self):
        """Return a string representation of the UserRecipeRelation model."""
        return f"{self.recipe} ({self.author})"


class Favorite(UserRecipeRelation):
    """Model representing user's favorite recipes."""


class ShoppingCart(UserRecipeRelation):
    """Model representing user's shopping cart items."""


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
        """Meta options for Follower model."""

        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'followed'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(follower=models.F('followed')),
                name='prevent_self_follow'
            )
        ]

    def __str__(self):
        """Return a string representation of the Follower model."""
        return f"{self.followed} ({self.follower})"
