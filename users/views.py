from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required # <--- Added
from django.contrib import messages # <--- Added
from .models import DealerProfile # <--- Added
from .forms import CustomUserCreationForm, DealerProfileForm  # <--- Added DealerProfileForm

def signup_view(request):
    if request.method == 'POST':
        # This form now expects username, email, AND phone_number
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Go straight to dashboard to upload their first car
            return redirect('dealer_dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # IMPROVEMENT: If they were trying to go somewhere specific, send them there.
            if 'next' in request.GET:
                return redirect(request.GET.get('next'))
            
            # Otherwise, go to dashboard
            return redirect('dealer_dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

# --- NEW: DEALER PROFILE SETTINGS ---
@login_required
def profile_settings(request):
    # 1. Get or Create the profile for the logged-in user
    # We use get_or_create so it doesn't crash if a profile is missing
    profile, created = DealerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = DealerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile details updated successfully!')
            return redirect('dealer_dashboard')
    else:
        form = DealerProfileForm(instance=profile)
    
    return render(request, 'dealer/profile_settings.html', {'form': form})