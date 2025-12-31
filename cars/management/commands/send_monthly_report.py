from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from cars.models import Car, Lead, CarView
from users.models import DealerProfile
import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Sends monthly performance reports to all dealers'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting Monthly Report Job...")

        # 1. Calculate Date Range (Last Month)
        today = timezone.now()
        first_day_this_month = today.replace(day=1)
        last_day_prev_month = first_day_this_month - datetime.timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)
        
        # Format month name for email (e.g., "December 2025")
        month_name = first_day_prev_month.strftime("%B %Y")
        
        # 2. Get all dealers with an active profile
        dealers = User.objects.filter(dealer_profile__isnull=False)

        for dealer in dealers:
            profile = dealer.dealer_profile
            
            # --- AGGREGATE STATS ---
            
            # Get cars owned by dealer
            dealer_cars = Car.objects.filter(dealer=dealer)
            
            # Count Leads in previous month
            leads_count = Lead.objects.filter(
                car__dealer=dealer,
                timestamp__gte=first_day_prev_month,
                timestamp__lte=last_day_prev_month
            ).count()
            
            # Count Views in previous month
            views_count = CarView.objects.filter(
                car__dealer=dealer,
                timestamp__gte=first_day_prev_month,
                timestamp__lte=last_day_prev_month
            ).count()
            
            # Skip sending if they have absolutely 0 activity (optional, but good to avoid "0" spam)
            if leads_count == 0 and views_count == 0:
                continue

            # Identify Hot Car
            hot_car_obj = dealer_cars.annotate(
                month_views=Count('views', filter=Q(views__timestamp__gte=first_day_prev_month, views__timestamp__lte=last_day_prev_month))
            ).order_by('-month_views').first()
            
            hot_car_name = f"{hot_car_obj.year} {hot_car_obj.make} {hot_car_obj.model}" if hot_car_obj else None
            hot_car_views = hot_car_obj.month_views if hot_car_obj else 0

            # Calculate ROI
            plan_cost = 0
            if profile.plan_type == 'LITE': plan_cost = 5000
            elif profile.plan_type == 'PRO': plan_cost = 12000
            elif profile.plan_type == 'STARTER': plan_cost = 1500
            
            cpl = 0
            roi_multiplier = 1
            if leads_count > 0 and plan_cost > 0:
                cpl = int(plan_cost / leads_count)
                # Compare to avg FB lead cost (approx 400 KES)
                roi_multiplier = round(400 / cpl, 1) if cpl < 400 else 1

            # --- PREPARE EMAIL ---
            context = {
                'dealer_name': profile.business_name or dealer.username,
                'month_name': month_name,
                'total_leads': leads_count,
                'total_views': views_count,
                'active_cars': dealer_cars.filter(status='AVAILABLE').count(),
                'hot_car': hot_car_name,
                'hot_car_views': hot_car_views,
                'cpl': cpl,
                'roi_multiplier': roi_multiplier
            }

            html_content = render_to_string('emails/monthly_report.html', context)
            text_content = strip_tags(html_content)

            # --- SEND EMAIL ---
            try:
                msg = EmailMultiAlternatives(
                    subject=f"Your {month_name} Performance Report 📈",
                    body=text_content,
                    from_email='BuyCars Africa <noreply@buycars.africa>',
                    to=[dealer.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                self.stdout.write(self.style.SUCCESS(f"Sent report to {dealer.email}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send to {dealer.email}: {e}"))

        self.stdout.write(self.style.SUCCESS("Monthly Report Job Completed!"))