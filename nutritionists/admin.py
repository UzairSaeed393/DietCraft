from django.contrib import admin
from .models import Nutritionist

@admin.register(Nutritionist)
class NutritionistAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "experience_years")
    search_fields = ("name", "specialty", "degrees")
    list_filter = ("category",)
