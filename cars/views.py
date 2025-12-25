from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q 
from django.contrib.auth import get_user_model 

from users.models import DealerProfile

from .models import Car, CarImage
from .forms import CarForm 

User = get_user_model() 

# --- PUBLIC VIEWS ---

def public_homepage(request):
    # 1. Start with ALL available cars
    cars = Car.objects.filter(status='AVAILABLE').order_by('-created_at')
    
    # 2. Capture Filter Parameters from the URL
    q = request.GET.get('q')           # Search text
    make = request.GET.get('make')     # Selected brand
    body_type = request.GET.get('body_type') # <--- NEW: Body Type
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_year = request.GET.get('min_year')   # <--- NEW: Min Year
    max_year = request.GET.get('max_year')   # <--- NEW: Max Year

    # 3. Apply Filters if they exist
    if q:
        cars = cars.filter(
            Q(make__icontains=q) | 
            Q(model__icontains=q) | 
            Q(description__icontains=q)
        )
    
    if make:
        cars = cars.filter(make__iexact=make)
        
    if body_type: # <--- NEW FILTER
        cars = cars.filter(body_type__iexact=body_type)
        
    if min_price:
        try:
            cars = cars.filter(price__gte=min_price)
        except ValueError:
            pass # Ignore if user types text instead of numbers
        
    if max_price:
        try:
            cars = cars.filter(price__lte=max_price)
        except ValueError:
            pass

    if min_year: # <--- NEW FILTER
        try:
            cars = cars.filter(year__gte=min_year)
        except ValueError:
            pass

    if max_year: # <--- NEW FILTER
        try:
            cars = cars.filter(year__lte=max_year)
        except ValueError:
            pass

    # 4. Get lists for dropdown menus
    all_makes = Car.objects.values_list('make', flat=True).distinct().order_by('make')
    
    # NEW: Get all unique body types (SUV, Sedan, etc.) for the dropdown
    all_body_types = Car.objects.values_list('body_type', flat=True).distinct().order_by('body_type')

    context = {
        'cars': cars,
        'all_makes': all_makes, 
        'all_body_types': all_body_types, # <--- Pass this to the template
    }
    return render(request, 'home.html', context)

def car_detail(request, car_id): 
    car = get_object_or_404(Car, pk=car_id)
    
    # --- RECOMMENDATION ENGINE ---
    # Fetch 3 other cars with the same Body Type (e.g., SUV, Sedan)
    # exclude(id=car.id) ensures we don't recommend the same car they are currently viewing.
    similar_cars = Car.objects.filter(
        body_type=car.body_type, 
        status='AVAILABLE'
    ).exclude(id=car.id).order_by('-created_at')[:3]
    
    context = {
        'car': car,
        'similar_cars': similar_cars, 
    }
    return render(request, 'cars/car_detail.html', context)

# --- PUBLIC DEALER SHOWROOM ---
def dealer_showroom(request, username):
    # 1. Get the dealer based on the username in the URL
    dealer = get_object_or_404(User, username=username)
    
    # 2. Explicitly fetch the profile
    profile = DealerProfile.objects.filter(user=dealer).first()
    
    # 3. Get ONLY this dealer's available cars
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
    # 1. Fetch cars belonging to this dealer
    my_cars = Car.objects.filter(dealer=request.user).order_by('-created_at')
    
    # 2. Calculate Stats
    total_value = sum(car.price for car in my_cars)
    
    context = {
        'cars': my_cars, 
        'total_cars': my_cars.count(),
        'total_value': total_value,
    }
    return render(request, 'dealer/dashboard.html', context)

@login_required
def add_car(request):
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        
        if form.is_valid():
            # 1. Create Car instance but don't save to DB yet
            car = form.save(commit=False)
            car.dealer = request.user  # Assign logged-in user
            car.status = 'AVAILABLE'
            car.save()
            
            # 2. Handle Image Upload
            image_file = request.FILES.get('image')
            if image_file:
                CarImage.objects.create(car=car, image=image_file, is_main=True)
            
            messages.success(request, 'Vehicle uploaded successfully!')
            return redirect('dealer_dashboard')
    else:
        form = CarForm()
    
    return render(request, 'dealer/add_car.html', {'form': form})

# --- EDIT & DELETE VIEWS ---

@login_required
def edit_car(request, car_id):
    # Get the car only if it belongs to the logged-in user (Security)
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            
            # Handle Image Update
            new_image = request.FILES.get('image')
            if new_image:
                car_img, created = CarImage.objects.get_or_create(car=car, is_main=True)
                car_img.image = new_image
                car_img.save()

            messages.success(request, 'Vehicle details updated successfully!')
            return redirect('dealer_dashboard')
    else:
        # Pre-fill form with existing data
        form = CarForm(instance=car)
    
    return render(request, 'dealer/edit_car.html', {'form': form, 'car': car})

@login_required
def delete_car(request, car_id):
    # Get the car only if it belongs to the logged-in user
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    
    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Vehicle removed from inventory.')
        return redirect('dealer_dashboard')
    
    return render(request, 'dealer/delete_confirm.html', {'car': car})