from django.urls import path
from .views import meals

urlpatterns = [
    path('', meals, name="meals"),
]
