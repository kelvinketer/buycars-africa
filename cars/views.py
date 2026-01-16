from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST 
from django.contrib import messages
from django.db.models import Q, Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model 
import re 

# --- IMPORT FOR MIGRATION FIX ---
from django.core.management import call_command

# --- NEW IMPORTS FOR EMAIL ---
from django.core.mail import send_mail
from django.conf import settings

from users.models import DealerProfile
from .models import Car, CarImage, CarView, Lead, SearchTerm, Booking 
from .forms import CarForm, CarBookingForm
from .utils import render_to_pdf 

User = get_user_model() 

# --- CONFIGURATION: PLAN LIMITS (UPDATED) ---
PLAN_LIMITS = {
    'STARTER': {'cars': 10, 'images': 8},
    'LITE':    {'cars': 40, 'images': 15},
    'PRO':     {'cars': 150, 'images': 30}
}

def sanitize_phone(phone):
    if not phone: return None
    return re.sub(r'\D', '', str(phone))

# --- PUBLIC VIEWS ---

def public_homepage(request):
    featured_cars = Car.objects.filter(status='AVAILABLE', is_featured=True).order_by('-created_at')[:8]
    cars = Car.objects.filter(status__in=['AVAILABLE', 'RESERVED', 'SOLD']).order_by('status', '-created_at')
    
    q = request.GET.get('q')
    listing_type = request.GET.get('listing_type') 
    make = request.GET.get('make')
    region = request.GET.get('region')
    body_type = request.GET.get('body_type') 
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_year = request.GET.get('min_year')   
    max_year = request.GET.get('max_year')   

    if listing_type:
        if listing_type == 'SALE': cars = cars.filter(listing_type__in=['SALE', 'BOTH'])
        elif listing_type == 'RENT': cars = cars.filter(listing_type__in=['RENT', 'BOTH'])

    if q:
        clean_q = q.strip().lower()
        if len(clean_q) > 2: 
            obj, created = SearchTerm.objects.get_or_create(term=clean_q)
            if not created: SearchTerm.objects.filter(id=obj.id).update(count=F('count') + 1)
        cars = cars.filter(Q(make__icontains=q) | Q(model__icontains=q) | Q(description__icontains=q))
    
    if make: cars = cars.filter(make__iexact=make)
    if region: cars = cars.filter(dealer__dealer_profile__city=region)
    if body_type: cars = cars.filter(body_type__iexact=body_type)
    
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
        'featured_cars': featured_cars, 'cars': cars, 'all_makes': all_makes, 
        'all_body_types': all_body_types, 'regions': regions, 
    }
    return render(request, 'home.html', context)

@require_POST
def set_currency(request):
    currency = request.POST.get('currency', 'KES')
    request.session['currency'] = currency
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def car_detail(request, car_id): 
    car = get_object_or_404(Car, pk=car_id)
    ip = request.META.get('REMOTE_ADDR')
    CarView.objects.create(car=car, ip_address=ip)
    similar_cars = Car.objects.filter(body_type=car.body_type, status='AVAILABLE').exclude(id=car.id).order_by('-created_at')[:4]
    return render(request, 'cars/car_detail.html', {'car': car, 'similar_cars': similar_cars})

@login_required
def book_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if car.listing_type == 'SALE':
        messages.error(request, "This vehicle is not available for hire.")
        return redirect('car_detail', car_id=car.id)

    if request.method == 'POST':
        form = CarBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.car = car
            booking.customer = request.user
            delta = booking.end_date - booking.start_date
            days = delta.days
            
            if days < car.min_hire_days:
                messages.error(request, f"Minimum rental period for this car is {car.min_hire_days} days.")
                return redirect('book_car', car_id=car.id)

            is_booked = Booking.objects.filter(
                car=car, status__in=['APPROVED', 'PAID'], 
                start_date__lte=booking.end_date, end_date__gte=booking.start_date
            ).exists()

            if is_booked:
                messages.error(request, "This car is already booked for those dates.")
                return redirect('book_car', car_id=car.id)

            booking.total_cost = days * (car.rent_price_per_day or 0)
            booking.status = 'PENDING'
            booking.save()
            
            try:
                dealer_email = car.dealer.email
                if dealer_email:
                    subject = f"New Booking Request: {car.make} {car.model}"
                    message = f"New booking from {request.user.username}. Dates: {booking.start_date} to {booking.end_date}. Value: {booking.total_cost}"
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [dealer_email], fail_silently=True)
            except Exception as e:
                print(f"Error sending email: {e}")

            return redirect('checkout', booking_id=booking.id)
    else:
        form = CarBookingForm()

    return render(request, 'cars/book_car.html', {'car': car, 'form': form, 'min_date': timezone.now().date().isoformat()})

def track_action(request, car_id, action_type):
    car = get_object_or_404(Car, id=car_id)
    action_type = action_type.upper()
    if action_type not in ['CALL', 'WHATSAPP']:
        return JsonResponse({'status': 'error'}, status=400)

    ip = request.META.get('REMOTE_ADDR')
    Lead.objects.create(car=car, action_type=action_type, ip_address=ip, user=request.user if request.user.is_authenticated else None)
    return JsonResponse({'status': 'success', 'action': action_type})

def dealer_showroom(request, username):
    dealer = get_object_or_404(User, username=username)
    profile = DealerProfile.objects.filter(user=dealer).first()
    cars = Car.objects.filter(dealer=dealer, status__in=['AVAILABLE', 'RESERVED', 'SOLD']).order_by('status', '-created_at')
    q = request.GET.get('q')
    if q: cars = cars.filter(Q(make__icontains=q) | Q(model__icontains=q))
    return render(request, 'dealer/showroom.html', {'dealer': dealer, 'profile': profile, 'cars': cars})

def diaspora_landing(request):
    featured_cars = Car.objects.filter(status='AVAILABLE', price__gte=3000000).order_by('-created_at')[:4]
    return render(request, 'cars/diaspora_landing.html', {'featured_cars': featured_cars})

# --- DEALER VIEWS ---

@login_required
def dealer_dashboard(request):
    my_cars = Car.objects.filter(dealer=request.user).order_by('-created_at')
    car_count = my_cars.count()
    total_value = sum(car.price for car in my_cars if car.price) 
    profile, created = DealerProfile.objects.get_or_create(user=request.user)
    user_plan = PLAN_LIMITS.get(profile.plan_type, PLAN_LIMITS['STARTER'])
    limit = user_plan['cars']
    can_add = car_count < limit

    recent_leads = Lead.objects.filter(car__dealer=request.user).order_by('-timestamp')[:10]
    total_leads_count = Lead.objects.filter(car__dealer=request.user).count()
    rental_bookings = Booking.objects.filter(car__dealer=request.user).order_by('-created_at')
    pending_bookings = rental_bookings.filter(status='PENDING').count()

    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_leads = Lead.objects.filter(car__dealer=request.user, timestamp__gte=thirty_days_ago).annotate(date=TruncDate('timestamp')).values('date').annotate(count=Count('id')).order_by('date')
    leads_dict = {item['date'].strftime('%Y-%m-%d'): item['count'] for item in daily_leads}
    chart_labels = []
    chart_values = []
    
    for i in range(30):
        d = (timezone.now() - timedelta(days=29-i)).date()
        d_str = d.strftime('%Y-%m-%d')
        chart_labels.append(d.strftime('%d %b'))
        chart_values.append(leads_dict.get(d_str, 0))

    hot_car = my_cars.filter(status='AVAILABLE').annotate(view_count=Count('views')).order_by('-view_count').first()
    
    context = {
        'profile': profile, 'cars': my_cars, 'rental_bookings': rental_bookings, 'recent_leads': recent_leads,
        'total_cars': car_count, 'limit': limit, 'can_add': can_add, 'total_value': total_value,
        'total_leads': total_leads_count, 'pending_bookings': pending_bookings,
        'chart_labels': chart_labels, 'chart_values': chart_values, 'hot_car': hot_car,
    }
    return render(request, 'dealer/dashboard.html', context)

