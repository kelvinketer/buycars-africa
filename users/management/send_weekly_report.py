from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.conf import settings
from users.models import DealerProfile
from cars.models import Car, CarView, Lead

class Command(BaseCommand):
    help = 'Sends weekly performance summary emails to dealers (HTML Version)'

    def handle(self, *args, **kwargs):
        # 1. Define the time range (Last 7 Days)
        today = timezone.now()
        seven_days_ago = today - timedelta(days=7)
        
        self.stdout.write(f"Preparing weekly reports for: {seven_days_ago.date()} to {today.date()}...")

        # 2. Get active dealers with valid emails
        dealers = DealerProfile.objects.select_related('user').filter(user__email__isnull=False)

        count_sent = 0

        for profile in dealers:
            user = profile.user
            email = user.email
            
            if not email:
                continue

            # 3. Calculate Stats (Last 7 Days)
            
            # A. Traffic & Leads
            new_views = CarView.objects.filter(car__dealer=user, timestamp__gte=seven_days_ago).count()
            new_leads = Lead.objects.filter(car__dealer=user, timestamp__gte=seven_days_ago).count()

            # B. Inventory Health
            active_cars = Car.objects.filter(dealer=user, status='AVAILABLE').count()
            sold_cars = Car.objects.filter(dealer=user, status='SOLD').count()
            total_cars = Car.objects.filter(dealer=user).count()

            # SKIP LOGIC: Don't spam inactive users (0 cars, 0 views, 0 leads)
            if active_cars == 0 and new_views == 0 and new_leads == 0:
                continue 

            # 4. Find "Star Car" (Most viewed this week)
            top_car = Car.objects.filter(dealer=user, status='AVAILABLE')\
                .annotate(recent_views=Count('views', filter=Q(views__timestamp__gte=seven_days_ago)))\
                .order_by('-recent_views').first()
            
            # 5. Prepare Data for HTML Template
            context = {
                'business_name': profile.business_name,
                'start_date': seven_days_ago.strftime('%b %d'),
                'end_date': today.strftime('%b %d'),
                'new_leads': new_leads,
                'new_views': new_views,
                'active_cars': active_cars,
                'sold_cars': sold_cars,
                'total_cars': total_cars,
                'top_car': top_car,
            }

            # 6. Render the HTML
            # This looks for templates/emails/weekly_report.html
            html_content = render_to_string('emails/weekly_report.html', context)
            
            # Plain text fallback (for old email clients)
            text_content = f"""
            Hi {profile.business_name},
            Here is your weekly summary:
            - {new_views} Car Views
            - {new_leads} New Leads
            - {active_cars} Active Cars
            Login to your dashboard for full details: https://buycars-africa.onrender.com/dashboard/
            """

            # 7. Dynamic Subject Line
            if new_leads > 0:
                subject = f"🚀 You got {new_leads} new leads this week!"
            else:
                subject = f"📈 Your Weekly Performance Report - BuyCars.Africa"

            # 8. Send the Email
            try:
                msg = EmailMultiAlternatives(
                    subject, 
                    text_content, 
                    settings.DEFAULT_FROM_EMAIL, 
                    [email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                
                count_sent += 1
                self.stdout.write(f"✅ Sent to {profile.business_name} ({email})")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to send to {email}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Done. Sent {count_sent} weekly reports."))