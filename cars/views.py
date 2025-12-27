from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count 
from django.contrib.auth import get_user_model 

from users.models import DealerProfile

from .models import Car, CarImage, CarLead 
from .forms import CarForm 

User = get_user_model() 

# --- PUBLIC VIEWS ---

def public_homepage(request):
    # 1. Start with ALL available cars
    cars = Car.objects.filter(status='AVAILABLE').order_by('-created_at')
    
    # 2. Capture Filter Parameters from the URL
    q = request.GET.get('q')           # Search text
    make = request.GET.get('make')     # Selected brand
    body_type = request.GET.get('body_type') 
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_year = request.GET.get('min_year')   
    max_year = request.GET.get('max_year')   

    # 3. Apply Filters if they exist
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

    # 4. Get lists for dropdown menus
    all_makes = Car.objects.values_list('make', flat=True).distinct().order_by('make')
    all_body_types = Car.objects.values_list('body_type', flat=True).distinct().order_by('body_type')

    context = {
        'cars': cars,
        'all_makes': all_makes, 
        'all_body_types': all_body_types, 
    }
    return render(request, 'home.html', context)

def car_detail(request, car_id): 
    car = get_object_or_404(Car, pk=car_id)
    
    # --- RECOMMENDATION ENGINE ---
    similar_cars = Car.objects.filter(
        body_type=car.body_type, 
        status='AVAILABLE'
    ).exclude(id=car.id).order_by('-created_at')[:3]
    
    context = {
        'car': car,
        'similar_cars': similar_cars, 
    }
    return render(request, 'cars/car_detail.html', context)

# --- LEAD TRACKING FUNCTION ---
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
    
    # 2. Determine the destination URL
    if action_type.upper() == 'WHATSAPP':
        phone = car.dealer.phone_number if car.dealer.phone_number else '254700000000'
        message = f"Hi, I am interested in the {car.year} {car.make} {car.model} listed for KES {car.price}"
        destination = f"https://wa.me/{phone}?text={message}"
        return HttpResponseRedirect(destination)
        
    elif action_type.upper() == 'CALL':
        phone = car.dealer.phone_number if car.dealer.phone_number else '254700000000'
        destination = f"tel:{phone}"
        
        # --- FIX: Bypass Django's safety check for 'tel:' links ---
        response = HttpResponse(status=302)
        response['Location'] = destination
        return response
        
    else:
        destination = f"/car/{car.id}/"
        return HttpResponseRedirect(destination)


# --- PUBLIC DEALER SHOWROOM ---
def dealer_showroom(request, username):
    dealer = get_object_or_404(User, username=username)
    profile = DealerProfile.objects.filter(user=dealer).first()
    cars = Car.objects.filter(dealer=dealer, status='AVAILABLE').order_by('-created_at')
    
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

    # 2. Get Analytics Data for Chart (Summary)
    leads_summary = CarLead.objects.filter(car__dealer=request.user).values('action').annotate(total=Count('id'))
    
    chart_labels = [item['action'] for item in leads_summary]
    chart_values = [item['total'] for item in leads_summary]

    # 3. Get Recent Activity (Specific Details)
    recent_activity = CarLead.objects.filter(car__dealer=request.user).order_by('-timestamp')[:5]
    
    context = {
        'cars': my_cars, 
        'total_cars': my_cars.count(),
        'total_value': total_value,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'recent_activity': recent_activity, 
    }
    return render(request, 'dealer/dashboard.html', context)

@login_required
def add_car(request):
    # --- NEW: Subscription Limit Check ---
    # Get the dealer's profile (create one if it doesn't exist to avoid errors)
    profile, created = DealerProfile.objects.get_or_create(user=request.user)
    
    # Check if they have reached their limit
    if not profile.can_add_car():
        messages.warning(request, 'You have reached the limit of the Free Plan (3 Cars). Please upgrade to Pro to list more vehicles.')
        return redirect('dealer_dashboard')
    # -------------------------------------

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