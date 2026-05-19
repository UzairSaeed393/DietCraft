from django.urls import path
from . import views
urlpatterns = [
    path('', views.dashboard, name="dashboard"),
    path('profile/', views.profile_view, name="profile"),
    path('profile/delete-meal-plan/', views.delete_meal_plan, name="delete_meal_plan"),
    path('profile/delete-exercise-plan/', views.delete_exercise_plan, name="delete_exercise_plan"),
]
