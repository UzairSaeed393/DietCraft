from django.shortcuts import render, redirect
from django.contrib import messages
from .models import MealPlan
from users.models import UserProfile
from users.forms import UserProfileForm
from authentication.decorators import profile_required

@profile_required
def meals(request):
    return render(request, "meals/mealplan.html")

