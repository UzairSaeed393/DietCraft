from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from authentication.decorators import profile_required

from .models import MealPlan, MealItem, FoodItem
from . import meal_engine


def get_latest_plan(user, finalized):
    """Return latest plan or None."""
    return MealPlan.objects.filter(
        user=user,
        is_finalized=finalized
    ).order_by("-created_at").first()


def get_selected_day(meal_plan, request):
    """Return selected day + navigation list."""
    days = list(meal_plan.days.all().order_by("date"))

    if not days:
        return None, None, None

    try:
        index = int(request.GET.get("day", 0))
    except:
        index = 0

    index = max(0, min(index, len(days) - 1))
    selected_day = days[index]

    day_list = [
        {"index": i, "name": d.day_name.title(), "date": d.date}
        for i, d in enumerate(days)
    ]

    return selected_day, day_list, index


def calculate_day_totals(day):
    """Compute calories + macros for one day."""
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    meals_data = []

    for mi in day.meals.select_related("food_item"):
        f = mi.food_item
        qty = float(mi.quantity or 1)

        cals = float(getattr(f, "calories_per_serving", 0))
        protein = float(getattr(f, "proteins_per_serving", 0))
        carbs = float(getattr(f, "carbs_per_serving", 0))
        fat = float(getattr(f, "fats_per_serving", 0))

        item = {
            "id": mi.id,
            "food_id": f.id,
            "meal_type": mi.get_meal_type_display(),
            "name": f.name,
            "quantity": qty,
            "cal_per_serv": cals,
            "cal_total": round(cals * qty, 0),
            "protein_per": protein,
            "protein_total": round(protein * qty, 1),
            "carbs_per": carbs,
            "carbs_total": round(carbs * qty, 1),
            "fat_per": fat,
            "fat_total": round(fat * qty, 1),
            "food_type": f.get_food_type_display(),
            "is_completed": mi.is_completed,
        }

        totals["calories"] += item["cal_total"]
        totals["protein"] += item["protein_total"]
        totals["carbs"] += item["carbs_total"]
        totals["fat"] += item["fat_total"]

        meals_data.append(item)

    return totals, meals_data


def render_plan(request, meal_plan, template, is_temp):
    """Shared renderer for temp + finalized plan."""
    selected_day, day_list, index = get_selected_day(meal_plan, request)

    if not selected_day:
        return render(request, "meals/noplan.html")

    totals, meals_data = calculate_day_totals(selected_day)

    daily_info = meal_engine.generate_daily_macro_plan(request.user.profile)

    context = {
        "meal_plan": meal_plan,
        "is_temp": is_temp,
        "selected_day": selected_day,
        "day_list": day_list,
        "selected_index": index,
        "totals": totals,
        "daily_calories": daily_info["calories"],
        "meals_data": meals_data,
    }

    return render(request, template, context)

#  FOOD LIST

def fooditems(request):
    items = FoodItem.objects.all().order_by("name")
    return render(request, "meals/Fooditems.html", {"fooditems": items})


# GENERATE TEMP PLAN 
@profile_required
def generate_temp_plan(request):
    try:
        meal_engine.generate_temp_meal_plan(request.user)
        messages.success(request, "Temporary meal plan generated")
    except Exception as e:
        messages.error(request, f"Could not generate plan: {e}")

    return redirect("meals:temp_plan")


# TEMP PLAN VIEW 

@profile_required
def temp_plan(request):
    meal_plan = get_latest_plan(request.user, finalized=False)

    if not meal_plan:
        messages.info(request, "Generate a plan first")
        return redirect("meals:fooditems")

    return render_plan(request, meal_plan, "meals/temp_plan.html", True)


#  EXCLUDE FOOD PERMANENTLY 

@require_POST
@profile_required
def exclude_permanently(request):
    food_id = int(request.POST.get("food_id"))
    profile = request.user.profile

    excluded = profile.excluded_foods or []

    if food_id not in excluded:
        excluded.append(food_id)
        profile.excluded_foods = excluded
        profile.save()

        meal_engine.generate_temp_meal_plan(request.user)
        messages.success(request, "Food excluded permanently")

    return redirect("meals:temp_plan")


# EXCLUDE FOOD FOR SINGLE DAY

@require_POST
@profile_required
def exclude_for_day(request):
    item_id = int(request.POST.get("meal_item_id"))
    meal_item = get_object_or_404(MealItem, id=item_id)

    profile = request.user.profile
    foods = list(meal_engine.get_filtered_foods(profile))

    # Filter by meal type
    if meal_item.meal_type == "snack":
        foods = [f for f in foods if f.food_type in ["drink", "snack"]]
    else:
        foods = [f for f in foods if f.food_type != "drink"]

    used_ids = list(meal_item.day.meals.values_list("food_item_id", flat=True))

    daily_plan = meal_engine.generate_daily_macro_plan(profile)
    meal_targets = meal_engine.split_macros_into_meals(daily_plan)
    targets = meal_targets.get(meal_item.meal_type)

    weekly_usage = {}

    picked = meal_engine.pick_food_for_target(
        foods,
        targets,
        used_ids,
        weekly_usage
    )

    if not picked:
        messages.error(request, "No replacement found")
        return redirect("meals:temp_plan")

    food, qty = picked[0]

    meal_item.delete()

    MealItem.objects.create(
        day=meal_item.day,
        food_item=food,
        meal_type=meal_item.meal_type,
        quantity=qty
    )

    messages.success(request, "Item replaced")
    return redirect("meals:temp_plan")

# FINALIZE PLAN 

@require_POST
@profile_required
def finalize_plan(request):
    meal_plan = get_latest_plan(request.user, finalized=False)

    if not meal_plan:
        messages.error(request, "No temporary plan")
        return redirect("meals:temp_plan")

    meal_engine.finalize_meal_plan(meal_plan)
    messages.success(request, "Meal plan finalized")

    return redirect("meals:mealplan")


# FINALIZED PLAN VIEW 

@profile_required
def mealplan_view(request):
    meal_plan = get_latest_plan(request.user, finalized=True)

    if not meal_plan:
        return render(request, "meals/noplan.html")

    return render_plan(request, meal_plan, "meals/mealplan.html", False)


# TOGGLE COMPLETED

@require_POST
@profile_required
def toggle_item_done(request):
    item_id = int(request.POST.get("item_id"))

    item = get_object_or_404(
        MealItem,
        id=item_id,
        day__meal_plan__user=request.user
    )

    item.is_completed = not item.is_completed
    item.save()

    return redirect("meals:mealplan")