from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count 
from django.contrib.auth import get_user_model 
import re 

from users.models import DealerProfile
from .models import Car, CarImage, CarLead 
from .forms import CarForm 

User = get_user_model() 

def sanitize_phone(phone):
    if not phone: return None
    return re.sub(r'\D', '', str(phone))

# --- PUBLIC VIEWS ---

def public_homepage(request):
    featured_cars = Car.objects.filter(status='AVAILABLE', is_featured=True).order_by('-created_at')[:8]
    cars = Car.objects.filter(status__in=['AVAILABLE', 'RESERVED', 'SOLD']).order_by('status', '-created_at')
    
    q = request.GET.get('q')
    make = request.GET.get('make')
    region = request.GET.get('region')
    body_type = request.GET.get('body_type') 
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_year = request.GET.get('min_year')   
    max_year = request.GET.get('max_year')   

    if q:
        cars = cars.filter(Q(make__icontains=q) | Q(model__icontains=q) | Q(description__icontains=q))
    if make:
        cars = cars.filter(make__iexact=make)
    if region:
        cars = cars.filter(dealer__dealer_profile__city=region)
    if body_type: 
        cars = cars.filter(body_type__iexact=body_type)
    if min_price:
        try: cars = cars.filter(price__gte=min_price)
        except: pass 
    if max_price:
        try: cars = cars.filter(price__lte=max_price)
        except: pass
    if min_year: 
        try: cars = cars.filter(year__gte=min_year)
        except: pass
    if max_year: 
        try: cars = cars.filter(year__lte=max_year)
        except: pass

    all_makes = Car.objects.values_list('make', flat=True).distinct().order_by('make')
    all_body_types = Car.objects.values_list('body_type', flat=True).distinct().order_by('body_type')
    regions = DealerProfile.CITY_CHOICES 

    context = {
        'featured_cars': featured_cars,
        'cars': cars,
        'all_makes': all_makes, 
        'all_body_types': all_body_types, 
        'regions': regions, 
    }
    return render(request, 'home.html', context)

def car_detail(request, car_id): 
    car = get_object_or_404(Car, pk=car_id)
    similar_cars = Car.objects.filter(body_type=car.body_type, status='AVAILABLE').exclude(id=car.id).order_by('-created_at')[:4]
    return render(request, 'cars/car_detail.html', {'car': car, 'similar_cars': similar_cars})

def track_action(request, car_id, action_type):
    car = get_object_or_404(Car, pk=car_id)
    ip = request.META.get('REMOTE_ADDR')
    CarLead.objects.create(car=car, action=action_type.upper(), ip_address=ip)
    
    try: raw_phone = car.dealer.dealer_profile.phone_number
    except: raw_phone = '254700000000'
    clean_phone = sanitize_phone(raw_phone) or '254700000000'

    if action_type.upper() == 'WHATSAPP':
        msg = f"Hi, I am interested in the {car.year} {car.make} {car.model} listed for KES {car.price}"
        return HttpResponseRedirect(f"https://wa.me/{clean_phone}?text={msg}")
    elif action_type.upper() == 'CALL':
        return HttpResponse(status=302, headers={'Location': f"tel:{clean_phone}"})
    return HttpResponseRedirect(f"/car/{car.id}/")

def dealer_showroom(request, username):
    dealer = get_object_or_404(User, username=username)
    profile = DealerProfile.objects.filter(user=dealer).first()
    cars = Car.objects.filter(dealer=dealer, status__in=['AVAILABLE', 'RESERVED', 'SOLD']).order_by('status', '-created_at')
    
    q = request.GET.get('q')
    if q:
        cars = cars.filter(Q(make__icontains=q) | Q(model__icontains=q) | Q(description__icontains=q))
    
    return render(request, 'dealer/showroom.html', {'dealer': dealer, 'profile': profile, 'cars': cars})

# --- DEALER VIEWS ---

@login_required
def dealer_dashboard(request):
    my_cars = Car.objects.filter(dealer=request.user).order_by('-created_at')
    total_value = sum(car.price for car in my_cars)
    car_count = my_cars.count()
    profile, created = DealerProfile.objects.get_or_create(user=request.user)
    
    limit = 3
    if profile.plan_type == 'LITE': limit = 15
    elif profile.plan_type == 'PRO': limit = 999999
    can_add = car_count < limit or profile.plan_type == 'PRO'

    leads = CarLead.objects.filter(car__dealer=request.user).values('action').annotate(total=Count('id'))
    chart_labels = [i['action'] for i in leads]
    chart_values = [i['total'] for i in leads]
    recent = CarLead.objects.filter(car__dealer=request.user).order_by('-timestamp')[:5]
    
    context = {
        'cars': my_cars, 'total_cars': car_count, 'total_value': total_value,
        'chart_labels': chart_labels, 'chart_values': chart_values,
        'recent_activity': recent, 'limit': limit, 'can_add': can_add
    }
    return render(request, 'dealer/dashboard.html', context)

@login_required
def add_car(request):
    try:
        profile = request.user.dealer_profile
        car_count = Car.objects.filter(dealer=request.user).count()
        LIMITS = {'FREE': 3, 'LITE': 15, 'PRO': 999999}
        if car_count >= LIMITS.get(profile.plan_type, 3):
            messages.warning(request, "Limit reached. Upgrade to add more.")
            return redirect('dealer_dashboard')
    except: pass 

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)
            car.dealer = request.user 
            car.status = 'AVAILABLE'
            car.save()
            if request.FILES.get('image'):
                CarImage.objects.create(car=car, image=request.FILES.get('image'), is_main=True)
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
            if request.FILES.get('image'):
                CarImage.objects.create(car=car, image=request.FILES.get('image'), is_main=True)
            messages.success(request, 'Vehicle updated!')
            return redirect('dealer_dashboard')
    else:
        form = CarForm(instance=car)
    return render(request, 'dealer/edit_car.html', {'form': form, 'car': car})

@login_required
def delete_car(request, car_id):
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Vehicle removed.')
        return redirect('dealer_dashboard')
    return render(request, 'dealer/delete_confirm.html', {'car': car})

def pricing_page(request):
    return render(request, 'saas/pricing.html')

# --- REQUIRED FOR '/brands/' LINK TO WORK ---
def all_brands(request):
    """
    Displays a list of all distinct car makes with their inventory count.
    """
    brands = (
        Car.objects.values('make')
        .annotate(total=Count('id'))
        .filter(total__gt=0)
        .order_by('make')
    )
    return render(request, 'cars/all_brands.html', {'brands': brands})