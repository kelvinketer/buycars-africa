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
    # --- UPDATED: 3-Tier Pricing Model ---
    PLAN_CHOICES = [
        ('FREE', 'Free (Inactive)'),
        ('STARTER', 'Starter (5 Cars)'), # KES 1,500
        ('LITE', 'Lite (15 Cars)'),      # KES 5,000
        ('PRO', 'Pro (50 Cars)'),        # KES 12,000
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
    subscription_expiry = models.DateTimeField(null=True, blank=True) # Tracks when plan expires

    def __str__(self):
        return self.business_name

    @property
    def is_plan_active(self):
        """Check if the paid plan (STARTER, LITE, PRO) is still valid"""
        if self.plan_type == 'FREE':
            return False # Free is now considered inactive/expired
            
        # If they are on a paid plan, check the date
        if self.subscription_expiry and self.subscription_expiry > timezone.now():
            return True
        return False

    @property
    def plan_limits(self):
        """Return limits dictionary based on the current plan"""
        # Define limits for each tier
        LIMITS = {
            'FREE': {'cars': 0, 'featured': 0, 'leads': 0},
            'STARTER': {'cars': 5, 'featured': 0, 'leads': 7},
            'LITE': {'cars': 15, 'featured': 2, 'leads': 16},
            'PRO': {'cars': 50, 'featured': 5, 'leads': 30},
        }
        
        # If plan is expired or Free, return restricted limits
        if not self.is_plan_active:
            return LIMITS['FREE']
            
        return LIMITS.get(self.plan_type, LIMITS['FREE'])

    def can_add_car(self):
        """
        Returns True if the dealer can add more cars based on their plan limits.
        """
        limit = self.plan_limits['cars']
        
        # Access cars via related_name 'cars' (defined in Car model)
        if hasattr(self.user, 'cars'):
            current_count = self.user.cars.count()
        else:
            current_count = self.user.car_set.count()

        return current_count < limit

    def can_feature_car(self):
        """
        Returns True if the dealer has remaining featured listing slots.
        """
        limit = self.plan_limits['featured']
        
        # Count currently featured cars (requires is_featured boolean on Car model)
        if hasattr(self.user, 'cars'):
            featured_count = self.user.cars.filter(is_featured=True).count()
        else:
            # Fallback if related_name isn't set, though 'cars' is standard
            try:
                featured_count = self.user.car_set.filter(is_featured=True).count()
            except:
                featured_count = 0
            
        return featured_count < limit