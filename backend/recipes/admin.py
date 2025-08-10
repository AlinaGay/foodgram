"""
Admin configuration for Foodgram project.

Registers models and customizes admin interface
for User, Ingredient, Tag, and Recipe.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from .models import (
    Favorite,
    Follower,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
    User,
)


@admin.action(description='Заблокировать выбранных пользователей')
def block_users(modeladmin, request, queryset):
    """Block selected users by setting is_active to False."""
    queryset.update(is_active=False)


@admin.action(description='Разблокировать выбранных пользователей')
def unblock_users(modeladmin, request, queryset):
    """Unblock selected users by setting is_active to True."""
    queryset.update(is_active=True)


class UserAdminConfig(UserAdmin):
    """Admin configuration for User model."""

    list_display = (
        'last_name',
        'first_name',
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


class RecipeIngredientInline(admin.TabularInline):
    """Inline for ingredients of recipe."""

    model = RecipeIngredient
    extra = 1
    min_num = 1
    fields = ('ingredient', 'amount')


class RecipeAdmin(admin.ModelAdmin):
    """Admin configuration for Recipe model."""

    inlines = [RecipeIngredientInline]
    list_display = (
        'name',
        'author',
        'text',
        'cooking_time',
        'favorites_count',
    )
    exclude = ('short_link',)
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
        return queryset.annotate(
            _favorites_count=Count('favorite')
        ).order_by('name')

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


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('follower', 'followed')
    list_filter = ('followed',)
    search_fields = ('follower__username', 'followed__username')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipe')
    list_filter = ('author', 'recipe')
    search_fields = ('author__username', 'recipe__name')


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipe')
    list_filter = ('author', 'recipe')
    search_fields = ('author__username', 'recipe__name')


admin.site.register(User, UserAdminConfig)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Follower, SubscriptionAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
