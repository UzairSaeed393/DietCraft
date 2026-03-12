import random
from typing import Dict, List, Tuple
from django.utils import timezone
from .models import MealPlan, MealItem, FoodItem, MealPlanDay

#BMR CALCULATION 
#To calculate the calories user need to stay alive
def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """
    Mifflin-St Jeor Equation
    """
    weight_kg = float(weight_kg)
    height_cm = float(height_cm)
    age = float(age)

    gender = gender.lower()

    if gender == "male":
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    elif gender == "female":
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        raise ValueError("Gender must be male or female")


#  TDEE CALCULATION 
ACTIVITY_LEVEL_FACTORS = {
    "not_active": 1.2,
    "lightly_active": 1.35,
    "moderately_active": 1.55,
    "active": 1.75,
    "very_active": 1.9,
}

FITNESS_GOAL_FACTORS = {
    "lose": 0.8,
    "maintain": 1.0,
    "gain": 1.1,
}


def calculate_tdee(bmr: float, activity_level: str) -> float:
    factor = ACTIVITY_LEVEL_FACTORS.get(activity_level, 1.55)
    return bmr * factor


def adjust_calories_for_goal(tdee: float, goal: str) -> float:
    factor = FITNESS_GOAL_FACTORS.get(goal, 1.0)
    return tdee * factor

#  MACRO CALCULATION 

def calculate_macros(calories: float, height_cm: float) -> dict:
    """
    Reference-weight based macro system
    Ensures macros always fit calorie target
    """
   # Reference weight based on ideal BMI midpoint
    BMI_REF = 22.5
    ref_weight = BMI_REF * (height_cm / 100) ** 2
    # Calculate initial macros based on reference weight
    protein_g = round(ref_weight * 2.0)
    fat_g = round(ref_weight * 0.8)
    # Calculate calories from protein and fat
    protein_cal = protein_g * 4
    fat_cal = fat_g * 9

    # Adjust if exceeds calories
    while (protein_cal + fat_cal) > calories:
        fat_g -= 1
        fat_cal = fat_g * 9
    # Remaining calories go to carbs
    carb_cal = calories - (protein_cal + fat_cal)
    carbs_g = round(carb_cal / 4)

    return {
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g,
    }


def generate_daily_macro_plan(profile) -> dict:
    """
    Returns daily calories + macros
    Accepts UserProfile instance
    """

    bmr = calculate_bmr(
        profile.weight_kg,
        profile.height_cm,
        profile.age,
        profile.gender,
    )

    tdee = calculate_tdee(bmr, profile.activity_level)
    calories = adjust_calories_for_goal(tdee, profile.goal)
    macros = calculate_macros(calories, profile.height_cm)

    return {
        "calories": round(calories),
        **macros
    }

# SPLIT DAILY MACROS INTO 4 MEALS
def split_macros_into_meals(daily_plan: dict) -> dict:
    """
    Split daily macros into 4 meals.
    FIX: ensures minimum calories so picker never fails.
    """

    calories = daily_plan["calories"]
    protein = daily_plan["protein_g"]
    carbs = daily_plan["carbs_g"]
    fat = daily_plan["fat_g"]

    ratios = {
        "breakfast": 0.30,
        "lunch": 0.35,
        "dinner": 0.25,
        "snack": 0.10,
    }

    MIN_MEAL_CALORIES = 250

    meals = {}
# Ensure each meal has at least MIN_MEAL_CALORIES, adjust macros proportionally
    for meal, r in ratios.items():
        meal_cal = max(calories * r, MIN_MEAL_CALORIES)
        factor = meal_cal / calories

        meals[meal] = {
            "calories": meal_cal,
            "protein_g": protein * factor,
            "carbs_g": carbs * factor,
            "fat_g": fat * factor,
        }

    return meals

# FOOD FILTERING 

def get_filtered_foods(profile):
    """
    Remove permanently excluded foods
    """
    excluded = getattr(profile, "excluded_foods", []) or []
    return FoodItem.objects.exclude(id__in=excluded)

#  FOOD PICKER WITH VARIETY + FALLBACK 

def pick_food_for_target(
    foods,
    targets: dict,
    used_ids_today: List[int],
    weekly_usage: Dict[int, int],
) -> List[Tuple[FoodItem, float]]:
    """
    Select food closest to macro target.
    FIXES:
    ✔ weekly variety
    ✔ randomness
    ✔ fallback if strict match fails
    """

    target_cal = targets["calories"]

    candidates = []

    for food in foods:
        if food.id in used_ids_today:
            continue

        cal = float(getattr(food, "calories_per_serving", 0))

        # score by calorie difference
        score = abs(cal - target_cal)

        # weekly repetition penalty
        weekly_count = weekly_usage.get(food.id, 0)
        score += weekly_count * 50

        # small randomness
        score += random.uniform(0, 10)

        candidates.append((score, food))

    if candidates:
        candidates.sort(key=lambda x: x[0])
        best = candidates[0][1]
        return [(best, 1)]

    # fallback → closest calorie food
    fallback = []
    for food in foods:
        cal = float(getattr(food, "calories_per_serving", 0))
        diff = abs(cal - target_cal)
        fallback.append((diff, food))

    if fallback:
        fallback.sort(key=lambda x: x[0])
        return [(fallback[0][1], 1)]

    return []

# TEMP MEAL PLAN GENERATION
def generate_temp_meal_plan(user):
    """
    Generate 7-day preview plan.
    FIX: ensures 4 meals per day + weekly variety
    """

    profile = user.profile

    # delete old temp plans
    MealPlan.objects.filter(user=user, is_finalized=False).delete()

    meal_plan = MealPlan.objects.create(
        user=user,
        is_finalized=False
    )

    foods = get_filtered_foods(profile)
    daily_plan = generate_daily_macro_plan(profile)
    meal_targets = split_macros_into_meals(daily_plan)

    weekly_usage = {}

    # for i in range(7):
    #     day = MealPlanDay.objects.create(
    #         meal_plan=meal_plan,
    #         date=timezone.now().date() + timezone.timedelta(days=i),
    #         day_name=timezone.now().strftime("%A")
    #     )
    start_date = timezone.now().date()

    for i in range(7):
        current_date = start_date + timezone.timedelta(days=i)

        day = MealPlanDay.objects.create(
            meal_plan=meal_plan,
            date=current_date,
            day_name=current_date.strftime("%A")  # correct weekday
        )
        used_today = []

        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:

            picked = pick_food_for_target(
                foods,
                meal_targets[meal_type],
                used_today,
                weekly_usage
            )

            if not picked:
                continue

            food, qty = picked[0]

            MealItem.objects.create(
                day=day,
                food_item=food,
                meal_type=meal_type,
                quantity=qty
            )

            used_today.append(food.id)
            weekly_usage[food.id] = weekly_usage.get(food.id, 0) + 1

    return meal_plan

# FINALIZE PLAN 
def finalize_meal_plan(meal_plan):
    """
    Convert temp plan into active plan
    """
    # Set as finalized and record week_start from earliest day date
    days = meal_plan.days.order_by("date")
    if days.exists():
        meal_plan.week_start = days.first().date

    meal_plan.is_finalized = True
    meal_plan.save()