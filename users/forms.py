from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import DealerProfile  # <--- Import the DealerProfile model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number') 

# --- NEW: DEALER PROFILE FORM ---
class DealerProfileForm(forms.ModelForm):
    class Meta:
        model = DealerProfile
        fields = ['business_name', 'logo', 'city', 'physical_address', 'website_link']
        widgets = {
            'physical_address': forms.Textarea(attrs={'rows': 3}),
        }