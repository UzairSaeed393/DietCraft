import csv
from django.core.management.base import BaseCommand
from meals.models import FoodItem, MedicalTag, FoodMedicalTag


class Command(BaseCommand):
    help = "Import food items and medical tags from CSV files"

    def handle(self, *args, **kwargs):

        self.stdout.write(self.style.SUCCESS("Starting CSV import..."))

        # =========================
        # 1. Import Medical Tags
        # =========================
        # with open('meals/data/medical_tags.csv', newline='', encoding='utf-8') as file:
        #     reader = csv.DictReader(file)
        #     for row in reader:
        #         MedicalTag.objects.get_or_create(
        #             code=row['code'],
        #             defaults={'name': row['name']}
        #         )

        # self.stdout.write(self.style.SUCCESS(" Medical tags imported"))

        # =========================
        # 2. Import Food Items
        # =========================
        with open('meals/data/food_clean.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                FoodItem.objects.get_or_create(
                    id=row['id'], 
                    defaults={
                        'name': row['name'],
                        'calories_per_serving': row['calories'],
                        'proteins_per_serving': row['protein'],  
                        'carbs_per_serving': row['carbs'],
                        'fats_per_serving': row['fat'],         
                        'food_type': row['type'],             
                    }
                )
        self.stdout.write(self.style.SUCCESS(" Food items imported"))
        # =========================
        # 3. Import Food–Medical Mapping
        # =========================
        with open('meals/data/food_medical_mapping.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    food = FoodItem.objects.get(id=row['food_id'])
                    medical = MedicalTag.objects.get(id=row['medical_tag_id'])

                    FoodMedicalTag.objects.get_or_create(
                        food=food,
                        medical_tag=medical
                    )
                except (FoodItem.DoesNotExist, MedicalTag.DoesNotExist):
                    continue

        self.stdout.write(self.style.SUCCESS(" Food–medical mappings imported"))
        self.stdout.write(self.style.SUCCESS(" CSV import completed successfully"))
