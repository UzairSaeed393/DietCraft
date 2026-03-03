from django.shortcuts import render, redirect
from authentication.decorators import profile_required
from .models import UserProfile
from .forms import UserProfileForm
from django.contrib import messages
from exercises.models import Exercise,ExercisePlan,ExercisePlanDay
from meals.models import MealItem,MealPlanDay,MealPlan
from datetime import date, timedelta
from django.utils import timezone
import json

@profile_required
def profile_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    edit_mode = request.GET.get("edit") == "true"

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
        else:
            messages.error(
                request,
                "Please complete all required fields before saving changes."
            )
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "users/profile.html", {
        "profile": profile,
        "form": form,
        "edit_mode": edit_mode
    })


@profile_required
def dashboard(request):
    profile = UserProfile.objects.filter(user=request.user).first()

    today = date.today()
    # compute week range: monday..sunday for current week
    week_start = today - timedelta(days=today.weekday())
    week_days = [week_start + timedelta(days=i) for i in range(7)]

    # calories & protein consumed per day (meal items linked to MealPlanDay.date)
    daily_calories = []
    daily_protein = []
    total_calories_week = 0
    total_protein_week = 0
    for d in week_days:
        # only count meals the user marked completed
        items = MealItem.objects.filter(day__date=d, day__meal_plan__user=request.user, is_removed=False, is_completed=True)
        day_sum = 0
        day_protein = 0
        for it in items:
            cals = (it.food_item.calories_per_serving or 0) * (it.quantity or 0)
            prot = (it.food_item.proteins_per_serving or 0) * (it.quantity or 0)
            day_sum += cals
            day_protein += prot
        daily_calories.append(int(day_sum))
        daily_protein.append(int(day_protein))
        total_calories_week += day_sum
        total_protein_week += day_protein

    # calories burned estimate: sum ExercisePlanDay.estimated_calories for plans overlapping this week
    week_end = week_start + timedelta(days=6)
    plans = ExercisePlan.objects.filter(profile__user=request.user)
    calories_burned = 0
    workouts_completed = 0
    # per-day exercise stats for the week
    daily_ex_burned = [0 for _ in range(7)]
    daily_ex_completed = [0 for _ in range(7)]
    for p in plans:
        # check overlap
        if p.start_date <= week_end and p.end_date >= week_start:
            eps = ExercisePlanDay.objects.filter(exercise_plan=p)
            for e in eps:
                # map exercise day_number to actual date using plan.start_date
                try:
                    ex_date = p.start_date + timedelta(days=(e.day_number - 1))
                except Exception:
                    continue
                if ex_date >= week_start and ex_date <= week_end:
                    idx = (ex_date - week_start).days
                    # only count completed exercises as burned and completed
                    if e.is_completed:
                        val = e.estimated_calories or 0
                        daily_ex_burned[idx] += val
                        calories_burned += val
                        daily_ex_completed[idx] += 1
                        workouts_completed += 1

    # Today's totals (for current-day progress bars)
    # today's items: only completed meals count as consumed
    today_items = MealItem.objects.filter(day__date=today, day__meal_plan__user=request.user, is_removed=False, is_completed=True)
    today_calories = 0
    today_protein = 0
    for it in today_items:
        today_calories += (it.food_item.calories_per_serving or 0) * (it.quantity or 0)
        today_protein += (it.food_item.proteins_per_serving or 0) * (it.quantity or 0)

    today_ex_burned = 0
    today_ex_completed = 0
    for p in plans:
        if p.start_date <= today and p.end_date >= today:
            eps = ExercisePlanDay.objects.filter(exercise_plan=p)
            for e in eps:
                try:
                    ex_date = p.start_date + timedelta(days=(e.day_number - 1))
                except Exception:
                    continue
                if ex_date == today and e.is_completed:
                    today_ex_burned += e.estimated_calories or 0
                    today_ex_completed += 1

    # compute goals: use TDEE estimate if profile exists
    calorie_target = 2000
    protein_goal_g = 0
    if profile:
        try:
            weight = profile.weight_kg
            height = profile.height_cm
            age = profile.age
            if profile.gender == 'male':
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            else:
                bmr = 10 * weight + 6.25 * height - 5 * age - 161

            activity_map = {
                'sedentary': 1.2,
                'light': 1.375,
                'moderate': 1.55,
                'active': 1.725,
                'very_active': 1.9,
            }
            mult = activity_map.get(profile.activity_level, 1.2)
            calorie_target = int(bmr * mult)
            protein_goal_g = int(1.2 * weight)
        except Exception:
            calorie_target = 2000
            protein_goal_g = 80
    else:
        protein_goal_g = 80

    # per-day exercise total and weekly workout goal (4 per day → 28 per week)
    daily_ex_total = 4
    weekly_workout_goal = daily_ex_total * 7
    # planned weekly totals from user's plan/targets
    planned_calories_week = calorie_target * 7
    # planned protein (weekly)
    planned_protein_week = protein_goal_g * 7

    # planned exercise burn for overlapping plans (sum all estimated_calories irrespective of completion)
    planned_ex_burn_week = 0
    for p in plans:
        if p.start_date <= week_end and p.end_date >= week_start:
            eps_all = ExercisePlanDay.objects.filter(exercise_plan=p)
            for e in eps_all:
                planned_ex_burn_week += e.estimated_calories or 0

    # prepare progress percentages
    calorie_progress = min(int((total_calories_week / (calorie_target * 7)) * 100) if calorie_target else 0, 100)
    protein_progress = min(int((total_protein_week / (protein_goal_g * 7)) * 100) if protein_goal_g else 0, 100)
    workout_progress = min(int((workouts_completed / weekly_workout_goal) * 100) if weekly_workout_goal else 0, 100)

    context = {
        'profile': profile,
        'daily_calories': daily_calories,
        'daily_protein': daily_protein,
        'total_calories_week': int(total_calories_week),
        'calories_burned': int(calories_burned),
        'current_weight': profile.weight_kg if profile else None,
        'calorie_target': calorie_target,
        'protein_goal_g': protein_goal_g,
        'total_protein_week': int(total_protein_week),
        'weekly_workout_goal': weekly_workout_goal,
        'workouts_completed': workouts_completed,
        'calorie_progress': calorie_progress,
        'protein_progress': protein_progress,
        'workout_progress': workout_progress,
        'week_labels': [d.strftime('%a') for d in week_days],
        'daily_calorie_avg': int(total_calories_week / 7) if total_calories_week else 0,
        'daily_protein_avg': int(total_protein_week / 7) if total_protein_week else 0,
        'daily_ex_burned': daily_ex_burned,
        'daily_ex_completed': daily_ex_completed,
        'daily_ex_total': daily_ex_total,
        'today_calories': int(today_calories),
        'today_protein': int(today_protein),
        'today_ex_burned': int(today_ex_burned),
        'today_ex_completed': int(today_ex_completed),
        'planned_calories_week': planned_calories_week,
        'planned_protein_week': planned_protein_week,
        'planned_ex_burn_week': planned_ex_burn_week,
    }

    # Add JSON-encoded strings for safe client-side parsing
    context['week_labels_json'] = json.dumps(context['week_labels'])
    context['daily_calories_json'] = json.dumps(context['daily_calories'])
    context['daily_protein_json'] = json.dumps(context['daily_protein'])
    context['daily_ex_burned_json'] = json.dumps(context['daily_ex_burned'])
    context['daily_ex_completed_json'] = json.dumps(context['daily_ex_completed'])

    return render(request, 'users/dashboard.html', context)
