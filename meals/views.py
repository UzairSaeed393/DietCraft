from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from authentication.decorators import profile_required
from .models import MealPlan, MealItem, FoodItem
from . import meal_engine
from users.models import UserProfile

def fooditems(request):
    items = FoodItem.objects.all().order_by('name')
    return render(request, "meals/Fooditems.html", {"fooditems": items})


@profile_required
def generate_temp_plan(request):
    """Generate a temporary (preview) weekly plan for the user.
    This creates a MealPlan with `is_finalized=False` that will be shown
    in the temp plan view where user can exclude items.
    """
    profile = request.user.profile
    # use permanent excludes from profile automatically (meal_engine handles it)
    try:
        meal_plan = meal_engine.generate_temp_meal_plan(request.user)
        messages.success(request, "Temporary meal plan generated")
    except Exception as e:
        messages.error(request, f"Could not generate plan: {e}")

    return redirect('meals:temp_plan')


@profile_required
def temp_plan(request):
    """Show the temporary (preview) plan where user can exclude items.
    Exclude actions trigger POST endpoints that will either permanently
    add an id to the profile excluded list or replace a single meal item.
    """
    try:
        meal_plan = MealPlan.objects.filter(user=request.user, is_finalized=False).latest('created_at')
    except MealPlan.DoesNotExist:
        messages.info(request, "No temporary plan found. Generate one first.")
        return redirect('meals:fooditems')

    # day navigation: accept ?day=index (0..6)
    day_index = 0
    try:
        day_index = int(request.GET.get('day', 0))
    except (TypeError, ValueError):
        day_index = 0

    days_qs = meal_plan.days.all().order_by('date')
    if days_qs.count() == 0:
        messages.error(request, 'No days found in this meal plan.')
        return render(request, 'meals/noplan.html')

    day_index = max(0, min(day_index, max(0, days_qs.count() - 1)))
    selected_day = days_qs[day_index]

    # ensure we have a profile and compute daily calories (profile-level)
    profile = request.user.profile
    daily_info = meal_engine.generate_daily_macro_plan(profile)
    daily_calories = daily_info.get('calories')

    totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    meals_data = []
    for mi in selected_day.meals.all():
        fs = mi.food_item
        qty = float(mi.quantity or 1)
        cals = float(getattr(fs, 'calories_per_serving', 0))
        proteins = float(getattr(fs, 'proteins_per_serving', 0))
        carbs = float(getattr(fs, 'carbs_per_serving', 0))
        fats = float(getattr(fs, 'fats_per_serving', 0))

        item_totals = {
            'id': mi.id,
            'food_id': fs.id,
            'meal_type': mi.get_meal_type_display(),
            'name': fs.name,
            'quantity': qty,
            'cal_per_serv': cals,
            'cal_total': round(cals * qty, 0),
            'protein_per': proteins,
            'protein_total': round(proteins * qty, 1),
            'carbs_per': carbs,
            'carbs_total': round(carbs * qty, 1),
            'fat_per': fats,
            'fat_total': round(fats * qty, 1),
            'food_type': fs.get_food_type_display(),
            'is_completed': mi.is_completed,
        }

        totals['calories'] += item_totals['cal_total']
        totals['protein'] += item_totals['protein_total']
        totals['carbs'] += item_totals['carbs_total']
        totals['fat'] += item_totals['fat_total']

        meals_data.append(item_totals)

    # build small day list for navigation
    day_list = [
        {'index': idx, 'name': d.day_name.title(), 'date': d.date}
        for idx, d in enumerate(days_qs)
    ]

    context = {
        'meal_plan': meal_plan,
        'is_temp': True,
        'totals': totals,
        'daily_calories': daily_calories,
        'selected_day': selected_day,
        'day_list': day_list,
        'selected_index': day_index,
        'meals_data': meals_data,
    }
    return render(request, 'meals/temp_plan.html', context)


@require_POST
@profile_required
def exclude_permanently(request):
    food_id = int(request.POST.get('food_id'))
    profile = request.user.profile
    excluded = getattr(profile, 'excluded_foods', []) or []
    if food_id not in excluded:
        excluded.append(food_id)
        profile.excluded_foods = excluded
        profile.save()
        # regenerate temp plan
        try:
            meal_engine.generate_temp_meal_plan(request.user)
            messages.success(request, 'Food excluded permanently and plan regenerated')
        except Exception as e:
            messages.error(request, f'Error regenerating plan: {e}')
    return redirect('meals:temp_plan')


@require_POST
@profile_required
def exclude_for_day(request):
    """Exclude a single meal item for its day and replace it with a new pick."""
    meal_item_id = int(request.POST.get('meal_item_id'))
    meal_item = get_object_or_404(MealItem, id=meal_item_id)
    profile = request.user.profile

    # candidate foods for this meal_type
    foods = meal_engine.get_filtered_foods(profile)
    if meal_item.meal_type == 'snack':
        candidates = foods.filter(food_type__in=['drink', 'snack']).exclude(id=meal_item.food_item.id)
    else:
        candidates = foods.exclude(food_type='drink').exclude(id=meal_item.food_item.id)

    # avoid foods used elsewhere same day
    used_ids = list(meal_item.day.meals.values_list('food_item_id', flat=True))
    candidates = candidates.exclude(id__in=used_ids)

    # Recompute daily macro targets and pick replacement by macro similarity
    daily_plan = meal_engine.generate_daily_macro_plan(profile)
    meal_targets = meal_engine.split_macros_into_meals(daily_plan)
    targets = meal_targets.get(meal_item.meal_type)

    if not targets:
        messages.error(request, 'No macro target for this meal type.')
        return redirect('meals:temp_plan')

    picked = meal_engine.pick_food_for_target(candidates, targets, used_ids)

    if not picked:
        messages.error(request, 'No replacement available that matches macros.')
        return redirect('meals:temp_plan')

    replacement_food, replacement_qty = picked[0]

    # replace old item with the picked item and adjusted quantity
    meal_item.delete()
    MealItem.objects.create(
        day=meal_item.day,
        food_item=replacement_food,
        meal_type=meal_item.meal_type,
        quantity=replacement_qty
    )

    messages.success(request, 'Item excluded for day and replaced with a macro-matching option')
    return redirect('meals:temp_plan')


@require_POST
@profile_required
def finalize_plan(request):
    """Finalize the temporary plan to become the user's active plan."""
    try:
        meal_plan = MealPlan.objects.filter(user=request.user, is_finalized=False).latest('created_at')
    except MealPlan.DoesNotExist:
        messages.error(request, 'No temporary plan to finalize')
        return redirect('meals:temp_plan')

    meal_engine.finalize_meal_plan(meal_plan)
    messages.success(request, 'Meal plan finalized')
    return redirect('meals:mealplan')


@profile_required
def mealplan_view(request):
    """Show finalized plan where user can mark meal items as completed."""
    try:
        meal_plan = MealPlan.objects.filter(user=request.user, is_finalized=True).latest('created_at')
    except MealPlan.DoesNotExist:
        # If there's no finalized plan, show the 'no plan' page with option to generate
        return render(request, 'meals/noplan.html')

    # day navigation for finalized plan (show one day at a time)
    day_index = 0
    try:
        day_index = int(request.GET.get('day', 0))
    except (TypeError, ValueError):
        day_index = 0

    days_qs = meal_plan.days.all().order_by('date')
    if days_qs.count() == 0:
        return render(request, 'meals/noplan.html')

    day_index = max(0, min(day_index, max(0, days_qs.count() - 1)))
    selected_day = days_qs[day_index]

    totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    meals_data = []
    for mi in selected_day.meals.all():
        fs = mi.food_item
        qty = float(mi.quantity or 1)
        cals = float(getattr(fs, 'calories_per_serving', 0))
        proteins = float(getattr(fs, 'proteins_per_serving', 0))
        carbs = float(getattr(fs, 'carbs_per_serving', 0))
        fats = float(getattr(fs, 'fats_per_serving', 0))

        item_totals = {
            'id': mi.id,
            'food_id': fs.id,
            'meal_type': mi.get_meal_type_display(),
            'name': fs.name,
            'quantity': qty,
            'cal_per_serv': cals,
            'cal_total': round(cals * qty, 0),
            'protein_per': proteins,
            'protein_total': round(proteins * qty, 1),
            'carbs_per': carbs,
            'carbs_total': round(carbs * qty, 1),
            'fat_per': fats,
            'fat_total': round(fats * qty, 1),
            'food_type': fs.get_food_type_display(),
            'is_completed': mi.is_completed,
        }

        totals['calories'] += item_totals['cal_total']
        totals['protein'] += item_totals['protein_total']
        totals['carbs'] += item_totals['carbs_total']
        totals['fat'] += item_totals['fat_total']

        meals_data.append(item_totals)

    # compute profile daily calories
    daily_info = meal_engine.generate_daily_macro_plan(request.user.profile)
    daily_calories = daily_info.get('calories')

    day_list = [
        {'index': idx, 'name': d.day_name.title(), 'date': d.date}
        for idx, d in enumerate(days_qs)
    ]

    context = {
        'meal_plan': meal_plan,
        'is_temp': False,
        'totals': totals,
        'daily_calories': daily_calories,
        'selected_day': selected_day,
        'day_list': day_list,
        'selected_index': day_index,
        'meals_data': meals_data,
    }
    return render(request, 'meals/mealplan.html', context)


@require_POST
@profile_required
def toggle_item_done(request):
    item_id = int(request.POST.get('item_id'))
    item = get_object_or_404(MealItem, id=item_id, day__meal_plan__user=request.user)
    item.is_completed = not item.is_completed
    item.save()
    return redirect('meals:mealplan')

