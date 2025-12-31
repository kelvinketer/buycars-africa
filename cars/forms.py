from django import forms
from .models import Car

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class IgnoreValidationFileField(forms.FileField):
    def to_python(self, data):
        # We handle files manually in views.py, so we don't need Django 
        # to normalize this data for us.
        return data

    def validate(self, value):
        # SKIP validation entirely for this field to prevent "list" errors
        pass

class CarForm(forms.ModelForm):
    # UPDATED: Use the lenient field class
    image = IgnoreValidationFileField(
        required=False, 
        widget=MultipleFileInput(attrs={
            'class': 'form-control', 
            'multiple': True, 
            'accept': 'image/*'
        })
    )

    class Meta:
        model = Car
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