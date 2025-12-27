from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    """
    Custom User Model to handle different roles (Admin, Dealer, Buyer).
    """
    ROLE_CHOICES = (
        ('ADMIN', 'Super Admin'),
        ('DEALER', 'Car Yard/Dealer'),
        ('BUYER', 'Regular Buyer'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='BUYER')
    
    # Critical contact info for WhatsApp/Calls
    phone_number = models.CharField(
        max_length=15, 
        unique=True, 
        null=True, 
        blank=True,
        help_text="Format: 254712345678"
    )
    
    # Trust badge for the website
    is_verified = models.BooleanField(default=False) 

    def __str__(self):
        return self.username

class DealerProfile(models.Model):
    """
    Extra profile information for Car Yards (Logos, Locations, Stats).
    """
    # --- UPDATED: 3-Tier Subscription Plan ---
    PLAN_CHOICES = [
        ('FREE', 'Free Plan (3 Cars)'),
        ('LITE', 'Biashara Lite (15 Cars)'), # KES 1,000
        ('PRO', 'Showroom Pro (Unlimited)'), # KES 2,500
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dealer_profile')
    business_name = models.CharField(max_length=100)
    
    # Location Logic
    CITY_CHOICES = (
        ('NBI', 'Nairobi'),
        ('MSA', 'Mombasa'),
        ('KSM', 'Kisumu'),
        ('ELD', 'Eldoret'),
        ('NKR', 'Nakuru'),
        ('OTH', 'Other'),
    )
    city = models.CharField(max_length=3, choices=CITY_CHOICES, default='NBI')
    physical_address = models.TextField(blank=True, null=True)
    
    # Contact Override (Optional: if business phone differs from login phone)
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Business contact number")

    logo = models.ImageField(upload_to='dealer_logos/', blank=True, null=True)
    website_link = models.URLField(blank=True, null=True)
    
    # Stats for the Dashboard
    total_views = models.IntegerField(default=0)
    
    # --- SUBSCRIPTION FIELDS ---
    plan_type = models.CharField(max_length=10, choices=PLAN_CHOICES, default='FREE')
    subscription_expiry = models.DateTimeField(null=True, blank=True) # Tracks when Pro/Lite expires

    def __str__(self):
        return self.business_name

    def is_plan_active(self):
        """Check if the paid plan (LITE or PRO) is still valid"""
        if self.plan_type == 'FREE':
            return True
        # If they are on a paid plan, check the date
        if self.subscription_expiry and self.subscription_expiry > timezone.now():
            return True
        return False

    def can_add_car(self):
        """
        Returns True if the dealer can add more cars based on their plan.
        FREE: 3 Cars
        LITE: 15 Cars
        PRO: Unlimited
        """
        # 1. Determine effective plan (Downgrade to FREE if expired)
        current_plan = self.plan_type
        if not self.is_plan_active():
            current_plan = 'FREE'

        # 2. Check Limits
        if current_plan == 'PRO':
            return True # Unlimited
            
        # We access the user's cars via the related_name 'cars' (set in Car model)
        # If 'cars' related_name is missing, we fallback to 'car_set'
        if hasattr(self.user, 'cars'):
            current_count = self.user.cars.count()
        else:
            current_count = self.user.car_set.count()

        if current_plan == 'LITE':
            return current_count < 15
        
        # Default FREE Limit
        return current_count < 3