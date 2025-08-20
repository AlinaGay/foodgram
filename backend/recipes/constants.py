"""
Constants for the Foodgram project.

Defines max lengths, regex patterns, and minimum values for models.
"""

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
MIN_TIME = 1
MIN_VALUE = 1
RECIPE_NAME_MAX_LENGTH = 256
