from django.contrib import admin

from .models import User, Ingredient, Tag, Recipe


admin.site.register(User)
admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(Recipe)
