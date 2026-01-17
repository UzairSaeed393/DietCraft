from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "age",
            "height_cm",
            "weight_kg",
            "activity_level",
            "goal",
            "gender",
            "image",
        ]

        widgets = {
            "age": forms.NumberInput(attrs={"class": "form-control"}),
            "height_cm": forms.NumberInput(attrs={"class": "form-control"}),
            "weight_kg": forms.NumberInput(attrs={"class": "form-control"}),
            "activity_level": forms.Select(attrs={"class": "form-control"}),
            "goal": forms.Select(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        }
