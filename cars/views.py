from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count 
from django.contrib.auth import get_user_model 
import re # Import Regex for phone sanitization

from users.models import DealerProfile
from .models import Car, CarImage, CarLead 
from .forms import CarForm 

User = get_user_model() 

# --- HELPER: Phone Sanitizer ---
def sanitize_phone(phone):
    if not phone:
        return None
    # Remove all non-digit characters (spaces, +, -, etc.)
    return re.sub(r'\D', '', str(phone))

# --- PUBLIC VIEWS ---

def public_homepage(request):
    # 1. Featured Cars: Keep ONLY Available cars here (Prime real estate)
    featured_cars = Car.objects.filter(status='AVAILABLE', is_featured=True).order_by('-created_at')[:8]

    # 2. Main List: Show AVAILABLE, RESERVED, and SOLD
    # Sorting by 'status' (A -> R -> S) ensures Available is top, Reserved middle, Sold bottom.
    cars = Car.objects.filter(status__in=['AVAILABLE', 'RESERVED', 'SOLD']).order_by('status', '-created_at')
    
    # 3. Capture Filter Parameters from the URL
    q = request.GET.get('q')           # Search text
    make = request.GET.get('make')     # Selected brand
    body_type = request.GET.get('body_type') 
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_year = request.GET.get('min_year')   
    max_year = request.GET.get('max_year')   

    # 4. Apply Filters if they exist
    if q:
        cars = cars.filter(
            Q(make__icontains=q) | 
            Q(model__icontains=q) | 
            Q(description__icontains=q)
        )
    
    if make:
        cars = cars.filter(make__iexact=make)
        
    if body_type: 
        cars = cars.filter(body_type__iexact=body_type)
        
    if min_price:
        try:
            cars = cars.filter(price__gte=min_price)
        except ValueError:
            pass 
        
    if max_price:
        try:
            cars = cars.filter(price__lte=max_price)
        except ValueError:
            pass

    if min_year: 
        try:
            cars = cars.filter(year__gte=min_year)
        except ValueError:
            pass

    if max_year: 
        try:
            cars = cars.filter(year__lte=max_year)
        except ValueError:
            pass

    # 5. Get lists for dropdown menus
    all_makes = Car.objects.values_list('make', flat=True).distinct().order_by('make')
    all_body_types = Car.objects.values_list('body_type', flat=True).distinct().order_by('body_type')

    context = {
        'featured_cars': featured_cars,
        'cars': cars,
        'all_makes': all_makes, 
        'all_body_types': all_body_types, 
    }
    return render(request, 'home.html', context)

def car_detail(request, car_id): 
    car = get_object_or_404(Car, pk=car_id)
    
    # --- RECOMMENDATION ENGINE ---
    # Only recommend AVAILABLE cars to keep the user buying
    # UPDATED: Changed limit from [:3] to [:4]
    similar_cars = Car.objects.filter(
        body_type=car.body_type, 
        status='AVAILABLE'
    ).exclude(id=car.id).order_by('-created_at')[:4]
    
    context = {
        'car': car,
        'similar_cars': similar_cars, 
    }
    return render(request, 'cars/car_detail.html', context)

# --- LEAD TRACKING FUNCTION (FIXED) ---
def track_action(request, car_id, action_type):
    """
    Records an action (WhatsApp/Call) and redirects to the external link.
    """
    car = get_object_or_404(Car, pk=car_id)
    
    # 1. Record the action using the NEW CarLead model
    ip = request.META.get('REMOTE_ADDR')
    
    CarLead.objects.create(
        car=car,
        action=action_type.upper(),
        ip_address=ip
    )
    
    # 2. Get Safe Phone Number
    # Try to get profile phone, fallback to user phone, fallback to dummy
    try:
        raw_phone = car.dealer.dealer_profile.phone_number
    except:
        raw_phone = '254700000000'

    clean_phone = sanitize_phone(raw_phone)
    if not clean_phone:
        clean_phone = '254700000000'

    # 3. Determine the destination URL
    if action_type.upper() == 'WHATSAPP':
        message = f"Hi, I am interested in the {car.year} {car.make} {car.model} listed for KES {car.price}"
        destination = f"https://wa.me/{clean_phone}?text={message}"
        return HttpResponseRedirect(destination)
        
    elif action_type.upper() == 'CALL':
        destination = f"tel:{clean_phone}"
        
        # --- FIX: Bypass Django's safety check for 'tel:' links ---
        response = HttpResponse(status=302)
        response['Location'] = destination
        return response
        
    else:
        destination = f"/car/{car.id}/"
        return HttpResponseRedirect(destination)


