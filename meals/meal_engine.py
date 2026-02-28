import random
from datetime import timedelta
from django.utils import timezone
from .models import MealPlan, MealPlanDay, MealItem, FoodItem


#CONSTANTS 

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

BMR_CONSTANTS = {
    "male":   {"base": 88.36,  "weight": 13.397, "height": 4.799, "age": 5.677},
    "female": {"base": 447.6,  "weight": 9.247,  "height": 3.098, "age": 4.330},
    "other":  {"base": 400.0,  "weight": 11.0,   "height": 4.0,   "age": 5.0},
}

MEAL_SPLIT = {
    "breakfast": 0.27,
    "lunch": 0.35,
    "snack": 0.11,
    "dinner": 0.27,
}


# CORE LOGIC (Calorie and Macro Calculations)

def calculate_bmr(weight_kg, height_cm, age, gender):
    gender = gender.lower()
    constants = BMR_CONSTANTS.get(gender, BMR_CONSTANTS["other"])

    return (
        constants["base"]+ (constants["weight"] * weight_kg)+ (constants["height"] * height_cm)- (constants["age"] * age)
    )


def calculate_tdee(bmr, activity_level):
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)
    return bmr * multiplier


def adjust_calories_for_goal(tdee, goal):
    goal = goal.lower()

    if goal == "lose":
        return tdee * 0.80
    elif goal == "gain":
        return tdee * 1.15
    else:
        return tdee


# ADVANCED MACROS APPROACH CALULATION

def calculate_macros(calories: float, weight_kg: float, height_cm: float, gender: str) -> dict:

    calories = float(calories)
    weight_kg = float(weight_kg)
    height_cm = float(height_cm)

    BMI_REF = 22.5
    ref_wt = BMI_REF * (height_cm / 100) ** 2

    protein_factor = 2.0
    fat_factor = 0.8

    min_protein_factor = 1.6
    min_fat_factor = 0.6

    protein_g = round(ref_wt * protein_factor)
    fat_g = round(ref_wt * fat_factor)

    protein_cals = protein_g * 4
    fat_cals = fat_g * 9
    total_pf_cals = protein_cals + fat_cals

    min_protein_g = round(ref_wt * min_protein_factor)
    min_fat_g = round(ref_wt * min_fat_factor)

    while total_pf_cals > calories and fat_g > min_fat_g:
        fat_g -= 1
        fat_cals = fat_g * 9
        total_pf_cals = (protein_g * 4) + fat_cals

    while total_pf_cals > calories and protein_g > min_protein_g:
        protein_g -= 1
        protein_cals = protein_g * 4
        total_pf_cals = protein_cals + (fat_g * 9)

    if total_pf_cals > calories:
        raise ValueError("Calories too low to fit minimum protein and fat.")

    carb_cals = calories - total_pf_cals
    carbs_g = max(0, round(carb_cals / 4))

    return {
        "protein_g": int(protein_g),
        "fat_g": int(fat_g),
        "carbs_g": int(carbs_g),
    }


#  DAILY MACRO GENERATOR

def generate_daily_macro_plan(profile):

    bmr = calculate_bmr(
        profile.weight_kg,
        profile.height_cm,
        profile.age,
        profile.gender,
    )

    tdee = calculate_tdee(bmr, profile.activity_level)

    goal_calories = adjust_calories_for_goal(tdee, profile.goal)
    
    macros = calculate_macros(
        calories=goal_calories,
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        gender=profile.gender
    )

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "calories": round(goal_calories),
        **macros,
    }


#  SPLIT INTO 4 MEALS

def split_macros_into_meals(daily_plan):

    meals = {}

    for meal, ratio in MEAL_SPLIT.items():
        meals[meal] = {
            "calories": round(daily_plan["calories"] * ratio),
            "protein_g": round(daily_plan["protein_g"] * ratio),
            "fat_g": round(daily_plan["fat_g"] * ratio),
            "carbs_g": round(daily_plan["carbs_g"] * ratio),
        }

    return meals


# FILTER FOODS

