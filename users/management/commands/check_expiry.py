from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from users.models import DealerProfile
from cars.models import Car

# Define the limit for the free tier (Centralized logic)
STARTER_CAR_LIMIT = 5

class Command(BaseCommand):
    help = 'Checks for expired subscriptions and downgrades dealers to STARTER plan'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        
        # 1. Find dealers who are expired but still on paid plans
        expired_dealers = DealerProfile.objects.filter(
            subscription_expiry__lt=today,
            plan_type__in=['LITE', 'PRO']
        )

        if not expired_dealers.exists():
            self.stdout.write(self.style.SUCCESS('No expired subscriptions found today.'))
            return

        self.stdout.write(self.style.WARNING(f'Found {expired_dealers.count()} expired dealers. Processing...'))

        for profile in expired_dealers:
            old_plan = profile.plan_type
            
            # --- ACTION 1: DOWNGRADE PLAN ---
            profile.plan_type = 'STARTER'
            profile.subscription_expiry = None # Clear the date so they don't get flagged again
            profile.save()
            
            self.stdout.write(f"Downgraded {profile.business_name} ({profile.user.username}) from {old_plan} to STARTER.")

            # --- ACTION 2: ENFORCE INVENTORY LIMITS ---
            # Get all their currently AVAILABLE cars, ordered by newest first
            my_cars = Car.objects.filter(
                dealer=profile.user, 
                status='AVAILABLE'
            ).order_by('-created_at')
            
            total_active = my_cars.count()

            if total_active > STARTER_CAR_LIMIT:
                # Calculate how many to hide
                excess_count = total_active - STARTER_CAR_LIMIT
                
                # Identify the oldest cars (the ones exceeding the limit)
                # We slice from the limit onwards [5:]
                cars_to_hide = my_cars[STARTER_CAR_LIMIT:]
                
                # Bulk update them to a new status 'HIDDEN' or just 'DRAFT'
                # Since we don't have a HIDDEN status yet, we will use a custom status
                # ensuring your frontend filters exclude it.
                count_hidden = 0
                for car in cars_to_hide:
                    car.status = 'HIDDEN' # Ensure your views filter exclude 'HIDDEN'
                    car.save()
                    count_hidden += 1
                
                self.stdout.write(self.style.ERROR(f"   - Locked {count_hidden} excess vehicles."))
            else:
                self.stdout.write(self.style.SUCCESS(f"   - Inventory within limits ({total_active}/{STARTER_CAR_LIMIT}). No locking needed."))

        self.stdout.write(self.style.SUCCESS('Subscription check complete.'))