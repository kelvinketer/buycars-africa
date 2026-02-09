from django.db import models
from django.conf import settings
from PIL import Image  # Requires: pip install Pillow
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import intcomma

class Car(models.Model):
    # --- GLOBAL DROPDOWN CHOICES (SIMPLIFIED FOR KENYA) ---
    
    # --- DRIVE TYPE (2WD vs 4WD) - Kept visible ---
    DRIVE_TYPE_CHOICES = [
        ('2WD', '2WD (Two Wheel Drive)'),
        ('4WD', '4WD (Four Wheel Drive)'),
        ('AWD', 'AWD (All Wheel Drive)'),
    ]

    # --- EXISTING DROPDOWN CHOICES ---
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('SOLD', 'Sold'),
        ('RESERVED', 'Reserved'),
        ('HIDDEN', 'Hidden (Plan Expired)'), 
        ('AUCTION', 'Live Auction'), # New status for Auction logic
    )
    
    CONDITION_CHOICES = [
        ('NEW', 'Brand New'),
        ('FOREIGN', 'Foreign Used'),
        ('LOCAL', 'Local Used'),
    ]
    
    TRANSMISSION_CHOICES = [
        ('Automatic', 'Automatic'),
        ('Manual', 'Manual'),
        ('CVT', 'CVT'),
    ]
    
    FUEL_CHOICES = [
        ('Petrol', 'Petrol'),
        ('Diesel', 'Diesel'),
        ('Hybrid', 'Hybrid'),
        ('Electric', 'Electric'),
    ]
    
    BODY_TYPE_CHOICES = [
        ('SUV', 'SUV'),
        ('Sedan', 'Sedan'),
        ('Hatchback', 'Hatchback'),
        ('Pickup', 'Pickup'),
        ('Coupe', 'Coupe'),
        ('Bus', 'Bus/Van'),
        ('Truck', 'Truck'),
        ('Convertible', 'Convertible'),
        ('Wagon', 'Station Wagon'),
    ]

    # --- LISTING TYPE FOR RENTALS ---
    LISTING_TYPE_CHOICES = [
        ('SALE', 'For Sale'),
        ('RENT', 'For Hire'),
        ('BOTH', 'For Sale & Hire'),
    ]

    CITY_CHOICES = [
            ('Nairobi', 'Nairobi'),
            ('Mombasa', 'Mombasa'),
            ('Kisumu', 'Kisumu'),
            ('Nakuru', 'Nakuru'),
            ('Eldoret', 'Eldoret'),
            ('Kiambu', 'Kiambu'),
            ('Thika', 'Thika'),
            ('Naivasha', 'Naivasha'),
    ]

    # --- DATABASE FIELDS ---
    dealer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cars')
    
    registration_number = models.CharField(max_length=20, blank=True, null=True, help_text="e.g. KDA 123X (Hidden from public)")

    make = models.CharField(max_length=50) 
    model = models.CharField(max_length=50) 
    year = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    
    country = models.CharField(max_length=50, default='KE', choices=[('KE', 'Kenya')], editable=False)
    city = models.CharField(max_length=100, default='Nairobi', choices=CITY_CHOICES, help_text="City or Town")
    listing_currency = models.CharField(max_length=10, default='KES', editable=False)
    drive_side = models.CharField(max_length=50, default='RHD', choices=[('RHD', 'Right Hand Drive')], editable=False)

    location = models.CharField(max_length=100, default='Nairobi')

    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES, default='SALE')
    rent_price_per_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_hire_days = models.PositiveIntegerField(default=1)

    is_available_for_rent = models.BooleanField(default=True)
    mileage = models.IntegerField(default=0, help_text="Mileage in km")
    engine_cc = models.IntegerField(help_text="Engine cc (e.g. 2000)", null=True, blank=True)
    color = models.CharField(max_length=50, default='White')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='FOREIGN')
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='Automatic')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='Petrol')
    body_type = models.CharField(max_length=20, choices=BODY_TYPE_CHOICES, default='SUV')
    drive_type = models.CharField(max_length=10, choices=DRIVE_TYPE_CHOICES, default='2WD')

    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.make:
            self.make = self.make.strip().title()
            if self.make.lower() == 'bmw': self.make = 'BMW'
        if self.model:
            self.model = self.model.strip().title()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.year} {self.make} {self.model} - {self.city}, {self.country}"

class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='car_images/')
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.image:
            try:
                img = Image.open(self.image)
                if img.mode != 'RGB': img = img.convert('RGB')
                if img.width > 1200:
                    output_size = (1200, (1200 * img.height) // img.width)
                    img.thumbnail(output_size)
                output = BytesIO()
                img.save(output, format='JPEG', quality=75, optimize=True)
                output.seek(0)
                new_name = f"{self.image.name.split('.')[0]}.jpg"
                self.image = InMemoryUploadedFile(output, 'ImageField', new_name, 'image/jpeg', sys.getsizeof(output), None)
            except Exception as e: print(f"Image compression failed: {e}")
        super().save(*args, **kwargs)

# --- ANALYTICS, BOOKING, & MESSAGING (KEEPING EXISTING) ---
class Booking(models.Model):
    STATUS_CHOICES = (('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('PAID', 'Paid'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'), ('REJECTED', 'Rejected'),)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='bookings')
    renter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rentals')
    start_date, end_date = models.DateField(), models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    message, created_at, updated_at = models.TextField(blank=True, null=True), models.DateTimeField(auto_now_add=True), models.DateTimeField(auto_now=True)

class CarView(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class Lead(models.Model):
    ACTION_CHOICES = [('CALL', 'Phone Call'), ('WHATSAPP', 'WhatsApp Message')]
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='leads')
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp, user, ip_address = models.DateTimeField(auto_now_add=True), models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True), models.GenericIPAddressField(null=True, blank=True)

class SearchTerm(models.Model):
    term, count, last_searched = models.CharField(max_length=100, unique=True), models.IntegerField(default=1), models.DateTimeField(auto_now=True)

class Conversation(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='conversations')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer_conversations')
    dealer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dealer_conversations')
    created_at, updated_at = models.DateTimeField(auto_now_add=True), models.DateTimeField(auto_now=True)
    class Meta: unique_together = ['car', 'buyer']

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender, content, is_read, timestamp = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE), models.TextField(), models.BooleanField(default=False), models.DateTimeField(auto_now_add=True)

# --- SOCIAL FEATURES (KEEPING EXISTING) ---
class DealerFollow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    dealer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ('follower', 'dealer')

class CarLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ('user', 'car')

# ========================================================
#             BIDDING WAR: AUCTION & BID MODELS
# ========================================================

class Auction(models.Model):
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name='auction')
    start_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_highest_bid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Auction for {self.car.make} {self.car.model}"

    @property
    def time_remaining(self):
        now = timezone.now()
        if now >= self.end_time: return "EXPIRED"
        return self.end_time - now

class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-amount']

    def __str__(self):
        return f"{self.bidder.username} bid KES {self.amount}"
    