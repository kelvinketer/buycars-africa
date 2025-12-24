from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    """
    Custom User Model to handle different roles.
    """
    ROLE_CHOICES = (
        ('ADMIN', 'Super Admin'),
        ('DEALER', 'Car Yard/Dealer'),
        ('BUYER', 'Regular Buyer'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='BUYER')
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False) # For trusted dealers

    def __str__(self):
        return self.username

class DealerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dealer_profile')
    business_name = models.CharField(max_length=100)
    
    # Location Logic for Pilot
    CITY_CHOICES = (
        ('NBI', 'Nairobi'),
        ('MSA', 'Mombasa'),
        ('OTH', 'Other'),
    )
    city = models.CharField(max_length=3, choices=CITY_CHOICES, default='NBI')
    physical_address = models.TextField()
    
    logo = models.ImageField(upload_to='dealer_logos/', blank=True, null=True)
    website_link = models.URLField(blank=True, null=True)
    
    total_views = models.IntegerField(default=0)
    
    def __str__(self):
        return self.business_name