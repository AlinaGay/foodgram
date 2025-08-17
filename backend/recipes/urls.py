from django.urls import path

from .views import RecipeShortLinkRedirect

urlpatterns = [
    path(
        'r/<str:short_link>/',
        RecipeShortLinkRedirect.as_view(),
        name='recipe-short'
    ),
]
