from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    GOAL_CHOICES = [
        ('lose', 'Lose Weight'),
        ('maintain', 'Maintain Weight'),
        ('gain', 'Gain Weight'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sedentary'),
        ('light', 'Lightly Active'),
        ('moderate', 'Moderately Active'),
        ('active', 'Active'),
        ('very_active', 'Very Active'),
    ]

    FOOD_TYPE_CHOICES = [
         ('all', 'All'),
        ('meat', 'Meat'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('dairy', 'Dairy'),
        ('drink', 'Drink'),
        ('fastfood', 'Fast Food'),
    ]

    MEDICAL_CHOICES = [
        ('diabetes', 'Diabetes'),
        ('hypertension', 'Hypertension'),
        ('lactose', 'Lactose Intolerant'),
        ('heart', 'Heart Disease'),
        ('none', 'None'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='profile')

    age = models.PositiveIntegerField()
    height_cm = models.FloatField(help_text="Height in centimeters")
    weight_kg = models.FloatField(help_text="Weight in kilograms")
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )
    activity_level = models.CharField(
        max_length=20,
        choices=ACTIVITY_LEVEL_CHOICES
    )

    preferred_food_types = models.JSONField(
        default=list,
        help_text="Allowed food categories"
    )

    medical_conditions = models.JSONField(
        default=list,
        help_text="Medical conditions"
    )
    
    image = models.ImageField(
        upload_to="profiles/",
        null=True,
        blank=True
    )
    
    goal = models.CharField(
        max_length=20,
        choices=GOAL_CHOICES
    )

    def __str__(self):
        return f"{self.user.username} Profile"
