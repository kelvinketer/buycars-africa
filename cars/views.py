from django.shortcuts import render, redirect, get_object_or_404 # <--- Added get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q 
from .models import Car, CarImage

# --- PUBLIC VIEWS ---

def public_homepage(request):
    # 1. Get all cars that are marked as 'AVAILABLE'
    cars = Car.objects.filter(status='AVAILABLE').order_by('-created_at')
    
    # 2. Simple Search Logic
    query = request.GET.get('q') # Gets the text from search bar
    if query:
        cars = cars.filter(
            Q(make__icontains=query) | 
            Q(model__icontains=query) | 
            Q(description__icontains=query)
        )
        
    context = {'cars': cars}
    return render(request, 'home.html', context)

def car_detail(request, pk):
    # This fetches the car with the specific ID (pk)
    # If the ID doesn't exist, it automatically shows a 404 Not Found error
    car = get_object_or_404(Car, pk=pk)
    
    context = {
        'car': car
    }
    return render(request, 'car_detail.html', context)


# --- DEALER VIEWS ---

@login_required
def dealer_dashboard(request):
    # Fetch cars that belong ONLY to this logged-in dealer
    my_cars = Car.objects.filter(dealer=request.user).order_by('-created_at')
    
    context = {
        'cars': my_cars,
        'total_cars': my_cars.count()
    }
    return render(request, 'dashboard.html', context)

@login_required
def add_car(request):
    if request.method == 'POST':
        # 1. Get data from the form
        make = request.POST.get('make')
        model = request.POST.get('model')
        year = request.POST.get('year')
        transmission = request.POST.get('transmission')
        fuel = request.POST.get('fuel_type')
        price = request.POST.get('price')
        mileage = request.POST.get('mileage')
        desc = request.POST.get('description')
        
        # 2. Get the image
        image_file = request.FILES.get('image')

        # 3. Create the Car object in the Database
        new_car = Car.objects.create(
            dealer=request.user, # Link it to the logged-in user
            make=make,
            model=model,
            year=year,
            transmission=transmission,
            fuel_type=fuel,
            price=price,
            mileage_km=mileage,
            description=desc,
            status='AVAILABLE'
        )

        # 4. Save the Image (if uploaded)
        if image_file:
            CarImage.objects.create(car=new_car, image=image_file, is_main=True)

        # 5. Success! Redirect to dashboard
        messages.success(request, 'Car added successfully!')
        return redirect('dealer_dashboard')

    return render(request, 'add_car.html')