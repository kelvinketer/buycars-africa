from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from django.conf import settings
from users.models import DealerProfile
from cars.models import Car, CarView, Lead

class Command(BaseCommand):
    help = 'Sends weekly performance summary emails to dealers'

    def handle(self, *args, **kwargs):
        # 1. Define the time range (Last 7 Days)
        today = timezone.now()
        seven_days_ago = today - timedelta(days=7)
        
        self.stdout.write(f"Preparing weekly reports for week: {seven_days_ago.date()} to {today.date()}...")

        # 2. Get active dealers with valid emails
        dealers = DealerProfile.objects.select_related('user').filter(user__email__isnull=False)

        count_sent = 0

        for profile in dealers:
            user = profile.user
            email = user.email
            
            if not email:
                continue

            # 3. Calculate Stats for THIS Dealer's Cars (Last 7 Days)
            
            # A. Total Views (Traffic)
            total_views = CarView.objects.filter(
                car__dealer=user,
                timestamp__gte=seven_days_ago
            ).count()

            # B. Total Leads (Action)
            total_leads = Lead.objects.filter(
                car__dealer=user,
                timestamp__gte=seven_days_ago
            ).count()

            # Skip sending if they have absolutely zero activity and 0 cars
            # (Prevents spamming users who abandoned the platform years ago)
            active_cars_count = Car.objects.filter(dealer=user, status='AVAILABLE').count()
            if active_cars_count == 0 and total_views == 0:
                continue 

            # 4. Find their "Star Car" (Most viewed this week)
            # We annotate views specifically from the last 7 days to find the current trend
            top_car = Car.objects.filter(dealer=user, status='AVAILABLE')\
                .annotate(recent_views=Count('views', filter=Q(views__timestamp__gte=seven_days_ago)))\
                .order_by('-recent_views').first()
            
            top_car_name = f"{top_car.year} {top_car.make} {top_car.model}" if top_car else "your inventory"

            # 5. Dynamic Email Subject
            if total_leads > 0:
                subject = f"🚀 You got {total_leads} new leads this week!"
            else:
                subject = f"📈 Your Weekly Performance Report - BuyCars Africa"

            # 6. Construct the Email Body
            message = f"""
Hi {profile.business_name},

Here is how your yard performed this week on BuyCars Africa:

👀 {total_views} Buyers viewed your cars
🔥 {total_leads} Interested buyers clicked Call/WhatsApp
🏆 Top Performer: {top_car_name}

"""
            # Add dynamic advice based on performance
            if total_leads > 0:
                message += f"Good job! Buyers are interested. Make sure you pick up calls and reply to WhatsApp messages quickly to close these deals.\n"
            else:
                message += f"Want more leads? Listings with clear prices and 5+ photos get 3x more calls. Consider updating your photos for {top_car_name}.\n"

            message += """
Check your full dashboard here:
https://buycars-africa.onrender.com/dashboard/

Happy Selling,
The BuyCars Team
"""

            # 7. Send the Email
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                count_sent += 1
                self.stdout.write(f"Sent report to {profile.business_name} ({email})")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send to {email}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Done. Sent {count_sent} weekly reports."))