def get_filtered_foods(profile, excluded_food_ids=None):

    if excluded_food_ids is None:
        excluded_food_ids = []

    foods = FoodItem.objects.all()

    if profile.preferred_food_types:
        foods = foods.filter(food_type__in=profile.preferred_food_types)

    if profile.medical_conditions and "none" not in profile.medical_conditions:
        foods = foods.exclude(
            medical_tags__medical_tag__code__in=profile.medical_conditions
        )

    # Include any permanently excluded foods from the user's profile
    profile_excluded = getattr(profile, 'excluded_foods', []) or []
    all_excludes = set(excluded_food_ids) | set(profile_excluded)

    if all_excludes:
        foods = foods.exclude(id__in=list(all_excludes))

    return foods.distinct()


#CALORIE TOLERANCE MATCHING (±5%)

def get_foods_within_tolerance(foods, target_calories, tolerance=0.05):

    min_cal = target_calories * (1 - tolerance)
    max_cal = target_calories * (1 + tolerance)

    return foods.filter(
        calories_per_serving__gte=min_cal,
        calories_per_serving__lte=max_cal
    )


#  SMART PICK WITH VARIETY (NO REPEAT SAME DAY + PORTION ADJUSTMENT)

def pick_food_for_target(foods, targets, used_food_ids_today):

    foods = foods.exclude(id__in=used_food_ids_today)

    if not foods.exists():
        return []

    selected_items = []

    remaining_protein = targets["protein_g"]
    remaining_carbs = targets["carbs_g"]
    remaining_fat = targets["fat_g"]
    remaining_calories = targets["calories"]

    foods_list = list(foods)

    for _ in range(3):

        if remaining_calories <= 50:
            break

        def macro_distance(food):
            return (
                abs(food.protein_g - remaining_protein) * 4 +
                abs(food.carbs_g - remaining_carbs) * 4 +
                abs(food.fat_g - remaining_fat) * 9
            )

        best_food = min(foods_list, key=macro_distance)

        if best_food.calories_per_serving > 0:
            quantity = remaining_calories / best_food.calories_per_serving
        else:
            quantity = 1

        if quantity < 0.5:
            quantity = 0.5
        elif quantity > 2:
            quantity = 2
        else:
            quantity = round(quantity, 1)

        selected_items.append((best_food, quantity))
        used_food_ids_today.append(best_food.id)

        remaining_protein -= best_food.protein_g * quantity
        remaining_carbs -= best_food.carbs_g * quantity
        remaining_fat -= best_food.fat_g * quantity
        remaining_calories -= best_food.calories_per_serving * quantity

        foods_list = [f for f in foods_list if f.id != best_food.id]

        if not foods_list:
            break

    return selected_items


#  GENERATE TEMP WEEKLY PLAN 

def generate_temp_meal_plan(user, excluded_food_ids=None):

    profile = user.profile

    MealPlan.objects.filter(user=user, is_finalized=False).delete()

    meal_plan = MealPlan.objects.create(
        user=user,
        week_start=timezone.now().date(),
        is_finalized=False
    )

    daily_plan = generate_daily_macro_plan(profile)
    meal_targets = split_macros_into_meals(daily_plan)

    foods = get_filtered_foods(profile, excluded_food_ids)

    if not foods.exists():
        raise ValueError("No foods available after filtering.")

    for i in range(7):

        day_date = meal_plan.week_start + timedelta(days=i)

        day_obj = MealPlanDay.objects.create(
            meal_plan=meal_plan,
            day_name=day_date.strftime("%A").lower(),
            date=day_date
        )

        used_food_ids_today = []

        for meal_type, targets in meal_targets.items():

            if meal_type == "snack":
                meal_foods = foods.filter(food_type__in=["drink", "snack"])
            else:
                meal_foods = foods.exclude(food_type="drink")

            selected_items = pick_food_for_target(
                meal_foods,
                targets,
                used_food_ids_today
            )

            for selected_food, quantity in selected_items:
                MealItem.objects.create(
                    day=day_obj,
                    food_item=selected_food,
                    meal_type=meal_type,
                    quantity=quantity
                )

    return meal_plan


#  FINALIZE PLAN

def finalize_meal_plan(meal_plan):
    meal_plan.is_finalized = True
    meal_plan.save()