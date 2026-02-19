from django.db import models
from django.contrib.auth.models import User

class FoodItem(models.Model):

    FOOD_TYPE_CHOICES = [
        ('meat', 'Meat'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('dairy', 'Dairy'),
        ('drink', 'Drink'),
        ('fastfood', 'Fast Food'),
    ]

    name = models.CharField(max_length=100)

    # 🔹 Nutrition values PER SERVING
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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Meal Plan"
