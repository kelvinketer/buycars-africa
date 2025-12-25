from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q 
from .models import Car, CarImage
from .forms import CarForm # Make sure you created cars/forms.py!

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

def car_detail(request, car_id): # Changed 'pk' to 'car_id' to match URLs
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
        'my_cars': my_cars,
        'total_cars': my_cars.count(),
        'total_value': total_value,
    }
    # Points to the new template we created
    return render(request, 'dealer/dashboard.html', context)

@login_required
def add_car(request):
    if request.method == 'POST':
        # Use the Form to handle validation automatically
        form = CarForm(request.POST, request.FILES)
        
        if form.is_valid():
            # 1. Create Car instance but don't save to DB yet
            car = form.save(commit=False)
            car.dealer = request.user  # Assign logged-in user
            car.status = 'AVAILABLE'
            car.save()
            
            # 2. Handle Image Upload
            # We check request.FILES for the 'image' field we added to the form
            image_file = request.FILES.get('image')
            if image_file:
                CarImage.objects.create(car=car, image=image_file, is_main=True)
            
            messages.success(request, 'Vehicle uploaded successfully!')
            return redirect('dealer_dashboard')
    else:
        form = CarForm()
    
    return render(request, 'dealer/add_car.html', {'form': form})