from django.shortcuts import render, redirect
from django.contrib import messages
from .models import MealPlan
from users.models import UserProfile
from users.forms import UserProfileForm
from django.contrib.auth.decorators import login_required

@login_required
def meals(request):
    return render(request, "meals/mealplan.html")

