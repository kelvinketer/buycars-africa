from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DealerProfile
# --- UPDATED IMPORTS: Import the new DealerSettingsForm ---
from .forms import CustomUserCreationForm, DealerSettingsForm 

def signup_view(request):
    if request.method == 'POST':
        # Expects username, email, phone_number
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a Dealer Profile immediately so they have one
            DealerProfile.objects.create(user=user, business_name=f"{user.username}'s Yard")
            
            login(request, user)
            # Go straight to dashboard to upload their first car
            return redirect('dealer_dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'auth/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # If they were trying to go somewhere specific, send them there.
            if 'next' in request.GET:
                return redirect(request.GET.get('next'))
            
            # Otherwise, go to dashboard
            return redirect('dealer_dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home')

# --- DEALER PROFILE SETTINGS ---
@login_required
def profile_settings(request):
    # 1. Get or Create the profile so it doesn't crash
    profile, created = DealerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Load the new DealerSettingsForm (Business Info + M-Pesa Number)
        form = DealerSettingsForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, 'Your business settings have been saved!')
            return redirect('profile_settings') 
    else:
        # Load form with current database info
        form = DealerSettingsForm(instance=profile)
    
    # Pass 'form' to the template (matches the settings.html we created)
    return render(request, 'dealer/settings.html', {'form': form})

# --- DEALER SUPPORT CENTER ---
@login_required
def support_view(request):
    return render(request, 'dealer/support.html')