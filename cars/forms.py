from django import forms
from django.utils import timezone
# FIXED: Imported Booking instead of CarBooking
from .models import Car, Booking  

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
        # We exclude fields the dealer shouldn't touch manually
        exclude = ['dealer', 'status', 'is_featured', 'created_at', 'views', 'leads']
        
        widgets = {
            # --- EXISTING FIELDS ---
            'make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Toyota'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Harrier'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2017'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. KDA 123X (Private)'}),
            
            # Note: We add an ID to 'price' so we can hide it if "For Rent" is selected
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2500000', 'id': 'id_selling_price'}),
            
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'transmission': forms.Select(attrs={'class': 'form-select'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 85000'}),
            'engine_size': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2000'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Pearl White'}),
            'body_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Nairobi, Kiambu Road'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the car...'}),

            # --- NEW RENTAL FIELDS ---
            # We add IDs here to control them with JavaScript (Show/Hide logic)
            'listing_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_listing_type'}),
            'rent_price_per_day': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 3500', 'id': 'id_rent_price'}),
            'min_hire_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1', 'id': 'id_min_days'}),
            'is_available_for_rent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# --- NEW: BOOKING FORM ---
class CarBookingForm(forms.ModelForm):
    class Meta:
        # FIXED: Using the new Booking model
        model = Booking
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'startDate'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'endDate'}),
        }

    def clean(self):
        """
        Validates that dates are in the future and end date is after start date.
        """
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end:
            if start < timezone.now().date():
                 raise forms.ValidationError("Start date cannot be in the past.")
            if end <= start:
                raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data