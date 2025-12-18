from django.contrib import admin
from .models import Nutritionist

@admin.register(Nutritionist)
class NutritionistAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "category", "experience_years", "rating")
    search_fields = ("name", "specialty", "degrees", "clinic_name", "city")
    list_filter = ("city", "category")
