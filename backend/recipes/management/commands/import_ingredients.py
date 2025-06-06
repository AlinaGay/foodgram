import csv
import os

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import ingredients from data/ingredients.csv'

    def handle(self, *args, **options):
        file_path = '/Users/alina/Dev/foodgram/data/ingredients.csv'
        if not os.path.exists(file_path):
            self.stderr.write(f'File {file_path} is not found.')
            return

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            count = 0
            for row in reader:
                if len(row) < 2:
                    continue
                try:
                    Ingredient.objects.update_or_create(
                        name=row[0],
                        defaults={'measurement_unit': row[1]}
                    )
                    count += 1
                except IntegrityError as e:
                    self.stderr.write(f"[Ingredient] Error: {e}")
                except Exception as e:
                    self.stderr.write(f"Unexpected error: {e}")
            self.stdout.write(self.style.SUCCESS
                              (f"Imported ingredients: {count}"))