# --- PUBLIC DEALER SHOWROOM (Updated with Search & Status Logic) ---
def dealer_showroom(request, username):
    dealer = get_object_or_404(User, username=username)
    profile = DealerProfile.objects.filter(user=dealer).first()
    
    # 1. Get Base Query (Show AVAILABLE + RESERVED + SOLD)
    # Sort: Status (A-Z) -> Created (Newest)
    cars = Car.objects.filter(dealer=dealer, status__in=['AVAILABLE', 'RESERVED', 'SOLD']).order_by('status', '-created_at')
    
    # 2. Add Search Logic
    q = request.GET.get('q')
    if q:
        cars = cars.filter(
            Q(make__icontains=q) | 
            Q(model__icontains=q) | 
            Q(description__icontains=q)
        )
    
    context = {
        'dealer': dealer,
        'profile': profile,
        'cars': cars,
    }
    return render(request, 'dealer/showroom.html', context)


# --- DEALER VIEWS ---

@login_required
def dealer_dashboard(request):
    # 1. Get Dealer's Inventory
    my_cars = Car.objects.filter(dealer=request.user).order_by('-created_at')
    total_value = sum(car.price for car in my_cars)

    # --- NEW: Limit Logic for Template Context ---
    # We calculate this here so the template knows whether to disable the button
    car_count = my_cars.count()
    profile, created = DealerProfile.objects.get_or_create(user=request.user)
    
    limit = 3 # Default Free
    if profile.plan_type == 'LITE':
        limit = 15
    elif profile.plan_type == 'PRO':
        limit = 999999
        
    can_add = car_count < limit
    if profile.plan_type == 'PRO':
        can_add = True
    # ---------------------------------------------

    # 2. Get Analytics Data for Chart (Summary)
    leads_summary = CarLead.objects.filter(car__dealer=request.user).values('action').annotate(total=Count('id'))
    
    chart_labels = [item['action'] for item in leads_summary]
    chart_values = [item['total'] for item in leads_summary]

    # 3. Get Recent Activity (Specific Details)
    recent_activity = CarLead.objects.filter(car__dealer=request.user).order_by('-timestamp')[:5]
    
    context = {
        'cars': my_cars, 
        'total_cars': car_count,
        'total_value': total_value,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'recent_activity': recent_activity,
        # New Context variables for Paywall
        'limit': limit,
        'can_add': can_add
    }
    return render(request, 'dealer/dashboard.html', context)

@login_required
def add_car(request):
    # --- PAYWALL LOGIC START ---
    try:
        profile = request.user.dealer_profile
        car_count = Car.objects.filter(dealer=request.user).count()
        
        # Define Limits
        LIMITS = {
            'FREE': 3,
            'LITE': 15,
            'PRO': 999999
        }
        
        user_limit = LIMITS.get(profile.plan_type, 3) 
        
        # Check Limit
        if car_count >= user_limit:
            messages.warning(request, f"You have reached your limit of {user_limit} cars. Please Upgrade to add more.")
            return redirect('dealer_dashboard')
            
    except Exception as e:
        print(f"Paywall Error: {e}")
        pass 
    # --- PAYWALL LOGIC END ---

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        
        if form.is_valid():
            car = form.save(commit=False)
            car.dealer = request.user 
            car.status = 'AVAILABLE'
            car.save()
            
            image_file = request.FILES.get('image')
            if image_file:
                CarImage.objects.create(car=car, image=image_file, is_main=True)
            
            messages.success(request, 'Vehicle uploaded successfully!')
            return redirect('dealer_dashboard')
    else:
        form = CarForm()
    
    return render(request, 'dealer/add_car.html', {'form': form})

@login_required
def edit_car(request, car_id):
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            
            new_image = request.FILES.get('image')
            if new_image:
                car_img, created = CarImage.objects.get_or_create(car=car, is_main=True)
                car_img.image = new_image
                car_img.save()

            messages.success(request, 'Vehicle details updated successfully!')
            return redirect('dealer_dashboard')
    else:
        form = CarForm(instance=car)
    
    return render(request, 'dealer/edit_car.html', {'form': form, 'car': car})

@login_required
def delete_car(request, car_id):
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    
    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Vehicle removed from inventory.')
        return redirect('dealer_dashboard')
    
    return render(request, 'dealer/delete_confirm.html', {'car': car})