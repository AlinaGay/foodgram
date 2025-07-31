"""
Management command to import ingredients from a CSV file into the database.

Reads data from data/ingredients.csv and creates or updates Ingredient objects.
"""

import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from recipes.models import Ingredient


class Command(BaseCommand):
    """Command to import ingredients from data/ingredients.csv."""

    help = 'Import ingredients from data/ingredients.csv'

    def handle(self, *args, **options):
        """
        Read ingredients from CSV and save them to the database.

        Each row must contain at least two columns: name and measurement_unit.
        """
        file_path = '/app/data/ingredients.csv'
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
            self.stdout.write(self.style.SUCCESS(
                f"Imported ingredients: {count}"
            ))
