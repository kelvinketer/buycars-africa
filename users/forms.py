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

# --- SETTINGS FORM: USER INFO (For Basic Account Info) ---
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2547... (For Login/WhatsApp)'}),
        }

# --- SETTINGS FORM: DEALER PROFILE (For Business Info & M-Pesa) ---
class DealerSettingsForm(forms.ModelForm):
    class Meta:
        model = DealerProfile
        # Added 'phone_number' here so the M-Pesa number can be saved
        fields = ['business_name', 'phone_number', 'city', 'physical_address', 'website_link', 'logo']
        
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mombasa Motors'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0712345678 (For M-Pesa Payments)'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'physical_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., Along Mombasa Road...'}),
            'website_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }