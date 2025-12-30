from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum

from .models import DealerProfile
from .forms import CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm 
from payments.models import MpesaTransaction
from cars.models import Car 

User = get_user_model()

# --- AUTHENTICATION VIEWS ---

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            DealerProfile.objects.create(user=user, business_name=f"{user.username}'s Yard")
            login(request, user)
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
            if 'next' in request.GET:
                return redirect(request.GET.get('next'))
            if user.is_superuser:
                return redirect('admin_dashboard')
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
    profile, created = DealerProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your business profile has been updated!')
            return redirect('profile_settings') 
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)
    context = {'u_form': u_form, 'p_form': p_form}
    return render(request, 'dealer/settings.html', context)

@login_required
def support_view(request):
    return render(request, 'dealer/support.html')

# ==========================================
#      SUPER ADMIN / CEO DASHBOARD
# ==========================================

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    # 1. FINANCIALS
    total_revenue = MpesaTransaction.objects.filter(status='SUCCESS').aggregate(Sum('amount'))['amount__sum'] or 0

    # 2. USERS & DEALERS
    total_users = User.objects.count()
    
    # 3. INVENTORY HEALTH
    total_cars = Car.objects.count()
    
    # 4. PENDING ACTIONS
    pending_dealers = User.objects.filter(role='DEALER', is_verified=False).count()

    # 5. RECENT ACTIVITY
    recent_users = User.objects.select_related('dealer_profile').order_by('-date_joined')[:5]
    recent_cars = Car.objects.select_related('dealer').order_by('-created_at')[:5]

    # 6. TRANSACTION HISTORY (NEW FEATURE)
    # We fetch the last 10 transactions, ordered by newest first (using 'id' as a proxy for time if created_at is missing)
    recent_transactions = MpesaTransaction.objects.order_by('-id')[:10]

    context = {
        'total_revenue': total_revenue,
        'total_users': total_users,
        'total_cars': total_cars,
        'pending_dealers': pending_dealers,
        'recent_users': recent_users,
        'recent_cars': recent_cars,
        'recent_transactions': recent_transactions, # Passing the new data
    }
    return render(request, 'users/admin_dashboard.html', context)

# --- ACTION: VERIFY DEALER ---
@login_required
@user_passes_test(is_superuser)
def verify_dealer(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_verified = True
        user.save()
        messages.success(request, f"Dealer {user.username} has been verified successfully.")
    return redirect('admin_dashboard')