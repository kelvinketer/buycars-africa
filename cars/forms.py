from django import forms
from .models import Car

class CarForm(forms.ModelForm):
    # We define 'image' here manually because it is NOT part of the Car model directly.
    # This allows the form to still show the file upload button.
    image = forms.ImageField(
        required=False, 
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Car
        # 'image' is REMOVED from this list to prevent the "Unknown field" error
        fields = [
            'make', 'model', 'year', 'price', 
            'condition', 'transmission', 'fuel_type', 
            'mileage', 'engine_size', 'color', 
            'body_type', 'location', 'description'
        ]
        
        # Professional Styling (Bootstrap)
        widgets = {
            'make': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Toyota'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Harrier'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. 2017'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. 2500000'
            }),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'transmission': forms.Select(attrs={'class': 'form-select'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'mileage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. 85000'
            }),
            'engine_size': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. 2000'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Pearl White'
            }),
            'body_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Nairobi, Kiambu Road'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Describe the car... (e.g. Clean interior, one owner, buy and drive)'
            }),
        }