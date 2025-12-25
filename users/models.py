from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

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
    
    logo = models.ImageField(upload_to='dealer_logos/', blank=True, null=True)
    website_link = models.URLField(blank=True, null=True)
    
    # Stats for the Dashboard
    total_views = models.IntegerField(default=0)
    
    def __str__(self):
        return self.business_name