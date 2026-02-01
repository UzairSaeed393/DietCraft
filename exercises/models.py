from django.db import models
from django.contrib.auth.models import User
from users.models import UserProfile
from urllib.parse import urlparse, parse_qs

# Create your models here.

#Exercise Model storing details about different exercises we offer.
class Exercise(models.Model):
    CATEGORY_CHOICES = [
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('maintenance', 'Maintenance'),
    ]

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    met_value = models.FloatField()
    duration_minutes = models.PositiveIntegerField()
    video_url = models.URLField(blank=True, null=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def get_embed_url(self):
        """
        Converts any YouTube URL into a safe embed URL
        """
        if not self.video_url:
            return None

        parsed = urlparse(self.video_url)
        video_id = None

        if "youtube.com" in parsed.netloc:
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif "youtu.be" in parsed.netloc:
            video_id = parsed.path.lstrip("/")
        elif "youtube-nocookie.com" in parsed.netloc:
            return self.video_url  # already embed

        if video_id:
            return f"https://www.youtube-nocookie.com/embed/{video_id}"

        return None

    def __str__(self):
        return self.name

#ExercisePlan Model storing details about exercise plans assigned to users for a week.
class ExercisePlan(models.Model):
    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='exercise_plans'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Exercise Plan - {self.profile.user.username}"
    
# ExercisePlanDay Model storing details about daily exercises in an exercise plan.
class ExercisePlanDay(models.Model):
    exercise_plan = models.ForeignKey(
        ExercisePlan,
        on_delete=models.CASCADE,
        related_name='daily_exercises'
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE
    )
    day_number = models.PositiveSmallIntegerField()
    order_number = models.PositiveSmallIntegerField() # Order of the exercise in the day's routine.
    estimated_calories = models.FloatField()
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['day_number', 'order_number']
        unique_together = ('exercise_plan', 'day_number', 'order_number')

    def __str__(self):
        return f"Day {self.day_number} - {self.exercise.name}"