@login_required
def download_report(request):
    dealer = request.user
    profile = request.user.dealer_profile
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    cars = Car.objects.filter(dealer=dealer)
    leads = Lead.objects.filter(car__dealer=dealer, timestamp__gte=start_of_month)
    total_views = CarView.objects.filter(car__dealer=dealer, timestamp__gte=start_of_month).count()
    
    plan_cost = 5000 if profile.plan_type == 'LITE' else (12000 if profile.plan_type == 'PRO' else 1500)
    cpl = int(plan_cost / leads.count()) if leads.count() > 0 else 0
        
    context = {
        'dealer': dealer, 'profile': profile, 'date': today, 'month_name': today.strftime('%B %Y'),
        'total_cars': cars.count(), 'total_views': total_views, 'total_leads': leads.count(),
        'whatsapp_clicks': leads.filter(action_type='WHATSAPP').count(), 'calls': leads.filter(action_type='CALL').count(),
        'cpl': cpl, 'inventory_value': cars.filter(status='AVAILABLE').aggregate(Sum('price'))['price__sum'] or 0,
        'sold_count': cars.filter(status='SOLD').count(),
    }
    
    pdf = render_to_pdf('dealer/monthly_report.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Monthly_Report_{profile.business_name}_{today.strftime('%b_%Y')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error Generating PDF", status=400)

@login_required
def add_car(request):
    profile = request.user.dealer_profile
    car_count = Car.objects.filter(dealer=request.user).count()
    user_plan = PLAN_LIMITS.get(profile.plan_type, PLAN_LIMITS['STARTER'])
    
    if car_count >= user_plan['cars']:
        messages.warning(request, f"Plan limit reached ({user_plan['cars']} cars). Upgrade to add more.")
        return redirect('dealer_dashboard')

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            reg_number = form.cleaned_data.get('registration_number')
            if reg_number:
                clean_reg = str(reg_number).strip().replace(" ", "").upper()
                if Car.objects.filter(dealer=request.user, registration_number__iexact=clean_reg, status='AVAILABLE').exists():
                    messages.error(request, f"Duplicate registration found.")
                    return render(request, 'dealer/add_car.html', {'form': form})

            car = form.save(commit=False)
            car.dealer = request.user 
            car.status = 'AVAILABLE'
            car.save()
            
            image_limit = user_plan['images']
            raw_images = request.FILES.getlist('image') 
            for index, img in enumerate(raw_images[:image_limit]):
                CarImage.objects.create(car=car, image=img, is_main=(index == 0))

            messages.success(request, 'Vehicle uploaded successfully!')
            return redirect('dealer_dashboard')
    else:
        form = CarForm()
    return render(request, 'dealer/add_car.html', {'form': form})

@login_required
def edit_car(request, car_id):
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    profile = request.user.dealer_profile
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            car = form.save(commit=False)
            new_status = request.POST.get('status')
            if new_status in ['AVAILABLE', 'RESERVED', 'SOLD']: car.status = new_status
            car.save()
            
            user_plan = PLAN_LIMITS.get(profile.plan_type, PLAN_LIMITS['STARTER'])
            image_limit = user_plan['images']
            current_count = car.images.count()
            slots_left = image_limit - current_count
            new_images = request.FILES.getlist('image')
            
            if new_images and slots_left > 0:
                for img in new_images[:slots_left]:
                    has_main = car.images.filter(is_main=True).exists()
                    CarImage.objects.create(car=car, image=img, is_main=(not has_main))
                messages.success(request, "Changes saved!")
            elif new_images:
                messages.error(request, "Image limit reached.")
            
            return redirect('car_detail', car_id=car.id)
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

@login_required
def mark_as_sold(request, car_id):
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    car.status = 'SOLD'
    car.save()
    messages.success(request, "Car marked as SOLD!")
    return redirect('dealer_dashboard')

@login_required
def set_main_image(request, car_id, image_id):
    car = get_object_or_404(Car, pk=car_id, dealer=request.user)
    image_to_set = get_object_or_404(CarImage, pk=image_id, car=car)
    if request.method == 'POST':
        car.images.all().update(is_main=False)
        image_to_set.is_main = True
        image_to_set.save()
        messages.success(request, 'Main photo updated!')
    return redirect('edit_car', car_id=car.id)

@login_required
def delete_car_image(request, image_id):
    image = get_object_or_404(CarImage, id=image_id)
    if image.car.dealer != request.user:
        messages.error(request, "Permission denied.")
        return redirect('dealer_dashboard')
    car_id = image.car.id
    was_main = image.is_main
    image.delete()
    if was_main:
        new_main = CarImage.objects.filter(car_id=car_id).first()
        if new_main:
            new_main.is_main = True
            new_main.save()
    return redirect('edit_car', car_id=car_id)

def pricing_page(request): return render(request, 'saas/pricing.html')

def all_brands(request):
    brands = Car.objects.values('make').annotate(total=Count('id')).filter(total__gt=0).order_by('make')
    return render(request, 'cars/all_brands.html', {'brands': brands})

@staff_member_required
def platform_dashboard(request):
    total_dealers = User.objects.filter(dealer_profile__isnull=False).count()
    lite_users = DealerProfile.objects.filter(plan_type='LITE').count()
    pro_users = DealerProfile.objects.filter(plan_type='PRO').count()
    mrr = (lite_users * 5000) + (pro_users * 12000)
    all_dealers = DealerProfile.objects.select_related('user').annotate(stock_count=Count('user__car_set')).order_by('-user__date_joined')
    context = {
        'total_dealers': total_dealers, 'total_cars': Car.objects.count(), 'total_leads': Lead.objects.count(),
        'all_dealers': all_dealers, 'mrr': mrr,
    }
    return render(request, 'saas/platform_dashboard.html', context)

def impact_page(request):
    total_cars_sold = Car.objects.filter(status='SOLD').count()
    trees_planted = total_cars_sold * 25
    co2_offset_tons = (trees_planted * 20) / 1000 
    context = {'trees_planted': trees_planted, 'co2_offset': co2_offset_tons, 'cars_sold': total_cars_sold}
    return render(request, 'pages/impact.html', context)

def transparency_hub(request):
    impact_events = Car.objects.filter(status='SOLD').order_by('-created_at')[:10]
    total_cars_sold = Car.objects.filter(status='SOLD').count()
    trees_planted = total_cars_sold * 25
    co2_offset_tons = (trees_planted * 22) / 1000 
    farmer_revenue_est = (trees_planted * 0.30) * 5 
    context = {'impact_events': impact_events, 'trees_planted': trees_planted, 'co2_offset': co2_offset_tons, 'farmer_revenue': farmer_revenue_est, 'sync_time': timezone.now()}
    return render(request, 'pages/transparency.html', context)

def dealership_network(request):
    dealers = DealerProfile.objects.filter(user__is_active=True).select_related('user')
    total_inventory_val = Car.objects.filter(status='AVAILABLE').aggregate(Sum('price'))['price__sum'] or 0
    city_counts = dealers.values('city').annotate(count=Count('id'))
    context = {'dealers': dealers, 'total_value': total_inventory_val, 'total_leads': Lead.objects.count(), 'active_stock': Car.objects.filter(status='AVAILABLE').count(), 'city_counts': list(city_counts)}
    return render(request, 'pages/dealerships.html', context)

def financing_page(request): return render(request, 'pages/financing.html')
def partners_page(request): return render(request, 'pages/partners.html')

def driving_change_page(request):
    cars_sold = Car.objects.filter(status='SOLD').count()
    context = {'dealers_empowered': DealerProfile.objects.count(), 'trees_planted': cars_sold * 25, 'capital_unlocked': cars_sold * 1500000}
    return render(request, 'pages/driving_change.html', context)

@login_required
def dealer_academy(request):
    modules = [
        {'id': 1, 'title': 'The Digital Broker Mindset', 'desc': 'Understanding the BuyCars ecosystem.', 'duration': '15 min', 'status': 'COMPLETED', 'progress': 100, 'icon': 'fas fa-brain'},
        {'id': 2, 'title': 'Sourcing & Verification', 'desc': 'How to spot a "lemon" and verify VINs.', 'duration': '45 min', 'status': 'IN_PROGRESS', 'progress': 40, 'icon': 'fas fa-search-plus'},
        {'id': 3, 'title': 'The Perfect Listing', 'desc': 'Photography guides and AI pricing.', 'duration': '30 min', 'status': 'LOCKED', 'progress': 0, 'icon': 'fas fa-camera'},
        {'id': 4, 'title': 'Closing the Deal', 'desc': 'Handling WhatsApp leads securely.', 'duration': '60 min', 'status': 'LOCKED', 'progress': 0, 'icon': 'fas fa-handshake'}
    ]
    resources = [{'name': 'KRA Sale Agreement', 'type': 'PDF', 'size': '1.2 MB'}, {'name': 'Vehicle Inspection Checklist', 'type': 'PDF', 'size': '0.8 MB'}, {'name': 'Q4 2025 Market Index', 'type': 'PDF', 'size': '3.5 MB'}]
    return render(request, 'dealer/academy.html', {'modules': modules, 'resources': resources, 'completion_rate': 35})

# --- EMERGENCY MIGRATION VIEW (RUN ONCE ONLY) ---
def run_migrations_view(request):
    if not request.user.is_superuser:
        return HttpResponse("<h1>Access Denied</h1><p>Only admins can run this.</p>", status=403)
    try:
        call_command('migrate')
        return HttpResponse("<h1>SUCCESS! Database Updated.</h1><p>The 'updated_at' column has been created. <br> <a href='/dashboard/'>Go back to Dashboard</a></p>")
    except Exception as e:
        return HttpResponse(f"<h1>Error Running Migration</h1><p>{e}</p>")
    
    # --- ADD AT THE VERY BOTTOM OF cars/views.py ---

from django.core.management import call_command
import io

def run_migrations_view(request):
    """
    SUPER FIXER: Forces 'makemigrations' then 'migrate'.
    Use this when the database column is missing but standard migrate doesn't fix it.
    """
    if not request.user.is_superuser:
        return HttpResponse("<h1>Access Denied</h1><p>Log in as admin first.</p>", status=403)

    output = io.StringIO()
    try:
        output.write("--- STEP 1: MAKING MIGRATIONS ---\n")
        # Force Django to look for changes in the 'cars' app and create the file
        call_command('makemigrations', 'cars', interactive=False, stdout=output)
        
        output.write("\n--- STEP 2: MIGRATING DATABASE ---\n")
        # Apply the new file to the database
        call_command('migrate', interactive=False, stdout=output)
        
        return HttpResponse(f"""
            <h1 style='color:green'>REPAIR COMPLETE</h1>
            <pre style='background:#eee; padding:15px; border-radius:5px;'>{output.getvalue()}</pre>
            <br>
            <a href='/dashboard/' style='font-size:20px; font-weight:bold;'>&larr; Return to Dashboard (It will work now)</a>
        """)
    except Exception as e:
        return HttpResponse(f"<h1 style='color:red'>ERROR</h1><pre>{e}</pre>")