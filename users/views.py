from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum

from .models import DealerProfile
from .forms import CustomUserCreationForm, DealerSettingsForm 
from payments.models import MpesaTransaction

User = get_user_model()

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

# --- SUPER ADMIN DASHBOARD ---
@staff_member_required
def admin_dashboard(request):
    # 1. Get Stats
    total_dealers = User.objects.filter(role='DEALER').count()
    total_revenue = MpesaTransaction.objects.filter(status='SUCCESS').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # 2. Get Dealers List (Pending Verification at top)
    dealers = User.objects.filter(role='DEALER').select_related('dealer_profile').order_by('is_verified', '-date_joined')
    
    # 3. Handle Verification Toggle
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        try:
            dealer_to_update = User.objects.get(id=user_id)
            if action == 'verify':
                dealer_to_update.is_verified = True
                messages.success(request, f"Verified {dealer_to_update.username}!")
            elif action == 'unverify':
                dealer_to_update.is_verified = False
                messages.warning(request, f"Unverified {dealer_to_update.username}.")
                
            dealer_to_update.save()
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            
        return redirect('admin_dashboard')

    context = {
        'total_dealers': total_dealers,
        'total_revenue': total_revenue,
        'dealers': dealers
    }
    return render(request, 'dealer/admin_dashboard.html', context)