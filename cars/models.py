from django.db import models
from django.conf import settings

class Car(models.Model):
    # --- DROPDOWN CHOICES ---
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('SOLD', 'Sold'),
        ('RESERVED', 'Reserved'),
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
    
    make = models.CharField(max_length=50) 
    model = models.CharField(max_length=50) 
    year = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Renamed from 'mileage_km' to 'mileage' to match your Form
    mileage = models.IntegerField(default=0, help_text="Mileage in km")
    
    # New Fields required by the Form
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

# --- NEW: ANALYTICS MODEL (Step 1 of Lead Tracking) ---
class CarAnalytics(models.Model):
    ACTION_CHOICES = [
        ('VIEW', 'Page View'),
        ('WHATSAPP', 'WhatsApp Click'),
        ('CALL', 'Phone Call'),
    ]
    
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='analytics')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Track IP to eventually filter out spam/duplicate clicks
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # --- ADDED TO FORCE NEW MIGRATION FILE ---
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Car Leads"

    def __str__(self):
        return f"{self.action} on {self.car} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"