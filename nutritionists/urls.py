from django.urls import path
from . import views

urlpatterns = [
    path('', views.nutritionists, name='nutritionists'),
]
