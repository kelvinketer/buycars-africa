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

# --- NEW IMPORTS FOR EMAIL ---
from django.core.mail import send_mail
from django.conf import settings

from users.models import DealerProfile
from .models import Car, CarImage, CarView, Lead, SearchTerm, Booking 
from .forms import CarForm, CarBookingForm
from .utils import render_to_pdf 

User = get_user_model() 

# --- CONFIGURATION: PLAN LIMITS ---
PLAN_LIMITS = {
    'STARTER': {'cars': 5, 'images': 6},   # Free Tier
    'LITE':    {'cars': 15, 'images': 10}, # Paid Tier 1
    'PRO':     {'cars': 50, 'images': 15}  # Paid Tier 2
}

def sanitize_phone(phone):
    if not phone: return None
    return re.sub(r'\D', '', str(phone))

# --- PUBLIC VIEWS ---

def public_homepage(request):
    """
    Renders the Homepage. Matches variables expected by home.html
    """
    featured_cars = Car.objects.filter(status='AVAILABLE', is_featured=True).order_by('-created_at')[:8]
    
    # Base Query: Show Available, Reserved, Sold cars
    cars = Car.objects.filter(status__in=['AVAILABLE', 'RESERVED', 'SOLD']).order_by('status', '-created_at')
    
    # --- GET SEARCH PARAMETERS ---
    q = request.GET.get('q')
    listing_type = request.GET.get('listing_type') 
    make = request.GET.get('make')
    region = request.GET.get('region')
    body_type = request.GET.get('body_type') 
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_year = request.GET.get('min_year')   
    max_year = request.GET.get('max_year')   

    # --- APPLY FILTERS ---

    # 1. Filter by Listing Type (Sale vs Rent)
    if listing_type:
        if listing_type == 'SALE':
            # Show cars meant for SALE or BOTH
            cars = cars.filter(listing_type__in=['SALE', 'BOTH'])
        elif listing_type == 'RENT':
            # Show cars meant for RENT or BOTH
            cars = cars.filter(listing_type__in=['RENT', 'BOTH'])

    # 2. Filter by Keywords
    if q:
        clean_q = q.strip().lower()
        if len(clean_q) > 2: 
            obj, created = SearchTerm.objects.get_or_create(term=clean_q)
            if not created:
                SearchTerm.objects.filter(id=obj.id).update(count=F('count') + 1)

        cars = cars.filter(Q(make__icontains=q) | Q(model__icontains=q) | Q(description__icontains=q))
    
    # 3. Other Filters
    if make:
        cars = cars.filter(make__iexact=make)
    if region:
        cars = cars.filter(dealer__dealer_profile__city=region)
    if body_type: 
        cars = cars.filter(body_type__iexact=body_type)
    
    # 4. Price & Year Filters
    if min_price:
        try: 
            # Note: We filter by 'price' (Selling Price) by default. 
            cars = cars.filter(price__gte=min_price)
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

    # --- PREPARE DROPDOWNS ---
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

# --- CURRENCY SWITCHER VIEW ---
@require_POST
def set_currency(request):
    """
    Sets the user's preferred currency in the session (e.g., USD, GBP, KES).
    """
    currency = request.POST.get('currency', 'KES')
    # Save choice to the user's session (temporary memory)
    request.session['currency'] = currency
    
    # Reload the page they were on, or go home if referer is missing
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# -----------------------------------

def car_detail(request, car_id): 
    car = get_object_or_404(Car, pk=car_id)
    
    # Track Page View
    ip = request.META.get('REMOTE_ADDR')
    CarView.objects.create(car=car, ip_address=ip)

    similar_cars = Car.objects.filter(body_type=car.body_type, status='AVAILABLE').exclude(id=car.id).order_by('-created_at')[:4]
    return render(request, 'cars/car_detail.html', {'car': car, 'similar_cars': similar_cars})

