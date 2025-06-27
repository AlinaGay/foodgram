from django.contrib import admin

from .models import User, Ingredient, Tag, Recipe


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'last_name',
        'first_name',
        'role',
        'email'
    )

    list_iditable = (
        'last_name',
        'first_name',
        'email'
    )

    search_fields = ('last_name',)
    list_filter = ('role',)


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug'
    )

    list_iditable = (
        'title',
        'slug'
    )

    search_fields = ('name',)
    list_filter = ('name',)
    list_display_links = ('name',)


admin.site.register(User, UserAdmin)
admin.site.register(Ingredient)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe)
