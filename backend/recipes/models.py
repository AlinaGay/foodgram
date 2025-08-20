"""
Models for the Foodgram project.

Defines custom user, ingredient, tag, recipe,
favorite, shopping cart, and follower models.
"""


import hashlib

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import IntegrityError, models
from django.db.models import BooleanField, Exists, OuterRef, Value

from .constants import (
    INGREDIENT_MESUREMENT_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    MIN_TIME,
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


class RecipeManager(models.Manager):
    """
    Custom manager for the Recipe model.

    Provides a method to annotate recipes with user-specific fields,
    such as whether the recipe is favorited or in the user's shopping cart.
    """

    def with_user_annotations(self, user=None):
        """
        Return a queryset of annotated Recipe objects.

        Adds boolean annotations:
        - is_favorited: True if the given user has favorited the recipe.
        - is_in_shopping_cart: True if the recipe
          is in the user's shopping cart.

        If no user is provided or the user is not authenticated,
        both fields are annotated as False.
        """
        queryset = self.get_queryset()

        if user and user.is_authenticated:
            favorited_subquery = Favorite.objects.filter(
                author=user, recipe=OuterRef('pk')
            )
            cart_subquery = ShoppingCart.objects.filter(
                author=user, recipe=OuterRef('pk')
            )
            return queryset.annotate(
                is_favorited=Exists(favorited_subquery),
                is_in_shopping_cart=Exists(cart_subquery)
            )
        return queryset.annotate(
            is_favorited=Value(False, output_field=BooleanField()),
            is_in_shopping_cart=Value(False, output_field=BooleanField())
        )


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
        validators=[MinValueValidator(MIN_TIME)],
        help_text="Время приготовления (в минутах), целое число ≥ 1.",
        verbose_name='Время приготовления'
    )
    short_link = models.URLField(null=True, blank=True)
    objects = RecipeManager()

    class Meta:
        """Meta class for Recipe model."""

        ordering = ['name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def save(self, *args, **kwargs):
        """
        Save the Recipe instance to the database.

        If the short_link field is not set,
        attempts to generate a unique short link
        based on a hash of the author and recipe name.
        """
        if not self.short_link:
            for _ in range(5):
                self.short_link = hashlib.md5(
                    f"{self.author}-{self.name}".encode()
                ).hexdigest()[:8]
                try:
                    super().save(*args, **kwargs)
                    break
                except IntegrityError:
                    self.short_link = None
            else:
                raise ValidationError("Не удалось сгенерировать короткий код.")
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

    author = models.ForeignKey(
        'User', on_delete=models.CASCADE, verbose_name='Пользователь')
    recipe = models.ForeignKey(
        'Recipe', on_delete=models.CASCADE, verbose_name='Рецепт')

    class Meta:
        """Meta class for UserRecipeRelation model."""

        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'recipe'],
                name='unique_%(app_label)s_%(class)s_author_recipe'
            )
        ]
        ordering = ['author']

    def __str__(self):
        """Return a string representation of the UserRecipeRelation model."""
        return f"{self.recipe} ({self.author})"


class Favorite(UserRecipeRelation):
    """Model representing user's favorite recipes."""
    class Meta(UserRecipeRelation.Meta):
        """Meta class for Recipe model."""

        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelation):
    """Model representing user's shopping cart items."""

    class Meta(UserRecipeRelation.Meta):
        """Meta class for Recipe model."""

        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class Follower(models.Model):
    """Model for user subscriptions."""

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик'
    )
    followed = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписка'
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
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'

    def __str__(self):
        """Return a string representation of the Follower model."""
        return f"{self.followed} ({self.follower})"
