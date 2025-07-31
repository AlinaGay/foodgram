"""
Management command to import ingredients from a CSV file into the database.

Reads data from data/ingredients.csv and creates or updates Ingredient objects.
"""

import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Command to import ingredients from data/ingredients.csv."""

    help = 'Import ingredients from data/ingredients.csv'

    def handle(self, *args, **options):
        """
        Read ingredients from CSV and save them to the database.

        Each row must contain at least two columns: name and measurement_unit.
        """
        file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.csv')
        if not os.path.exists(file_path):
            self.stderr.write(f'File {file_path} is not found.')
            return

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            ingredients = []
            for row in reader:
                if len(row) < 2:
                    continue
                ingredients.append(
                    Ingredient(name=row[0], measurement_unit=row[1]))
            try:
                Ingredient.objects.bulk_create(
                    ingredients, ignore_conflicts=True
                )
                self.stdout.write(self.style.SUCCESS(
                    f"Imported ingredients: {len(ingredients)}"
                ))
            except Exception as e:
                self.stderr.write(f"Unexpected error: {e}")
