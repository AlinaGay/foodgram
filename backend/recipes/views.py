from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import Recipe


class RecipeShortLinkRedirect(APIView):
    """View for handling short links redirection to frontend."""

    permission_classes = [AllowAny]

    def get(self, request, short_link):
        try:
            recipe = Recipe.objects.get(short_link=short_link)
            return redirect(f'api/recipes/{recipe.id}')
        except ObjectDoesNotExist:
            return redirect('/404')
