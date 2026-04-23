import random
from typing import Dict, List, Tuple
from django.db.models import Q
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
    "sedentary": 1.2,
    "light": 1.35,
    "moderate": 1.55,
    "active": 1.75,
    "very_active": 1.9,
    # Backwards-compatible aliases for older profile data.
    "not_active": 1.2,
    "lightly_active": 1.35,
    "moderately_active": 1.55,
}

FITNESS_GOAL_FACTORS = {
    "lose": 0.8,
    "maintain": 1.0,
    "gain": 1.1,
}


def calculate_tdee(bmr: float, activity_level: str) -> float:
    factor = ACTIVITY_LEVEL_FACTORS.get(activity_level, ACTIVITY_LEVEL_FACTORS["moderate"])
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
    while (protein_cal + fat_cal) > calories and fat_g > 0:
        fat_g -= 1
        fat_cal = fat_g * 9

    if (protein_cal + fat_cal) > calories:
        protein_g = max(0, int(calories // 4))
        protein_cal = protein_g * 4
        fat_g = 0
        fat_cal = 0

    # Remaining calories go to carbs
    carb_cal = max(0, calories - (protein_cal + fat_cal))
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


MEAL_QUANTITY_STEP = 0.25
MEAL_MAX_QUANTITY = 6.0


def _meal_suitability_value(food):
    value = getattr(food, 'meal_suitability', 'any') or 'any'
    return str(value).lower()


def _normalized_preferred_food_types(profile):
    preferred = [value for value in (getattr(profile, "preferred_food_types", []) or []) if value]
    if "all" in preferred:
        return []
    return preferred


def _normalized_medical_conditions(profile):
    return [
        value
        for value in (getattr(profile, "medical_conditions", []) or [])
        if value and value != "none"
    ]


def _apply_profile_filters(queryset, preferred_food_types, medical_conditions):
    if preferred_food_types:
        queryset = queryset.filter(food_type__in=preferred_food_types)

    if medical_conditions:
        queryset = queryset.filter(
            Q(medical_tags__medical_tag__code__in=medical_conditions)
            | Q(medical_tags__isnull=True)
        )

    return queryset.distinct()


def _meal_type_foods(foods, meal_type):
    foods = list(foods)

    if meal_type == "snack":
        filtered = [
            food
            for food in foods
            if food.food_type in {"snack", "drink"}
            and _meal_suitability_value(food) == "snack"
        ]
        return filtered

    filtered = [
        food
        for food in foods
        if food.food_type != "drink"
        and _meal_suitability_value(food) in {meal_type, "any"}
    ]

    if filtered:
        return filtered

    return [food for food in foods if food.food_type != "drink"]


def _food_medical_codes(food):
    return {mapping.medical_tag.code for mapping in food.medical_tags.all()}


def _macro_score(food, targets: dict, quantity: float) -> float:
    target_protein = max(float(targets.get("protein_g", 0)), 1.0)
    target_carbs = max(float(targets.get("carbs_g", 0)), 1.0)
    target_fat = max(float(targets.get("fat_g", 0)), 1.0)
    target_calories = max(float(targets.get("calories", 0)), 1.0)

    protein_total = float(getattr(food, "proteins_per_serving", 0)) * quantity
    carbs_total = float(getattr(food, "carbs_per_serving", 0)) * quantity
    fat_total = float(getattr(food, "fats_per_serving", 0)) * quantity
    calories_total = float(getattr(food, "calories_per_serving", 0)) * quantity

    protein_error = abs(protein_total - target_protein) / target_protein
    carbs_error = abs(carbs_total - target_carbs) / target_carbs
    fat_error = abs(fat_total - target_fat) / target_fat
    calorie_error = abs(calories_total - target_calories) / target_calories

    return (
        (protein_error * 4.0)
        + (carbs_error * 2.0)
        + (fat_error * 3.0)
        + (calorie_error * 0.15)
    )


def _meal_suitability_score(food, meal_type: str) -> float:
    suitability = _meal_suitability_value(food)

    if meal_type == "snack":
        if suitability == "snack":
            return -0.35
        return 0.0

    if suitability == meal_type:
        return -0.4

    if suitability == "any":
        return 0.08

    return 0.25

# FOOD FILTERING 

def get_filtered_foods(profile):
    """
    Remove permanently excluded foods and apply profile preferences.
    """
    excluded = [food_id for food_id in (getattr(profile, "excluded_foods", []) or []) if food_id]
    preferred_food_types = _normalized_preferred_food_types(profile)
    medical_conditions = _normalized_medical_conditions(profile)

    base = FoodItem.objects.exclude(id__in=excluded).prefetch_related("medical_tags__medical_tag")

    attempts = []

    if preferred_food_types and medical_conditions:
        attempts.append(_apply_profile_filters(base, preferred_food_types, medical_conditions))

    if preferred_food_types:
        attempts.append(_apply_profile_filters(base, preferred_food_types, []))

    if medical_conditions:
        attempts.append(_apply_profile_filters(base, [], medical_conditions))

    attempts.append(base)

    for queryset in attempts:
        if queryset.exists():
            return queryset

    return base.none()

#  FOOD PICKER WITH VARIETY + FALLBACK 

def pick_food_for_target(
    foods,
    targets: dict,
    used_ids_today: List[int],
    weekly_usage: Dict[int, int],
    exclude_food_ids: List[int] | None = None,
    meal_type: str | None = None,
    profile=None,
) -> List[Tuple[FoodItem, float]]:
    """
    Select food closest to macro target.
    Macro match is the primary signal, while calories and repetition are only tie-breakers.
    """
    food_pool = list(foods)
    used_ids = set(used_ids_today or [])
    excluded_ids = set(exclude_food_ids or [])
    available_foods = [
        food for food in food_pool
        if food.id not in used_ids and food.id not in excluded_ids
    ]
    meal_foods = _meal_type_foods(available_foods, meal_type)

    if not meal_foods:
        meal_foods = available_foods

    if not meal_foods:
        return []

    preferred_food_types = set(_normalized_preferred_food_types(profile))
    medical_conditions = set(_normalized_medical_conditions(profile))

    scored_foods = []
    for food in meal_foods:
        weekly_count = weekly_usage.get(food.id, 0)
        food_medical_codes = _food_medical_codes(food) if medical_conditions else set()
        scored_foods.append((food, weekly_count, food_medical_codes))

    best_choice = None
    quantity = MEAL_QUANTITY_STEP

    while quantity <= MEAL_MAX_QUANTITY:
        for food, weekly_count, food_medical_codes in scored_foods:
            score = _macro_score(food, targets, quantity)

            score += _meal_suitability_score(food, meal_type or "")

            calories_per_serving = float(getattr(food, "calories_per_serving", 0))
            if calories_per_serving > 0:
                ideal_quantity = float(targets.get("calories", 0)) / calories_per_serving
                score += abs(quantity - ideal_quantity) * 0.03

            score += weekly_count * 0.35
            score += random.uniform(0, 0.02)

            if preferred_food_types:
                if food.food_type in preferred_food_types:
                    score -= 0.25
                else:
                    score += 0.35

            if medical_conditions:
                if food_medical_codes:
                    if food_medical_codes & medical_conditions:
                        score -= 0.2
                    else:
                        score += 0.4

            if best_choice is None or score < best_choice[0]:
                best_choice = (score, food, round(quantity, 2))

        quantity = round(quantity + MEAL_QUANTITY_STEP, 2)

    if best_choice:
        return [(best_choice[1], best_choice[2])]

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

    foods = list(get_filtered_foods(profile))
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
            day_name=current_date.strftime("%A").lower()  # matches stored choices
        )
        used_today = []

        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:

            picked = pick_food_for_target(
                foods,
                meal_targets[meal_type],
                used_today,
                weekly_usage,
                meal_type=meal_type,
                profile=profile,
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