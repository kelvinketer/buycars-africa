from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q 
from .models import Car, CarImage
from .forms import CarForm 

# --- PUBLIC VIEWS ---

def public_homepage(request):
    # 1. Get all cars that are available
    cars = Car.objects.filter(status='AVAILABLE').order_by('-created_at')
    
    # 2. Search Logic
    query = request.GET.get('q')
    if query:
        cars = cars.filter(
            Q(make__icontains=query) | 
            Q(model__icontains=query) | 
            Q(description__icontains=query)
        )
        
    context = {'cars': cars}
    return render(request, 'home.html', context)

def car_detail(request, car_id): 
    car = get_object_or_404(Car, pk=car_id)
    context = {
        'car': car
    }
    return render(request, 'cars/car_detail.html', context)


# --- DEALER VIEWS ---

@login_required
def dealer_dashboard(request):
    # 1. Fetch cars belonging to this dealer
    my_cars = Car.objects.filter(dealer=request.user).order_by('-created_at')
    
    # 2. Calculate Stats
    total_value = sum(car.price for car in my_cars)
    
    context = {
        'cars': my_cars, # I renamed this key to 'cars' to match your dashboard.html template
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

# --- NEW EDIT & DELETE VIEWS ---

@login_required
def edit_car(request, car_id):
    # Get the car only if it belongs to the logged-in user (Security)
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            
            # Handle Image Update (Optional: Update main image if new one provided)
            new_image = request.FILES.get('image')
            if new_image:
                # Get existing main image or create a new one
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