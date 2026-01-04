from django.db import models
from django.conf import settings
from cars.models import CarBooking  # <--- Import this to link payments to bookings

class Payment(models.Model):
    # 1. Define the Plans here (only for dealer subscriptions)
    PLAN_CHOICES = [
        ('STARTER', 'Starter Plan (KES 1,500)'),
        ('LITE', 'Lite Plan (KES 5,000)'),
        ('PRO', 'Pro Plan (KES 12,000)'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payments')
    
    # 2. NEW: Link to a Booking (Nullable, because Plan payments won't have this)
    booking = models.ForeignKey(CarBooking, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')

    # 3. Transaction Details
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # 4. M-Pesa Identifiers
    checkout_request_id = models.CharField(max_length=100, unique=True)
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True) 
    mpesa_receipt_number = models.CharField(max_length=30, null=True, blank=True)
    
    # 5. Logic Fields
    # We make plan_type optional now, because booking payments don't need it
    plan_type = models.CharField(max_length=10, choices=PLAN_CHOICES, null=True, blank=True) 
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    description = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.plan_type:
            return f"Subscription: {self.user} - {self.plan_type} - {self.status}"
        elif self.booking:
            return f"Booking: {self.user} - Car #{self.booking.car.id} - {self.status}"
        return f"Payment: {self.user} - {self.amount}"

    class Meta:
        ordering = ['-created_at']