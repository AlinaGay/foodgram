"""App configuration for the Recipes application."""

from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """Configuration class for the Recipes app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
