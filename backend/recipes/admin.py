from django.contrib import admin
from django.db.models import Count

from .models import User, Ingredient, Tag, Recipe


@admin.action(description='Заблокировать выбранных пользователей')
def block_users(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description='Разблокировать выбранных пользователей')
def unblock_users(modeladmin, request, queryset):
    queryset.update(is_active=True)


class UserAdmin(admin.ModelAdmin):
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
        'cooking_time',
        'favorites_count',
    )

    list_editable = ('text',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    autocomplete_fields = ('tags',)

    def get_search_results(self, request, queryset, search_term):
        return super().get_search_results(request, queryset, search_term)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(_favorites_count=Count('favorite'))

    @admin.display(
        description='В избранном',
        ordering='_favorites_count'
    )
    def favorites_count(self, obj):
        if hasattr(obj, '_favorites_count'):
            return obj._favorites_count
        return obj.favorite.count()


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
