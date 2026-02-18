from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    
    preferred_food_types = forms.MultipleChoiceField(
        choices=UserProfile.FOOD_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True  # 🔥 NOW REQUIRED
    )

    medical_conditions = forms.MultipleChoiceField(
        choices=UserProfile.MEDICAL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True  # 🔥 NOW REQUIRED
    )

    class Meta:
        model = UserProfile
        fields = [
            "age",
            "height_cm",
            "weight_kg",
            "activity_level",
            "goal",
            "gender",
            "preferred_food_types",
            "medical_conditions",
            "image",
        ]

    # VALIDATION: Food preference must not be empty
    def clean_preferred_food_types(self):
        data = self.cleaned_data.get("preferred_food_types")
        if not data:
            raise forms.ValidationError("Please select at least one food preference.")
        return data

    #  Medical must not be empty
    def clean_medical_conditions(self):
        data = self.cleaned_data.get("medical_conditions")
        if not data:
            raise forms.ValidationError("Please select at least one medical condition (or None).")
        return data

    # Extra rule: if 'none' selected, it must be alone
    def clean(self):
        cleaned_data = super().clean()
        medical = cleaned_data.get("medical_conditions")

        if medical:
            if "none" in medical and len(medical) > 1:
                raise forms.ValidationError(
                    "If 'None' is selected, no other medical condition can be selected."
                )

        return cleaned_data
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
            "preferred_food_types",
            "medical_conditions",
        ]

        widgets = {
            "age": forms.NumberInput(attrs={"class": "form-control"}),
            "height_cm": forms.NumberInput(attrs={"class": "form-control"}),
            "weight_kg": forms.NumberInput(attrs={"class": "form-control"}),
            "activity_level": forms.Select(attrs={"class": "form-control"}),
            "goal": forms.Select(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
            "preferred_food_types": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "medical_conditions": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            
        }
