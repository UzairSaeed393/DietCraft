from django.contrib import admin
from .models import Exercise
# Register your models here.
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'difficulty', 'met_value', 'duration_minutes', 'is_active')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('name',)