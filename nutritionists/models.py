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
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")

    phone = models.CharField(max_length=20)
    email = models.EmailField()
    clinic_name = models.CharField(max_length=200)
    clinic_address = models.CharField(max_length=300)

    experience_years = models.IntegerField(default=1)
    degrees = models.CharField(max_length=200, help_text="Comma separated e.g: MBBS, RD, PhD")
    image = models.ImageField(
    upload_to="nutritionists/",
    null=True,     
    blank=True         
)

    def __str__(self):
        return self.name
