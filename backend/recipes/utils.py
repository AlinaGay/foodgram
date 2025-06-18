import hashlib
from django.conf import settings


def generate_short_link(recipe_id):
    hash_obj = hashlib.md5(f'recipe_{recipe_id}'.encode())
    return f'{settings.BASE_URL}/r/{hash_obj.hexdigest()[:8]}'
