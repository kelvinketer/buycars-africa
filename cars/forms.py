from django import forms
from .models import Car

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            'make', 'model', 'year', 'price', 
            'condition', 'transmission', 'fuel_type', 
            'mileage', 'engine_size', 'color', 
            'body_type', 'location', 'description', 
            'image' # Assuming you have a main image field, or we handle multiple images separately
        ]
        
        # This makes the form look professional (Bootstrap classes)
        widgets = {
            'make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Toyota'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Prado TX-L'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2018'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price in KES'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'transmission': forms.Select(attrs={'class': 'form-select'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 65000'}),
            'engine_size': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2700'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'body_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Nairobi, Mombasa'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the car features...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }