from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import DealerProfile

User = get_user_model()

# --- SIGNUP FORM (Used in Registration) ---
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number')

# --- SETTINGS FORM: USER INFO (Account Info) ---
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        # Matches the "Account Information" section in your screenshot
        fields = ['username', 'email'] 
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable username so it cannot be edited (Read-Only)
        if 'username' in self.fields:
            self.fields['username'].disabled = True
            self.fields['username'].widget.attrs['class'] = 'form-control bg-light'

# --- SETTINGS FORM: DEALER PROFILE (Business Info) ---
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = DealerProfile
        fields = [
            'business_name', 
            'phone_number', 
            'city', 
            'address',           # NEW
            'google_map_link',   # NEW
            'website_link', 
            'logo'
        ]
        
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. RJ Motorworld'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 0712345678 (WhatsApp)'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            
            # --- New Fields Widgets ---
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 123 Ngong Road, Greenhouse Mall, Suite 4B'}),
            'google_map_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Paste Google Maps Link here'}),
            # --------------------------

            'website_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }