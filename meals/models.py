from datetime import date, timedelta

from django.db import models
from django.contrib.auth.models import User

class FoodItem(models.Model):

    FOOD_TYPE_CHOICES = [
        ('meat', 'Meat'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('dairy', 'Dairy'),
        ('drink', 'Drink'),
        ('snack', 'Snack'),
        ('fastfood', 'Fast Food'),
    ]

    name = models.CharField(max_length=100)

    #  Nutrition values PER SERVING
    calories_per_serving = models.PositiveIntegerField(
        help_text="Calories per serving"
    )
    carbs_per_serving = models.FloatField(
        help_text="Carbohydrates (g) per serving"
    )
    proteins_per_serving = models.FloatField(
        help_text="Protein (g) per serving"
    )
    fats_per_serving = models.FloatField(
        help_text="Fat (g) per serving"
    )

    food_type = models.CharField(
        max_length=20,
        choices=FOOD_TYPE_CHOICES
    )

    def __str__(self):
        return self.name
    
    @property
    def protein_g(self):
        return self.proteins_per_serving

    @property
    def carbs_g(self):
        return self.carbs_per_serving

    @property
    def fat_g(self):
        return self.fats_per_serving
   
class MedicalTag(models.Model):

    MEDICAL_CODE_CHOICES = [
        ('diabetes', 'Diabetes'),
        ('hypertension', 'Hypertension'),
        ('lactose', 'Lactose Intolerant'),
        ('heart', 'Heart Disease'),
        ('none', 'None'),
    ]

    code = models.CharField(
        max_length=20,
        choices=MEDICAL_CODE_CHOICES,
        unique=True
    )

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class FoodMedicalTag(models.Model):

    food = models.ForeignKey(
        FoodItem,
        on_delete=models.CASCADE,
        related_name="medical_tags"
    )

    medical_tag = models.ForeignKey(
        MedicalTag,
        on_delete=models.CASCADE,
        related_name="foods"
    )

    class Meta:
        unique_together = ('food', 'medical_tag')
        verbose_name = "Food Medical Tag"
        verbose_name_plural = "Food Medical Tags"

    def __str__(self):
        return f"{self.food.name} → {self.medical_tag.name}"
    
class MealPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    week_start = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    is_finalized = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Week Plan ({self.week_start})"
    
class MealPlanDay(models.Model):

    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    meal_plan = models.ForeignKey(MealPlan,on_delete=models.CASCADE,related_name="days")
    day_name = models.CharField(max_length=20,choices=DAY_CHOICES)
    date = models.DateField()

    def __str__(self):
        return f"{self.meal_plan.user.username} - {self.day_name}"
    
class MealItem(models.Model):

    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('snack', 'Snack'),
        ('dinner', 'Dinner'),
    ]

    day = models.ForeignKey(
        MealPlanDay,
        on_delete=models.CASCADE,
        related_name="meals"
    )

    food_item = models.ForeignKey(
        FoodItem,
        on_delete=models.CASCADE
    )

    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_TYPE_CHOICES
    )

    quantity = models.FloatField(default=1)

    is_completed = models.BooleanField(default=False)
    is_removed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.food_item.name} - {self.meal_type}"