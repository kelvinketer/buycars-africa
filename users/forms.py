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

# --- SETTINGS FORM: USER INFO (New) ---
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2547... (For WhatsApp)'}),
        }

# --- SETTINGS FORM: DEALER PROFILE (Updated with Styles) ---
class DealerProfileForm(forms.ModelForm):
    class Meta:
        model = DealerProfile
        fields = ['business_name', 'logo', 'city', 'physical_address', 'website_link']
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'physical_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'website_link': forms.URLInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }