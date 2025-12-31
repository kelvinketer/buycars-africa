from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model 
import re 

from users.models import DealerProfile
from .models import Car, CarImage, CarView, Lead, SearchTerm
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
        clean_q = q.strip().lower()
        if len(clean_q) > 2: 
            obj, created = SearchTerm.objects.get_or_create(term=clean_q)
            if not created:
                SearchTerm.objects.filter(id=obj.id).update(count=F('count') + 1)

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
    
    # Track Page View
    ip = request.META.get('REMOTE_ADDR')
    CarView.objects.create(car=car, ip_address=ip)

    similar_cars = Car.objects.filter(body_type=car.body_type, status='AVAILABLE').exclude(id=car.id).order_by('-created_at')[:4]
    return render(request, 'cars/car_detail.html', {'car': car, 'similar_cars': similar_cars})

def track_action(request, car_id, action_type):
    car = get_object_or_404(Car, id=car_id)
    action_type = action_type.upper()
    if action_type not in ['CALL', 'WHATSAPP']:
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    Lead.objects.create(
        car=car,
        action_type=action_type,
        ip_address=ip,
        user=request.user if request.user.is_authenticated else None
    )

    return JsonResponse({'status': 'success', 'action': action_type})

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
    plan_cost = 0 
    
    if profile.plan_type == 'LITE': 
        limit = 15
        plan_cost = 5000
    elif profile.plan_type == 'PRO': 
        limit = 999999
        plan_cost = 12000
    elif profile.plan_type == 'STARTER':
        plan_cost = 1500
        
    can_add = car_count < limit or profile.plan_type == 'PRO'

    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_leads = Lead.objects.filter(
        car__dealer=request.user, 
        timestamp__gte=thirty_days_ago
    ).annotate(date=TruncDate('timestamp'))\
     .values('date')\
     .annotate(count=Count('id'))\
     .order_by('date')

    leads_dict = {item['date'].strftime('%Y-%m-%d'): item['count'] for item in daily_leads}
    
    chart_labels = []
    chart_values = []
    total_leads_30 = 0 
    
    for i in range(30):
        d = (timezone.now() - timedelta(days=29-i)).date()
        d_str = d.strftime('%Y-%m-%d')
        count = leads_dict.get(d_str, 0)
        
        chart_labels.append(d.strftime('%b %d'))
        chart_values.append(count)
        total_leads_30 += count 

    cpl = 0
    if total_leads_30 > 0 and plan_cost > 0:
        cpl = int(plan_cost / total_leads_30)

    inventory_stats = my_cars.filter(status='AVAILABLE').annotate(view_count=Count('views'))
    
    hot_car = inventory_stats.order_by('-view_count').first()
    
    three_days_ago_date = timezone.now() - timedelta(days=3)
    stale_candidates = inventory_stats.filter(created_at__lte=three_days_ago_date)
    
    if stale_candidates.exists():
        stale_car = stale_candidates.order_by('view_count').first()
    else:
        stale_car = inventory_stats.order_by('view_count').first()

    recent = Lead.objects.filter(car__dealer=request.user).order_by('-timestamp')[:5]
    
    context = {
        'cars': my_cars, 
        'total_cars': car_count, 
        'total_value': total_value,
        'chart_labels': chart_labels, 
        'chart_values': chart_values,
        'recent_activity': recent, 
        'limit': limit, 
        'can_add': can_add,
        'hot_car': hot_car,
        'stale_car': stale_car,
        'plan_cost': plan_cost,
        'leads_30': total_leads_30,
        'cpl': cpl,
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
            
            images = request.FILES.getlist('image') 
            
            for index, img in enumerate(images):
                is_main = (index == 0)
                CarImage.objects.create(car=car, image=img, is_main=is_main)

            messages.success(request, 'Vehicle uploaded successfully!')
            return redirect('dealer_dashboard')
        else:
            print("Form Errors:", form.errors)
    else:
        form = CarForm()
    return render(request, 'dealer/add_car.html', {'form': form})

@login_required
def edit_car(request, car_id):
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            car = form.save(commit=False)
            
            new_status = request.POST.get('status')
            if new_status in ['AVAILABLE', 'RESERVED', 'SOLD']:
                car.status = new_status
            
            car.save()
            
            new_images = request.FILES.getlist('image')
            if new_images:
                for img in new_images:
                    CarImage.objects.create(car=car, image=img, is_main=False)
            
            count = len(new_images)
            if count > 0:
                messages.success(request, f'Changes saved! {count} new photo(s) added successfully.')
            else:
                messages.success(request, 'Vehicle details updated successfully!')
            
            return redirect('car_detail', car_id=car.id)
            
        else:
            print("Form Errors:", form.errors)
            messages.error(request, "Please correct the errors below.")
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

# --- NEW: SET MAIN IMAGE VIEW ---
@login_required
def set_main_image(request, car_id, image_id):
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    image_to_set = get_object_or_404(CarImage, pk=image_id, car=car)

    if request.method == 'POST':
        # 1. Reset all images for this car to NOT be main
        car.images.all().update(is_main=False)
        
        # 2. Set the selected image to main
        image_to_set.is_main = True
        image_to_set.save()
        
        messages.success(request, 'Main photo updated!')
    
    return redirect('edit_car', car_id=car.id)

def pricing_page(request):
    return render(request, 'saas/pricing.html')

def all_brands(request):
    brands = (
        Car.objects.values('make')
        .annotate(total=Count('id'))
        .filter(total__gt=0)
        .order_by('make')
    )
    return render(request, 'cars/all_brands.html', {'brands': brands})