from django.shortcuts import render, redirect
from django.contrib import messages
from authentication.decorators import profile_required
from datetime import date
from .models import MealPlan, MealItem, FoodItem, FoodMedicalTag, MedicalTag

def fooditems(request):
    """Render a responsive table of food items. Client-side JS will handle
    searching and filtering .
    """
    items = FoodItem.objects.all().order_by('name')
    return render(request, "meals/Fooditems.html", {"fooditems": items})

# Meal Plan View
@profile_required
def meals(request):

    try:
        meal_plan = MealPlan.objects.get(user=request.user)

        profile = request.user.profile

        # Step 1: BMR
        bmr = calculate_bmr(profile)

        # Step 2: TDEE
        tdee = calculate_tdee(bmr, profile.activity_level)

        # Step 3: Daily Calories
        daily_calories = calculate_daily_calories(tdee, profile.goal)

        context = {
            "meal_plan": meal_plan,
            "daily_calories": daily_calories,
        }

        return render(request, "meals/mealplan.html", context)

    except MealPlan.DoesNotExist:
        return render(request, "meals/noplan.html")
    
#  BMR Calculation
def calculate_bmr(profile):

    weight = profile.weight_kg
    height = profile.height_cm
    age = profile.age
    gender = profile.gender

    if gender == "male":
        return (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        return (10 * weight) + (6.25 * height) - (5 * age) - 161

#  TDEE Calculation
def calculate_tdee(bmr, activity_level):

    ACTIVITY_MULTIPLIER = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }

    multiplier = ACTIVITY_MULTIPLIER.get(activity_level, 1.2)

    return bmr * multiplier


#  Goal Based Calories
def calculate_daily_calories(tdee, goal):

    GOAL_MULTIPLIER = {
        "lose": 0.8,
        "maintain": 1.0,
        "gain": 1.15,
    }

    multiplier = GOAL_MULTIPLIER.get(goal, 1.0)

    return round(tdee * multiplier)

