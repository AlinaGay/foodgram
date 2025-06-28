from django.contrib import admin

from .models import User, Ingredient, Tag, Recipe


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'last_name',
        'first_name',
        'role',
        'email'
    )

    list_editable = ('email',)
    search_fields = ('last_name',)
    list_filter = ('role',)


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug'
    )

    list_editable = ('slug',)
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'text',
        'cooking_time'
    )

    list_editable = ('text',)
    search_fields = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)


admin.site.register(User, UserAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
