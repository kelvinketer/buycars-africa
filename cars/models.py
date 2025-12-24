from django.db import models
from django.conf import settings

class Car(models.Model):
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('SOLD', 'Sold'),
        ('RESERVED', 'Reserved'),
    )
    
    # Link to the Dealer (User)
    dealer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cars')
    
    make = models.CharField(max_length=50) 
    model = models.CharField(max_length=50) 
    year = models.IntegerField()
    transmission = models.CharField(max_length=20, choices=(('AUTO', 'Automatic'), ('MANUAL', 'Manual')))
    fuel_type = models.CharField(max_length=20, choices=(('PETROL', 'Petrol'), ('DIESEL', 'Diesel'), ('HYBRID', 'Hybrid')))
    
    price = models.DecimalField(max_digits=12, decimal_places=2)
    mileage_km = models.IntegerField()
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