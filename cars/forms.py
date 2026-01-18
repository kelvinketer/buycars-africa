from django import forms
from django.utils import timezone
from .models import Car, Booking, Message  # Added Message import here

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
        # Exclude internal fields AND the old legacy 'location' field
        exclude = ['dealer', 'status', 'is_featured', 'created_at', 'views', 'leads', 'location']
        
        widgets = {
            # --- NEW GLOBAL FIELDS ---
            'country': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Nairobi, Cape Town, Dubai'}),
            'listing_currency': forms.Select(attrs={'class': 'form-select'}),

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
            
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the car...'}),

            # --- RENTAL FIELDS ---
            # We add IDs here to control them with JavaScript (Show/Hide logic)
            'listing_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_listing_type'}),
            'rent_price_per_day': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 3500', 'id': 'id_rent_price'}),
            'min_hire_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1', 'id': 'id_min_days'}),
            'is_available_for_rent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# --- BOOKING FORM ---
class CarBookingForm(forms.ModelForm):
    class Meta:
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
    
# --- SALE AGREEMENT FORM ---
class SaleAgreementForm(forms.Form):
    # Seller Details
    seller_name = forms.CharField(label="Seller's Full Name", max_length=100)
    seller_id = forms.CharField(label="Seller's ID/Passport No", max_length=50)
    seller_phone = forms.CharField(label="Seller's Phone", max_length=20)
    
    # Buyer Details
    buyer_name = forms.CharField(label="Buyer's Full Name", max_length=100)
    buyer_id = forms.CharField(label="Buyer's ID/Passport No", max_length=50)
    buyer_phone = forms.CharField(label="Buyer's Phone", max_length=20)
    
    # Vehicle Details
    make_model = forms.CharField(label="Vehicle Make & Model", max_length=100, widget=forms.TextInput(attrs={'placeholder': 'e.g. Toyota Fielder'}))
    reg_number = forms.CharField(label="Registration Number", max_length=20, widget=forms.TextInput(attrs={'placeholder': 'KBC 123A'}))
    chassis_number = forms.CharField(label="Chassis / VIN Number", max_length=50)
    engine_number = forms.CharField(label="Engine Number", max_length=50, required=False)
    color = forms.CharField(label="Color", max_length=30)
    
    # Transaction Details
    sale_price = forms.IntegerField(label="Agreed Price (KES)")
    amount_paid = forms.IntegerField(label="Amount Paid Now (KES)")
    balance = forms.IntegerField(label="Balance Remaining (KES)", required=False, initial=0)
    witness_name = forms.CharField(label="Witness Name", max_length=100, required=False)

# --- NEW: SECURE MESSAGING FORM ---
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Hi, is this car still available? I would like to schedule a viewing...'
            })
        }