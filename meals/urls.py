from django.urls import path
from .views import meals, fooditems

urlpatterns = [
    path('', meals, name="meals"),
    path('fooditems/', fooditems, name="fooditems"),
]
