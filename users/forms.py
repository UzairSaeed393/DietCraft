from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'age',
            'height_cm',
            'weight_kg',
            'activity_level',
            'goal',
        ]

        widgets = {
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your age'
            }),
            'height_cm': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Height in cm'
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Weight in kg'
            }),
            'activity_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'goal': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
