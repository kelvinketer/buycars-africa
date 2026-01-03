from django.db import models
from django.conf import settings

class Car(models.Model):
    # --- DROPDOWN CHOICES ---
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('SOLD', 'Sold'),
        ('RESERVED', 'Reserved'),
        ('HIDDEN', 'Hidden (Plan Expired)'), # <--- NEW: For the Subscription Enforcer
    )
    
    CONDITION_CHOICES = [
        ('NEW', 'Brand New'),
        ('FOREIGN', 'Foreign Used'),
        ('LOCAL', 'Local Used'),
    ]
    
    TRANSMISSION_CHOICES = [
        ('AUTOMATIC', 'Automatic'),
        ('MANUAL', 'Manual'),
        ('CVT', 'CVT'),
    ]
    
    FUEL_CHOICES = [
        ('PETROL', 'Petrol'),
        ('DIESEL', 'Diesel'),
        ('HYBRID', 'Hybrid'),
        ('ELECTRIC', 'Electric'),
    ]
    
    BODY_TYPE_CHOICES = [
        ('SUV', 'SUV'),
        ('SEDAN', 'Sedan'),
        ('HATCHBACK', 'Hatchback'),
        ('PICKUP', 'Pickup'),
        ('COUPE', 'Coupe'),
        ('BUS', 'Bus/Van'),
        ('TRUCK', 'Truck'),
        ('CONVERTIBLE', 'Convertible'),
    ]

    # --- DATABASE FIELDS ---
    dealer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cars')
    
    # Identify the car uniquely (Added for Duplicate Checks)
    registration_number = models.CharField(max_length=20, blank=True, null=True, help_text="e.g. KDA 123X (Hidden from public)")

    make = models.CharField(max_length=50) 
    model = models.CharField(max_length=50) 
    year = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    
    mileage = models.IntegerField(default=0, help_text="Mileage in km")
    
    engine_size = models.IntegerField(help_text="Engine cc", null=True, blank=True)
    color = models.CharField(max_length=50, default='White')
    location = models.CharField(max_length=100, default='Nairobi')
    
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='FOREIGN')
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='AUTOMATIC')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='PETROL')
    body_type = models.CharField(max_length=20, choices=BODY_TYPE_CHOICES, default='SUV')
    
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.year} {self.make} {self.model}"

class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='car_images/')
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.car.model}"

# --- ANALYTICS MODELS ---

class CarView(models.Model):
    """Tracks simple page views (Traffic)."""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"View on {self.car} at {self.timestamp}"

class Lead(models.Model):
    """Tracks valuable actions (Call/WhatsApp clicks)."""
    ACTION_CHOICES = [
        ('CALL', 'Phone Call'),
        ('WHATSAPP', 'WhatsApp Message'),
    ]
    
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='leads')
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_action_type_display()} for {self.car} at {self.timestamp}"

# --- SEARCH ANALYTICS ---
class SearchTerm(models.Model):
    term = models.CharField(max_length=100, unique=True)
    count = models.IntegerField(default=1)
    last_searched = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.term} ({self.count})"