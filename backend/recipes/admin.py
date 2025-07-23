"""
Admin configuration for Foodgram project.

Registers models and customizes admin interface
for User, Ingredient, Tag, and Recipe.
"""

from django.contrib import admin
from django.db.models import Count

from .models import User, Ingredient, Tag, Recipe


@admin.action(description='Заблокировать выбранных пользователей')
def block_users(modeladmin, request, queryset):
    """Block selected users by setting is_active to False."""
    queryset.update(is_active=False)


@admin.action(description='Разблокировать выбранных пользователей')
def unblock_users(modeladmin, request, queryset):
    """Unblock selected users by setting is_active to True."""
    queryset.update(is_active=True)


class UserAdmin(admin.ModelAdmin):
    """Admin configuration for User model."""

    list_display = (
        'last_name',
        'first_name',
        'role',
        'email'
    )

    list_editable = ('email',)
    search_fields = ('first_name', 'email')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    actions = (block_users, unblock_users)


class TagAdmin(admin.ModelAdmin):
    """Admin configuration for Tag model."""

    list_display = (
        'name',
        'slug'
    )

    list_editable = ('slug',)
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    """Admin configuration for Recipe model."""

    list_display = (
        'name',
        'author',
        'text',
        'cooking_time',
        'favorites_count',
    )

    list_editable = ('text',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    autocomplete_fields = ('tags',)

    def get_search_results(self, request, queryset, search_term):
        """Return search results for recipes."""
        return super().get_search_results(request, queryset, search_term)

    def get_queryset(self, request):
        """Annotate queryset with favorites count."""
        queryset = super().get_queryset(request)
        return queryset.annotate(_favorites_count=Count('favorite'))

    @admin.display(
        description='В избранном',
        ordering='_favorites_count'
    )
    def favorites_count(self, obj):
        """Return the number of times the recipe is favorited."""
        if hasattr(obj, '_favorites_count'):
            return obj._favorites_count
        return obj.favorite.count()


class IngredientAdmin(admin.ModelAdmin):
    """Admin configuration for Ingredient model."""

    list_display = (
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)


admin.site.register(User, UserAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
