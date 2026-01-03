from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model 
import re 

from users.models import DealerProfile
from .models import Car, CarImage, CarView, Lead, SearchTerm
from .forms import CarForm 
from .utils import render_to_pdf 

User = get_user_model() 

# --- CONFIGURATION: PLAN LIMITS (Source of Truth) ---
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
    
    # --- LOGIC UPDATE: Use PLAN_LIMITS ---
    user_plan = PLAN_LIMITS.get(profile.plan_type, PLAN_LIMITS['STARTER'])
    limit = user_plan['cars']
    
    plan_cost = 0 
    if profile.plan_type == 'LITE': 
        plan_cost = 5000
    elif profile.plan_type == 'PRO': 
        plan_cost = 12000
    elif profile.plan_type == 'STARTER':
        plan_cost = 1500
        
    can_add = car_count < limit

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

    # Correct use of 'views' (consistent with model definition)
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
def download_report(request):
    """
    Generates a PDF report for the dealer's monthly performance.
    """
    dealer = request.user
    profile = request.user.dealer_profile
    
    # 1. Define Date Range (Current Month)
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 2. Get Dealer's Cars
    cars = Car.objects.filter(dealer=dealer)
    
    # 3. Calculate Leads (Calls + WhatsApp)
    leads = Lead.objects.filter(car__dealer=dealer, timestamp__gte=start_of_month)
    total_leads = leads.count()
    whatsapp_clicks = leads.filter(action_type='WHATSAPP').count()
    calls = leads.filter(action_type='CALL').count()
    
    # 4. Calculate Views
    total_views = CarView.objects.filter(car__dealer=dealer, timestamp__gte=start_of_month).count()
    
    # 5. --- NEW ROI & INVENTORY METRICS ---
    
    # 5a. Cost Per Lead (CPL)
    plan_cost = 0
    if profile.plan_type == 'LITE': plan_cost = 5000
    elif profile.plan_type == 'PRO': plan_cost = 12000
    elif profile.plan_type == 'STARTER': plan_cost = 1500
    
    cpl = 0
    if total_leads > 0:
        cpl = int(plan_cost / total_leads)
        
    # 5b. Total Asset Valuation (Available Stock)
    inventory_value = cars.filter(status='AVAILABLE').aggregate(Sum('price'))['price__sum'] or 0
    
    # 5c. Sold Count
    sold_count = cars.filter(status='SOLD').count()
    
    # 5d. Stale Stock (Inventory sitting for > 60 days)
    sixty_days_ago = today - timedelta(days=60)
    stale_stock_count = cars.filter(status='AVAILABLE', created_at__lte=sixty_days_ago).count()

    # 6. Top 5 Performing Cars (Annotated with views)
    top_cars = cars.filter(status='AVAILABLE').annotate(num_views=Count('views')).order_by('-num_views')[:5]
    
    # 7. Context Data
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
        # New Metrics
        'cpl': cpl,
        'inventory_value': inventory_value,
        'sold_count': sold_count,
        'stale_stock_count': stale_stock_count
    }
    
    # 8. Generate PDF
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
    
    # --- LOGIC UPDATE: Enforce Car Limit from PLAN_LIMITS ---
    user_plan = PLAN_LIMITS.get(profile.plan_type, PLAN_LIMITS['STARTER'])
    if car_count >= user_plan['cars']:
        messages.warning(request, f"Plan limit reached ({user_plan['cars']} cars). Upgrade to add more.")
        return redirect('dealer_dashboard')

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            
            # --- START DUPLICATE CHECK ---
            
            # 1. Get cleaned data from form
            reg_number = form.cleaned_data.get('registration_number')
            make = form.cleaned_data.get('make')
            model = form.cleaned_data.get('model')
            year = form.cleaned_data.get('year')
            
            duplicate_found = False
            
            # 2. Check by Registration Number (If provided in form)
            if reg_number:
                clean_reg = str(reg_number).strip().replace(" ", "").upper()
                if Car.objects.filter(dealer=request.user, registration_number__iexact=clean_reg, status='AVAILABLE').exists():
                    messages.error(request, f"Duplicate: You already have a car with registration {reg_number} listed as available.")
                    duplicate_found = True

            # 3. Check by Make/Model/Year (Fallback)
            if not duplicate_found:
                if Car.objects.filter(dealer=request.user, make=make, model=model, year=year, status='AVAILABLE').exists():
                    messages.error(request, f"Duplicate: You already have a {year} {make} {model} listed. Please check your inventory.")
                    duplicate_found = True

            # 4. If duplicate found, return form with errors
            if duplicate_found:
                return render(request, 'dealer/add_car.html', {'form': form})

            # --- END DUPLICATE CHECK ---

            car = form.save(commit=False)
            car.dealer = request.user 
            car.status = 'AVAILABLE'
            car.save()
            
            # --- LOGIC UPDATE: Enforce Image Limit ---
            image_limit = user_plan['images']
            raw_images = request.FILES.getlist('image') 
            
            # Slice the list to the allowed limit (Discard excess images)
            images_to_save = raw_images[:image_limit]
            
            for index, img in enumerate(images_to_save):
                is_main = (index == 0)
                CarImage.objects.create(car=car, image=img, is_main=is_main)

            # Show warning if user tried to upload too many
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
            
            # --- LOGIC UPDATE: Enforce Image Limit on Edit ---
            user_plan = PLAN_LIMITS.get(profile.plan_type, PLAN_LIMITS['STARTER'])
            image_limit = user_plan['images']
            current_count = car.images.count()
            
            # Calculate remaining slots
            slots_left = image_limit - current_count
            
            new_images = request.FILES.getlist('image')
            
            if new_images:
                if slots_left > 0:
                    # Take only as many as fit
                    accepted_images = new_images[:slots_left]
                    
                    for img in accepted_images:
                        # If car has no images, make the first new one the main image
                        has_main = car.images.filter(is_main=True).exists()
                        is_first_new = (img == accepted_images[0] and not has_main)
                        CarImage.objects.create(car=car, image=img, is_main=is_first_new)
                    
                    # Feedback
                    if len(new_images) > slots_left:
                        messages.warning(request, f"Added {slots_left} photos. {len(new_images) - slots_left} were skipped (Limit: {image_limit} photos).")
                    else:
                        messages.success(request, f"Changes saved! {len(accepted_images)} new photo(s) added.")
                else:
                    messages.error(request, f"Cannot add photos. You have reached your limit of {image_limit} images for this car.")
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

