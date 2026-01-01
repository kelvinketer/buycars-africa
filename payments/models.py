from django.db import models
from django.conf import settings

class Payment(models.Model):
    # 1. Define the Plans here so we know what is being bought
    PLAN_CHOICES = [
        ('LITE', 'Lite Plan (KES 5,000)'),
        ('PRO', 'Pro Plan (KES 12,000)'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payments')
    
    # 2. Transaction Details
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # 3. M-Pesa Identifiers (Crucial for the Callback)
    checkout_request_id = models.CharField(max_length=100, unique=True) # The unique ID M-Pesa gives us
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True) 
    mpesa_receipt_number = models.CharField(max_length=30, null=True, blank=True) # The code (e.g. QKH...)
    
    # 4. Logic Fields
    plan_type = models.CharField(max_length=10, choices=PLAN_CHOICES) # <--- CRITICAL: Tells us what to upgrade them to
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    description = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.plan_type} - {self.status}"

    class Meta:
        ordering = ['-created_at']