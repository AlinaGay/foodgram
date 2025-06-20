from django.contrib.auth.models import AbstractUser
from django.db import models


SLUG_MAX_LENGTH = 50
NAME_MAX_LENGTH = 256


class User(AbstractUser):
    USER = 'user'
    ADMIN = 'admin'

    ROLE_CHOICES = (
        (ADMIN, 'Администратор'),
        (USER, 'Пользователь')
    )
    first_name = models.CharField(max_length=NAME_MAX_LENGTH)
    last_name = models.CharField(max_length=NAME_MAX_LENGTH)
    username = models.CharField(max_length=NAME_MAX_LENGTH,
                                blank=True, null=True)
    role = models.CharField(
        max_length=max(len(role) for role, _ in ROLE_CHOICES),
        choices=ROLE_CHOICES,
        default=USER
    )
    email = models.EmailField(unique=True)
    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(
        upload_to='users/avatars/',
        null=True,
        default=None
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser


class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=64)


class Tag(models.Model):
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    slug = models.SlugField(max_length=SLUG_MAX_LENGTH, unique=True)


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag, through='RecipeTag',
                                  through_fields=('recipe', 'tag'))
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         through_fields=('recipe',
                                                         'ingredient'))
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None
    )
    text = models.TextField()
    cooking_time = models.PositiveIntegerField()
    short_link = models.URLField(null=True, blank=True)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL,
                               blank=True, null=True)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.SET_NULL,
                                   blank=True, null=True)
    amount = models.PositiveIntegerField(null=True)


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL,
                               blank=True, null=True)
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL,
                            blank=True, null=True)


class Favorite(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL,
                               blank=True, null=True)
