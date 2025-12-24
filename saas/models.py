from django.db import models
from django.conf import settings

class SubscriptionPlan(models.Model):
    """
    Defines the 3 Tiers: Starter, Standard, Premium
    """
    name = models.CharField(max_length=50) # e.g., "Standard (Dealer)"
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    
    # The Limits
    max_cars = models.IntegerField() 
    max_photos_per_car = models.IntegerField() 
    allow_video = models.BooleanField(default=False)
    is_featured_allowed = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class DealerSubscription(models.Model):
    """
    Tracks who has paid for what.
    """
    dealer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField() 
    is_active = models.BooleanField(default=True)
    
    mpesa_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.dealer.username} - {self.plan.name}"