from django import forms
from .models import Car

# --- CUSTOM WIDGET TO ALLOW MULTIPLE SELECTIONS ---
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# --- CUSTOM FIELD TO VALIDATE A LIST OF FILES ---
class MultipleFileField(forms.FileField):
    def to_python(self, data):
        if not data:
            return None
        if not isinstance(data, list):
            data = [data]
        return data

class CarForm(forms.ModelForm):
    # UPDATED: Use the custom field and widget
    image = MultipleFileField(
        required=False, 
        widget=MultipleFileInput(attrs={
            'class': 'form-control', 
            'multiple': True,  # HTML5 attribute
            'accept': 'image/*' 
        })
    )

    class Meta:
        model = Car
        # Remove 'image' from fields list to avoid conflicts
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