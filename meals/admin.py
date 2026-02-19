from django.contrib import admin
from .models import FoodItem, MedicalTag, FoodMedicalTag

# Register your models here.
@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'food_type', 'calories_per_serving')
    search_fields = ('name',)
    list_filter = ('food_type',)
    
admin.site.register(MedicalTag)
admin.site.register(FoodMedicalTag)