# --- BOOKING LOGIC ---
@login_required
def book_car(request, car_id):
    """
    Handles the booking process: Validation, Cost Calculation, Creation, and Notification.
    """
    car = get_object_or_404(Car, id=car_id)

    # 1. Security Check: Is this car actually for rent?
    if car.listing_type == 'SALE':
        messages.error(request, "This vehicle is not available for hire.")
        return redirect('car_detail', car_id=car.id)

    if request.method == 'POST':
        form = CarBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.car = car
            booking.customer = request.user
            
            # 2. Calculate Duration & Cost
            delta = booking.end_date - booking.start_date
            days = delta.days
            
            # 3. Validation: Minimum Hire Days
            if days < car.min_hire_days:
                messages.error(request, f"Minimum rental period for this car is {car.min_hire_days} days.")
                return redirect('book_car', car_id=car.id)

            # 4. Check Availability (Prevent Double Booking)
            is_booked = Booking.objects.filter(
                car=car,
                status__in=['APPROVED', 'PAID'], 
                start_date__lte=booking.end_date,
                end_date__gte=booking.start_date
            ).exists()

            if is_booked:
                messages.error(request, "This car is already booked for those dates. Please choose different dates.")
                return redirect('book_car', car_id=car.id)

            # 5. Finalize Booking Record
            booking.total_cost = days * (car.rent_price_per_day or 0)
            booking.status = 'PENDING' # Waiting for payment
            booking.save()
            
            # --- 6. SEND EMAIL NOTIFICATION TO DEALER ---
            try:
                dealer_email = car.dealer.email
                if dealer_email:
                    subject = f"New Booking Request: {car.make} {car.model}"
                    message = f"""
                    Hello {car.dealer.username},

                    You have received a new booking request for your vehicle.

                    Vehicle: {car.year} {car.make} {car.model}
                    Renter: {request.user.username} ({request.user.email})
                    Phone: {getattr(request.user, 'phone_number', 'Not provided')}
                    
                    Dates: {booking.start_date} to {booking.end_date} ({days} days)
                    Total Value: KES {booking.total_cost:,}

                    Please log in to your dashboard to review this request.
                    """
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [dealer_email],
                        fail_silently=True, # Don't crash if email fails
                    )
            except Exception as e:
                print(f"Error sending booking email: {e}")
            # --------------------------------------------

            # 7. Redirect to Payment
            return redirect('checkout', booking_id=booking.id)

    else:
        form = CarBookingForm()

    return render(request, 'cars/book_car.html', {
        'car': car, 
        'form': form,
        'min_date': timezone.now().date().isoformat()
    })

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

def diaspora_landing(request):
    """
    Dedicated landing page for International/Diaspora Ads.
    Filters for high-value premium cars (Over 3M KES).
    """
    featured_cars = Car.objects.filter(
        status='AVAILABLE', 
        price__gte=3000000 
    ).order_by('-created_at')[:4]
    
    return render(request, 'cars/diaspora_landing.html', {
        'featured_cars': featured_cars
    })

# --- DEALER VIEWS ---

@login_required
def dealer_dashboard(request):
    # 1. Fetch Inventory
    my_cars = Car.objects.filter(dealer=request.user).order_by('-created_at')
    car_count = my_cars.count()
    total_value = sum(car.price for car in my_cars if car.price) 
    
    # 2. Get Plan Limits
    profile, created = DealerProfile.objects.get_or_create(user=request.user)
    user_plan = PLAN_LIMITS.get(profile.plan_type, PLAN_LIMITS['STARTER'])
    limit = user_plan['cars']
    can_add = car_count < limit

    # 3. Fetch Leads (Sales Interest - Calls/WhatsApp)
    recent_leads = Lead.objects.filter(car__dealer=request.user).order_by('-timestamp')[:10]
    total_leads_count = Lead.objects.filter(car__dealer=request.user).count()

    # 4. Fetch Bookings (Rental Requests) - NEW!
    # We fetch bookings for cars owned by this dealer
    rental_bookings = Booking.objects.filter(car__dealer=request.user).order_by('-created_at')
    pending_bookings = rental_bookings.filter(status='PENDING').count()

    # 5. Chart Data (Leads over last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_leads = Lead.objects.filter(
        car__dealer=request.user, 
        timestamp__gte=thirty_days_ago
    ).annotate(date=TruncDate('timestamp')).values('date').annotate(count=Count('id')).order_by('date')

    leads_dict = {item['date'].strftime('%Y-%m-%d'): item['count'] for item in daily_leads}
    chart_labels = []
    chart_values = []
    
    for i in range(30):
        d = (timezone.now() - timedelta(days=29-i)).date()
        d_str = d.strftime('%Y-%m-%d')
        chart_labels.append(d.strftime('%d %b'))
        chart_values.append(leads_dict.get(d_str, 0))

    # 6. Inventory Health
    inventory_stats = my_cars.filter(status='AVAILABLE').annotate(view_count=Count('views'))
    hot_car = inventory_stats.order_by('-view_count').first()
    
    context = {
        'profile': profile,
        'cars': my_cars, 
        'rental_bookings': rental_bookings, # Pass bookings to template
        'recent_leads': recent_leads,
        
        'total_cars': car_count, 
        'limit': limit,
        'can_add': can_add,
        'total_value': total_value,
        'total_leads': total_leads_count,
        'pending_bookings': pending_bookings,
        
        'chart_labels': chart_labels, 
        'chart_values': chart_values,
        'hot_car': hot_car,
    }
    return render(request, 'dealer/dashboard.html', context)

