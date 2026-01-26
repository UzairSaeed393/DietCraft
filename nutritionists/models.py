from django.db import models

class Nutritionist(models.Model):
    CATEGORY_CHOICES = [
        ("sports", "Sports Nutrition"),
        ("weight", "Weight Management"),
        ("pediatric", "Pediatric Nutrition"),
        ("clinical", "Clinical Nutrition"),
        ("general", "General Nutrition"),
    ]

    name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=200)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="general"
    )

    clinic_name = models.CharField(max_length=200)
    clinic_address = models.CharField(max_length=300)
    city = models.CharField(
        max_length=20,
        help_text="e.g. Lahore, Gujrat, Islamabad"
    )
    experience_years = models.PositiveIntegerField(default=1)

    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=3.5
    )

    timing = models.CharField(
        max_length=50,
        help_text="e.g. 1:00 PM – 3:00 PM"
    )

    degrees = models.CharField(
        max_length=200,
        help_text="Comma separated e.g: MBBS, RD, MSc Nutrition"
    )

    image = models.ImageField(
        upload_to="nutritionists/",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name
