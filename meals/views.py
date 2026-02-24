from django.shortcuts import render, redirect
from django.contrib import messages
from .models import MealPlan, FoodItem
from users.models import UserProfile
from users.forms import UserProfileForm
from authentication.decorators import profile_required

@profile_required
def meals(request):
    return render(request, "meals/mealplan.html")

def fooditems(request):
    """Render a responsive table of food items. Client-side JS will handle
    searching and filtering .
    """
    items = FoodItem.objects.all().order_by('name')
    return render(request, "meals/Fooditems.html", {"fooditems": items})