# --- SET MAIN IMAGE VIEW ---
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

# --- NEW: DELETE IMAGE VIEW ---
@login_required
def delete_car_image(request, image_id):
    # 1. Get the image safely
    image = get_object_or_404(CarImage, id=image_id)
    
    # 2. Security: Ensure the logged-in user owns the car
    if image.car.dealer != request.user:
        messages.error(request, "You do not have permission to delete this image.")
        return redirect('dealer_dashboard')

    car_id = image.car.id
    was_main = image.is_main
    
    # 3. Delete the image
    image.delete()
    
    # 4. If the deleted image was the 'Main' image, assign a new one
    if was_main:
        remaining_images = CarImage.objects.filter(car_id=car_id)
        if remaining_images.exists():
            new_main = remaining_images.first()
            new_main.is_main = True
            new_main.save()
            messages.info(request, "Main image deleted. A new main image was automatically assigned.")
        else:
            messages.warning(request, "You deleted the main image. Please upload a new one.")
    else:
        messages.success(request, "Image deleted successfully.")
    
    # 5. Redirect back to the edit page
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

# --- SUPER ADMIN DASHBOARD ---

@staff_member_required
def platform_dashboard(request):
    """
    The 'God View' for the SaaS Founder.
    Tracks all dealers, system-wide inventory, and platform health.
    """
    # 1. Platform-Wide Metrics
    total_dealers = User.objects.filter(dealer_profile__isnull=False).count()
    total_cars = Car.objects.count()
    total_leads = Lead.objects.count()
    
    # 2. Financial/Plan Metrics
    starter_users = DealerProfile.objects.filter(plan_type='STARTER').count()
    lite_users = DealerProfile.objects.filter(plan_type='LITE').count()
    pro_users = DealerProfile.objects.filter(plan_type='PRO').count()
    
    # Estimate Monthly Recurring Revenue (MRR)
    mrr = (lite_users * 5000) + (pro_users * 12000)

    # 3. The "Yards" List - Fetches every yard, even newly added ones
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