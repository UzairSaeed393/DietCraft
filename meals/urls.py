from django.urls import path
from . import views

app_name = 'meals'

urlpatterns = [
    path('', views.mealplan_view, name='mealplan'),
    path('fooditems/', views.fooditems, name='fooditems'),
    path('generate-temp/', views.generate_temp_plan, name='generate_temp'),
    path('temp/', views.temp_plan, name='temp_plan'),
    path('exclude/permanent/', views.exclude_permanently, name='exclude_permanent'),
    path('exclude/day/', views.exclude_for_day, name='exclude_for_day'),
    path('finalize/', views.finalize_plan, name='finalize_plan'),
    path('toggle-done/', views.toggle_item_done, name='toggle_item_done'),
]