@login_required
def download_report(request):
    """
    Generates a PDF report for the dealer's monthly performance.
    """
    dealer = request.user
    profile = request.user.dealer_profile
    
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    cars = Car.objects.filter(dealer=dealer)
    
    leads = Lead.objects.filter(car__dealer=dealer, timestamp__gte=start_of_month)
    total_leads = leads.count()
    whatsapp_clicks = leads.filter(action_type='WHATSAPP').count()
    calls = leads.filter(action_type='CALL').count()
    
    total_views = CarView.objects.filter(car__dealer=dealer, timestamp__gte=start_of_month).count()
    
    plan_cost = 0
    if profile.plan_type == 'LITE': plan_cost = 5000
    elif profile.plan_type == 'PRO': plan_cost = 12000
    elif profile.plan_type == 'STARTER': plan_cost = 1500
    
    cpl = 0
    if total_leads > 0:
        cpl = int(plan_cost / total_leads)
        
    inventory_value = cars.filter(status='AVAILABLE').aggregate(Sum('price'))['price__sum'] or 0
    sold_count = cars.filter(status='SOLD').count()
    
    sixty_days_ago = today - timedelta(days=60)
    stale_stock_count = cars.filter(status='AVAILABLE', created_at__lte=sixty_days_ago).count()

    top_cars = cars.filter(status='AVAILABLE').annotate(num_views=Count('views')).order_by('-num_views')[:5]
    
    context = {
        'dealer': dealer,
        'profile': profile,
        'date': today,
        'month_name': today.strftime('%B %Y'),
        'total_cars': cars.count(),
        'total_views': total_views,
        'total_leads': total_leads,
        'whatsapp_clicks': whatsapp_clicks,
        'calls': calls,
        'top_cars': top_cars,
        'cpl': cpl,
        'inventory_value': inventory_value,
        'sold_count': sold_count,
        'stale_stock_count': stale_stock_count
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
            
            # --- DUPLICATE CHECK ---
            reg_number = form.cleaned_data.get('registration_number')
            make = form.cleaned_data.get('make')
            model = form.cleaned_data.get('model')
            year = form.cleaned_data.get('year')
            
            duplicate_found = False
            
            if reg_number:
                clean_reg = str(reg_number).strip().replace(" ", "").upper()
                if Car.objects.filter(dealer=request.user, registration_number__iexact=clean_reg, status='AVAILABLE').exists():
                    messages.error(request, f"Duplicate: You already have a car with registration {reg_number} listed as available.")
                    duplicate_found = True

            if not duplicate_found:
                if Car.objects.filter(dealer=request.user, make=make, model=model, year=year, status='AVAILABLE').exists():
                    messages.error(request, f"Duplicate: You already have a {year} {make} {model} listed. Please check your inventory.")
                    duplicate_found = True

            if duplicate_found:
                return render(request, 'dealer/add_car.html', {'form': form})
            # -----------------------

            car = form.save(commit=False)
            car.dealer = request.user 
            car.status = 'AVAILABLE'
            car.save()
            
            image_limit = user_plan['images']
            raw_images = request.FILES.getlist('image') 
            images_to_save = raw_images[:image_limit]
            
            for index, img in enumerate(images_to_save):
                is_main = (index == 0)
                CarImage.objects.create(car=car, image=img, is_main=is_main)

            if len(raw_images) > image_limit:
                messages.warning(request, f"Vehicle saved, but we only uploaded the first {image_limit} photos (Plan Limit).")
            else:
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
    profile = request.user.dealer_profile
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            car = form.save(commit=False)
            
            new_status = request.POST.get('status')
            if new_status in ['AVAILABLE', 'RESERVED', 'SOLD']:
                car.status = new_status
            
            car.save()
            
            user_plan = PLAN_LIMITS.get(profile.plan_type, PLAN_LIMITS['STARTER'])
            image_limit = user_plan['images']
            current_count = car.images.count()
            slots_left = image_limit - current_count
            
            new_images = request.FILES.getlist('image')
            
            if new_images:
                if slots_left > 0:
                    accepted_images = new_images[:slots_left]
                    for img in accepted_images:
                        has_main = car.images.filter(is_main=True).exists()
                        is_first_new = (img == accepted_images[0] and not has_main)
                        CarImage.objects.create(car=car, image=img, is_main=is_first_new)
                    
                    if len(new_images) > slots_left:
                        messages.warning(request, f"Added {slots_left} photos. {len(new_images) - slots_left} were skipped.")
                    else:
                        messages.success(request, f"Changes saved! {len(accepted_images)} new photo(s) added.")
                else:
                    messages.error(request, f"Cannot add photos. Limit of {image_limit} reached.")
            else:
                messages.success(request, 'Vehicle details updated successfully!')
            
            return redirect('car_detail', car_id=car.id)
        else:
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
        remaining_images = CarImage.objects.filter(car_id=car_id)
        if remaining_images.exists():
            new_main = remaining_images.first()
            new_main.is_main = True
            new_main.save()
            messages.info(request, "Main image deleted. New main assigned.")
        else:
            messages.warning(request, "Main image deleted. Please upload a new one.")
    else:
        messages.success(request, "Image deleted.")
    
    return redirect('edit_car', car_id=car_id)

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

@staff_member_required
def platform_dashboard(request):
    total_dealers = User.objects.filter(dealer_profile__isnull=False).count()
    total_cars = Car.objects.count()
    total_leads = Lead.objects.count()
    
    starter_users = DealerProfile.objects.filter(plan_type='STARTER').count()
    lite_users = DealerProfile.objects.filter(plan_type='LITE').count()
    pro_users = DealerProfile.objects.filter(plan_type='PRO').count()
    
    mrr = (lite_users * 5000) + (pro_users * 12000)

    all_dealers = DealerProfile.objects.select_related('user').annotate(
        stock_count=Count('user__car_set'),
    ).order_by('-user__date_joined')

    context = {
        'total_dealers': total_dealers,
        'total_cars': total_cars,
        'total_leads': total_leads,
        'all_dealers': all_dealers,
        'mrr': mrr,
        'plan_breakdown': {
            'starter': starter_users,
            'lite': lite_users,
            'pro': pro_users
        }
    }
    return render(request, 'saas/platform_dashboard.html', context)

# --- NEW: IMPACT / 1 MILLION TREES PAGE ---
def impact_page(request):
    """
    Renders the '1 Million Trees' Impact Page with live transparency data.
    """
    # 1. Calculate Real Impact based on Sales
    total_cars_sold = Car.objects.filter(status='SOLD').count()
    
    # THE FORMULA: 1 Car Sold = 25 Trees Planted
    trees_planted = total_cars_sold * 25
    
    # Calculate Carbon Offset (Approx 20kg CO2 per tree/year)
    co2_offset_tons = (trees_planted * 20) / 1000 

    context = {
        'trees_planted': trees_planted,
        'co2_offset': co2_offset_tons,
        'cars_sold': total_cars_sold,
    }
    return render(request, 'pages/impact.html', context)

# --- NEW: TRANSPARENCY HUB ---
def transparency_hub(request):
    """
    Renders the live transparency dashboard with real-time sales-to-impact tracking.
    """
    # 1. Evidence of Action: Fetch last 10 'SOLD' cars as Proof of Impact
    # We use updated_at to show when the sale was finalized
    impact_events = Car.objects.filter(status='SOLD').order_by('-updated_at')[:10]
    
    # 2. Aggregated Outcome Data
    total_cars_sold = Car.objects.filter(status='SOLD').count()
    trees_planted = total_cars_sold * 25
    
    # OUTCOME 1: Carbon Sequestration (Approx 22kg CO2 per tree/year)
    co2_offset_tons = (trees_planted * 22) / 1000 
    
    # OUTCOME 2: Economic Benefit (Assuming 30% are fruit trees for farmers)
    # Estimated $5 per tree in annual yield for the community
    farmer_revenue_est = (trees_planted * 0.30) * 5 

    context = {
        'impact_events': impact_events,
        'trees_planted': trees_planted,
        'co2_offset': co2_offset_tons,
        'farmer_revenue': farmer_revenue_est,
        'sync_time': timezone.now(),
    }
    return render(request, 'pages/transparency.html', context)

# --- NEW: DEALERSHIP NETWORK PAGE ---
def dealership_network(request):
    """
    Renders the 'Live Network' page showing verified dealers and platform stats.
    """
    # 1. Fetch Verified Dealers (active)
    dealers = DealerProfile.objects.filter(user__is_active=True).select_related('user')
    
    # 2. Stats for the "Why Join?" section
    # Use Count and Sum from django.db.models
    total_inventory_val = Car.objects.filter(status='AVAILABLE').aggregate(Sum('price'))['price__sum'] or 0
    total_leads_generated = Lead.objects.count()
    active_stock_count = Car.objects.filter(status='AVAILABLE').count()
    
    # 3. Map Data (Group by city)
    city_counts = dealers.values('city', 'country').annotate(count=Count('id'))

    context = {
        'dealers': dealers,
        'total_value': total_inventory_val,
        'total_leads': total_leads_generated,
        'active_stock': active_stock_count,
        'city_counts': list(city_counts), # Convert QuerySet to list for JS
    }
    return render(request, 'pages/dealerships.html', context)

# --- NEW: FINANCING PAGE ---
def financing_page(request):
    """
    Renders the Asset Financing & Loans page.
    """
    return render(request, 'pages/financing.html')