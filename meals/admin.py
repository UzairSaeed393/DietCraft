from django.contrib import admin
from .models import (
    FoodItem,
    MedicalTag,
    FoodMedicalTag,
    MealPlan,
    MealPlanDay,
    MealItem
)

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ("name", "meal_suitability", "calories_per_serving", "food_type")
    search_fields = ("name",)
    list_filter = ("meal_suitability", "food_type")

@admin.register(MedicalTag)
class MedicalTagAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")

@admin.register(FoodMedicalTag)
class FoodMedicalTagAdmin(admin.ModelAdmin):
    list_display = ("food", "medical_tag")
    list_filter = ("medical_tag",)

@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "week_start", "is_finalized")
    list_filter = ("is_finalized",)
    search_fields = ("user__username",)

@admin.register(MealPlanDay)
class MealPlanDayAdmin(admin.ModelAdmin):
    list_display = ("meal_plan", "day_name", "date")
    list_filter = ("day_name",)

@admin.register(MealItem)
class MealItemAdmin(admin.ModelAdmin):
    list_display = ("day", "food_item", "meal_type", "quantity", "is_completed")
    list_filter = ("meal_type", "is_completed")
    search_fields = ("food_item__name",)