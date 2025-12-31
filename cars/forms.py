from django import forms
from .models import Car

# Custom Widget to allow 'multiple' attribute without Django throwing a ValueError
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class CarForm(forms.ModelForm):
    # UPDATED: Use standard FileField for validation safety, but MultipleWidget for UI
    image = forms.FileField(
        required=False, 
        widget=MultipleFileInput(attrs={
            'class': 'form-control', 
            'multiple': True, 
            'accept': 'image/*'
        })
    )

    class Meta:
        model = Car
        # We exclude 'status' here so we don't conflict with model logic, 
        # but we will handle it manually in the view.
        exclude = ['dealer', 'status', 'is_featured', 'created_at']
        
        widgets = {
            'make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Toyota'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Harrier'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2017'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2500000'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'transmission': forms.Select(attrs={'class': 'form-select'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 85000'}),
            'engine_size': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2000'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Pearl White'}),
            'body_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Nairobi, Kiambu Road'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the car...'}),
        }