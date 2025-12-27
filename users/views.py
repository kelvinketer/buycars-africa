from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DealerProfile
# Added UserUpdateForm to the imports
from .forms import CustomUserCreationForm, DealerProfileForm, UserUpdateForm

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
    # 1. Get or Create the profile so it doesn't crash
    profile, created = DealerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Load both forms with POST data
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = DealerProfileForm(request.POST, request.FILES, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            # Stay on the settings page so they can see the changes
            return redirect('profile_settings') 
    else:
        # Load forms with current database info
        u_form = UserUpdateForm(instance=request.user)
        p_form = DealerProfileForm(instance=profile)
    
    context = {
        'u_form': u_form, 
        'p_form': p_form
    }
    # Make sure your template file is named 'settings.html' inside 'templates/dealer/'
    return render(request, 'dealer/settings.html', context)