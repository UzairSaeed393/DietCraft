from django.shortcuts import render, redirect
from django.contrib import messages
from .models import MealPlan
from users.models import UserProfile
from users.forms import UserProfileForm


def meals(request):
    # User NOT logged in
    if not request.user.is_authenticated:
        messages.warning(request, "Please login first to access meal plans.")
        return redirect("/auth/login/")

    # User logged in → continue
    meal_plan = MealPlan.objects.filter(user=request.user).first()

    # CASE 1: MealPlan exists → show meal plan
    if meal_plan:
        return render(request, "meals/mealplan.html", {
            "meal_plan": meal_plan
        })

    # CASE 2: MealPlan does NOT exist → show profile form
    profile = UserProfile.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            MealPlan.objects.create(user=request.user)
            messages.success(request, "Meal plan generated successfully.")
            return redirect("meals")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "meals/profileform.html", {
        "form": form
    })
