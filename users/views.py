from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command

# --- DEBUGGING TOOLS IMPORTS ---
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings

# --- LOCAL IMPORTS ---
from .models import DealerProfile, CustomerProfile
from .forms import CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm, CustomerSignUpForm
from payments.models import Payment   
from cars.models import Car, Lead, SearchTerm

User = get_user_model()

# ==========================================
#      AUTHENTICATION & SIGNUP FLOWS
# ==========================================

def select_account(request):
    """
    Gateway page where users choose between Renter or Dealer account.
    """
    return render(request, 'auth/select_account.html')

def customer_signup(request):
    """
    Handles registration for Renters (Buyers).
    Includes UX FIX: Redirects back to the previous page (e.g., Booking) if 'next' is present.
    """
    if request.method == 'POST':
        form = CustomerSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! You can now book cars.")
            
            # --- UX FIX: Redirect back to the booking page if applicable ---
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            # -------------------------------------------------------------
            
            return redirect('home') 
    else:
        form = CustomerSignUpForm()
    return render(request, 'auth/customer_signup.html', {'form': form})

def signup_view(request):
    """
    Handles registration for Dealers.
    Redirects to Dealer Dashboard upon success.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Ensure we create the profile immediately for Dealers
            DealerProfile.objects.create(user=user, business_name=f"{user.username}'s Yard")
            login(request, user)
            return redirect('dealer_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})

def login_view(request):
    """
    Smart Login: Redirects users based on their Role (Admin, Dealer, or Renter).
    """
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # 1. If there is a 'next' param (e.g. they were trying to book), go there first
            if 'next' in request.GET:
                return redirect(request.GET.get('next'))
            
            # 2. Super Admin -> CEO Dashboard
            if user.is_superuser:
                return redirect('admin_dashboard')
            
            # 3. Dealer -> Dealer Dashboard
            if hasattr(user, 'dealer_profile'):
                return redirect('dealer_dashboard')
            
            # 4. Renter/Regular User -> Homepage (or Renter Dashboard)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home')

# ==========================================
#      RENTER / CUSTOMER DASHBOARD
# ==========================================

@login_required
def renter_dashboard(request):
    """
    Dashboard for Renters to view profile status and payment history.
    """
    # 1. Security Check: If they are a Dealer, send them to Dealer Dashboard
    if hasattr(request.user, 'dealer_profile'):
        return redirect('dealer_dashboard')

    # 2. Get the Profile
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)

    # 3. Handle Profile Updates
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('renter_dashboard')
    else:
        u_form = UserUpdateForm(instance=request.user)

    # 4. Get Rental History (Based on Payments made by their phone number)
    # We use phone_number because M-Pesa payments are linked to phone
    user_payments = Payment.objects.filter(phone_number=request.user.phone_number).order_by('-id')

    context = {
        'u_form': u_form,
        'profile': profile,
        'payments': user_payments,
    }
    return render(request, 'users/renter_dashboard.html', context)

# ==========================================
#      DEALER SETTINGS & PROFILE
# ==========================================

@login_required
def profile_settings(request):
    # Only allow Dealers to access this
    if not hasattr(request.user, 'dealer_profile'):
        messages.error(request, "This page is for Dealers only.")
        return redirect('home')

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
    """
    The 'God View' for the SaaS Founder.
    Tracks all dealers, system-wide inventory, and platform health.
    """
    
    # 1. FINANCIALS
    total_revenue = Payment.objects.filter(status='SUCCESS').aggregate(Sum('amount'))['amount__sum'] or 0

    # 2. USERS & DEALERS
    total_users = User.objects.count()
    
    # 3. INVENTORY HEALTH
    total_cars = Car.objects.count()
    
    # 4. PENDING ACTIONS
    pending_dealers = User.objects.filter(dealer_profile__isnull=False, is_verified=False).count()

    # 5. VALUE METER (LEADS)
    total_leads = Lead.objects.count()
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    leads_today = Lead.objects.filter(timestamp__gte=today_start).count()

    # 6. MARKET DOMINANCE (Chart Data)
    brand_stats = Car.objects.values('make').annotate(count=Count('id')).order_by('-count')[:5]
    brand_labels = [entry['make'] for entry in brand_stats]
    brand_counts = [entry['count'] for entry in brand_stats]
    
    top_5_count = sum(brand_counts)
    other_count = total_cars - top_5_count
    if other_count > 0:
        brand_labels.append('Other')
        brand_counts.append(other_count)

    # 7. TOP DEALER LEADERBOARD
    top_dealers = User.objects.filter(dealer_profile__isnull=False).annotate(
        inventory_count=Count('cars', distinct=True),
        leads_generated=Count('cars__leads', distinct=True)
    ).order_by('-leads_generated', '-inventory_count')[:5]

    # 8. SEARCH ANALYTICS [FIXED]
    # Replaced aggregation with direct table access to fix 'GROUP BY' error
    top_searches = SearchTerm.objects.all().order_by('-count')[:10]

    # 9. CHURN FORECAST (EXPIRING SOON)
    seven_days_from_now = timezone.now() + timedelta(days=7)
    
    expiring_dealers = User.objects.filter(
        dealer_profile__isnull=False,
        dealer_profile__plan_type__in=['LITE', 'PRO'],
        dealer_profile__subscription_expiry__lte=seven_days_from_now,
        dealer_profile__subscription_expiry__gte=timezone.now()
    ).select_related('dealer_profile').order_by('dealer_profile__subscription_expiry')[:5]

    # 10. RECENT ACTIVITY
    recent_users = User.objects.filter(dealer_profile__isnull=False).select_related('dealer_profile').order_by('-date_joined')[:5]
    recent_cars = Car.objects.select_related('dealer').order_by('-created_at')[:5]

    # 11. TRANSACTION HISTORY
    recent_transactions = Payment.objects.order_by('-id')[:10]
    for trans in recent_transactions:
        phone = trans.phone_number
        # Try to find the user associated with this payment
        related_user = User.objects.filter(
            Q(phone_number=phone) | 
            Q(dealer_profile__phone_number=phone)
        ).first()
        trans.related_user = related_user

    # 12. GROWTH ANALYTICS (Last 30 Days)
    today = timezone.now().date()
    dates = []
    user_counts = []
    car_counts = []

    for i in range(29, -1, -1):
        target_date = today - timedelta(days=i)
        dates.append(target_date.strftime('%b %d'))
        # Track new Dealers specifically
        daily_users = User.objects.filter(date_joined__date=target_date, dealer_profile__isnull=False).count()
        daily_cars = Car.objects.filter(created_at__date=target_date).count()
        user_counts.append(daily_users)
        car_counts.append(daily_cars)

    # 13. MASTER DEALER LIST (The "God View" Table)
    all_dealers = User.objects.filter(dealer_profile__isnull=False).select_related('dealer_profile').order_by('-date_joined')
    
    search_query = request.GET.get('q')
    if search_query:
        all_dealers = all_dealers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(dealer_profile__business_name__icontains=search_query) |
            Q(dealer_profile__phone_number__icontains=search_query)
        )

    context = {
        'total_revenue': total_revenue,
        'total_users': total_users,
        'total_cars': total_cars,
        'pending_dealers': pending_dealers,
        'total_leads': total_leads,
        'leads_today': leads_today,
        'brand_labels': brand_labels,
        'brand_counts': brand_counts,
        'top_dealers': top_dealers,
        'top_searches': top_searches,
        'expiring_dealers': expiring_dealers, 
        'recent_users': recent_users,
        'recent_cars': recent_cars,
        'recent_transactions': recent_transactions,
        'analytics_dates': dates,
        'analytics_users': user_counts,
        'analytics_cars': car_counts,
        'all_dealers': all_dealers,
        'search_query': search_query,
    }
    return render(request, 'users/admin_dashboard.html', context)

# --- ACTION: VERIFY DEALER ---
@login_required
@user_passes_test(is_superuser)
def verify_dealer(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_verified:
            user.is_verified = False
            messages.warning(request, f"Dealer {user.username} has been UNVERIFIED.")
        else:
            user.is_verified = True
            messages.success(request, f"Dealer {user.username} has been VERIFIED successfully.")
        
        user.save()
    return redirect('admin_dashboard')

# ==========================================
#      MANUAL TRIGGER TOOLS (CEO ONLY)
# ==========================================

@staff_member_required
def trigger_weekly_report(request):
    """
    TEMPORARY DEBUGGER: Tests connection to Gmail directly.
    Replaces the standard report command to expose errors.
    """
    try:
        # 1. Print settings to the screen (Hidden password for security)
        debug_info = f"""
        Testing connection with:
        HOST: {settings.EMAIL_HOST}
        PORT: {settings.EMAIL_PORT}
        TLS: {settings.EMAIL_USE_TLS}
        USER: {settings.EMAIL_HOST_USER}
        """
        
        # 2. Try to send a simple "Hello" email
        send_mail(
            subject='Test Connection from Render',
            message='If you received this, your email settings are PERFECT! 🚀',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email], # Sends to your admin email
            fail_silently=False,
        )
        
        return HttpResponse(f"✅ SUCCESS! Email sent to {request.user.email}. <br><pre>{debug_info}</pre>")

    except Exception as e:
        # 3. If it fails, PRINT THE EXACT ERROR to the browser
        return HttpResponse(f"❌ FAILED. <br> <strong>Error:</strong> {e} <br><pre>{debug_info}</pre>")

@staff_member_required
def trigger_subscription_check(request):
    """
    Manually triggers the subscription enforcer.
    """
    try:
        call_command('check_expiry')
        messages.success(request, "✅ SUCCESS: Subscription check complete. Expired users downgraded.")
    except Exception as e:
        messages.error(request, f"❌ ERROR: Failed to check subscriptions. Details: {e}")

    return redirect('admin_dashboard')