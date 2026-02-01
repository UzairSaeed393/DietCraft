from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from authentication.decorators import profile_required

from .models import Exercise, ExercisePlan, ExercisePlanDay
from users.models import UserProfile


# =========================
# Exercise Plan Main Page
# =========================
@profile_required
def exercise_plan_view(request):
    profile = UserProfile.objects.get(user=request.user)
    today = date.today()

    plan = ExercisePlan.objects.filter(
        profile=profile,
        is_active=True
    ).first()

    # No plan or expired
    if not plan or today > plan.end_date:
        return render(request, 'exercises/no_plan.html')

    # Auto current day
    days_passed = (today - plan.start_date).days + 1
    current_day = min(max(days_passed, 1), 7)

    # Manual day navigation
    selected_day = request.GET.get('day')
    if selected_day and selected_day.isdigit():
        current_day = int(selected_day)

    daily_exercises = ExercisePlanDay.objects.filter(
        exercise_plan=plan,
        day_number=current_day
    )

    total_calories = sum(
        item.estimated_calories for item in daily_exercises
    )

    context = {
        'plan': plan,
        'current_day': current_day,
        'daily_exercises': daily_exercises,
        'total_calories': round(total_calories),
    }

    return render(request, 'exercises/exercise_plan.html', context)


# =========================
# Generate Exercise Plan
# =========================
@profile_required
def generate_exercise_plan(request):
    profile = UserProfile.objects.get(user=request.user)

    ExercisePlan.objects.filter(
        profile=profile,
        is_active=True
    ).update(is_active=False)

    start_date = date.today()
    end_date = start_date + timedelta(days=6)

    plan = ExercisePlan.objects.create(
        profile=profile,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )

    GOAL_TO_CATEGORY = {
        'lose': 'weight_loss',
        'gain': 'muscle_gain',
        'maintain': 'maintenance',
    }

    category = GOAL_TO_CATEGORY.get(profile.goal)

    exercises = list(
        Exercise.objects.filter(
            category=category,
            is_active=True
        )
    )

    if not exercises:
        return render(request, 'exercises/no_plan.html')

    index = 0

    for day in range(1, 8):
        for order in range(1, 5):
            exercise = exercises[index % len(exercises)]
            duration_hours = exercise.duration_minutes / 60
            calories = exercise.met_value * profile.weight_kg * duration_hours

            ExercisePlanDay.objects.create(
                exercise_plan=plan,
                day_number=day,
                exercise=exercise,
                order_number=order,
                estimated_calories=round(calories, 2)
            )

            index += 1

    return redirect('exercise_plan_view')


# =========================
# Mark Exercise Done
# =========================
@profile_required
def mark_done(request, item_id):
    item = get_object_or_404(
        ExercisePlanDay,
        id=item_id,
        exercise_plan__profile__user=request.user
    )

    item.is_completed = True
    item.save()

    return redirect('exercise_plan_view')
