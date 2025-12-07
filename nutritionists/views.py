from django.shortcuts import render
from .models import Nutritionist
from django.db import models


def nutritionists(request):
    search = request.GET.get("search", "")
    category = request.GET.get("category", "")

    nutritionists = Nutritionist.objects.all()

    if search:
        nutritionists = nutritionists.filter(
            models.Q(name__icontains=search) |
            models.Q(specialty__icontains=search) |
            models.Q(degrees__icontains=search)
        )

    if category:
        nutritionists = nutritionists.filter(category=category)

    context = {
        "nutritionists": nutritionists,
        "search": search,
        "category": category,
    }
    return render(request, "nutritionists/nutritionists.html", context)
