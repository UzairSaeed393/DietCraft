from exercises.models import ExercisePlan
from meals.models import MealPlan


def delete_user_plans(user):
    meal_deleted, _ = MealPlan.objects.filter(user=user).delete()
    exercise_deleted, _ = ExercisePlan.objects.filter(profile__user=user).delete()
    return meal_deleted, exercise_deleted
