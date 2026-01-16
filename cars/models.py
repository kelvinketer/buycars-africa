from django.db import models
from django.conf import settings
from PIL import Image  # Requires: pip install Pillow
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import intcomma

class Car(models.Model):
    # --- GLOBAL DROPDOWN CHOICES (PAN-AFRICAN EXPANSION) ---
    COUNTRY_CHOICES = [
        # East Africa (EAC & Horn)
        ('KE', 'Kenya'),
        ('UG', 'Uganda'),
        ('TZ', 'Tanzania'),
        ('RW', 'Rwanda'),
        ('SS', 'South Sudan'),
        ('ET', 'Ethiopia'),

        # West Africa (The Giants)
        ('NG', 'Nigeria'),
        ('GH', 'Ghana'),

        # North Africa
        ('EG', 'Egypt'),

        # Southern Africa
        ('ZA', 'South Africa'),
        ('NA', 'Namibia'),
        ('AO', 'Angola'),

        # Key Import Sources
        ('GB', 'United Kingdom'),
        ('JP', 'Japan'),
        ('AE', 'United Arab Emirates'), # Dubai
    ]

    CURRENCY_CHOICES = [
        # East Africa
        ('KES', 'Kenyan Shilling (KES)'),
        ('UGX', 'Ugandan Shilling (UGX)'),
        ('TZS', 'Tanzanian Shilling (TZS)'),
        ('RWF', 'Rwandan Franc (RWF)'),
        ('ETB', 'Ethiopian Birr (ETB)'),

        # West Africa
        ('NGN', 'Nigerian Naira (NGN)'),
        ('GHS', 'Ghanaian Cedi (GHS)'),

        # North & South
        ('EGP', 'Egyptian Pound (EGP)'),
        ('ZAR', 'South African Rand (ZAR)'),
        ('NAD', 'Namibian Dollar (NAD)'),
        ('AOA', 'Angolan Kwanza (AOA)'),

        # International Trade
        ('USD', 'US Dollar (USD)'),
        ('GBP', 'British Pound (GBP)'),
        ('AED', 'UAE Dirham (AED)'),
        ('JPY', 'Japanese Yen (JPY)'),
    ]

    # --- NEW: DRIVE SIDE (Crucial for Cross-Border) ---
    DRIVE_SIDE_CHOICES = [
        ('RHD', 'Right-Hand Drive (RHD)'), # Kenya, SA, UK, Japan, Uganda, TZ
        ('LHD', 'Left-Hand Drive (LHD)'),  # Nigeria, Ghana, US, Europe, Ethiopia, Rwanda
    ]

    # --- EXISTING DROPDOWN CHOICES ---
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('SOLD', 'Sold'),
        ('RESERVED', 'Reserved'),
        ('HIDDEN', 'Hidden (Plan Expired)'), 
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

    # --- LISTING TYPE FOR RENTALS ---
    LISTING_TYPE_CHOICES = [
        ('SALE', 'For Sale'),
        ('RENT', 'For Hire'),
        ('BOTH', 'For Sale & Hire'),
    ]

    # --- DATABASE FIELDS ---
    dealer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cars')
    
    # Identify the car uniquely
    registration_number = models.CharField(max_length=20, blank=True, null=True, help_text="e.g. KDA 123X (Hidden from public)")

    make = models.CharField(max_length=50) 
    model = models.CharField(max_length=50) 
    year = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # === NEW GLOBAL FIELDS ===
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='KE', help_text="The country where this car is physically located.")
    city = models.CharField(max_length=100, default='Nairobi', help_text="City or Town (e.g., Nairobi, Lagos, Accra)")
    listing_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='KES', help_text="Currency for the listed price.")
    
    # New Field for Traffic Laws
    drive_side = models.CharField(
        max_length=3, 
        choices=DRIVE_SIDE_CHOICES, 
        default='RHD', 
        help_text="Select LHD for Nigeria/Ghana/Ethiopia. RHD for Kenya/SA/UK."
    )

    # Note: 'location' kept for legacy support/display
    location = models.CharField(max_length=100, default='Nairobi')

    # === RENTAL FIELDS ===
    listing_type = models.CharField(
        max_length=10, 
        choices=LISTING_TYPE_CHOICES, 
        default='SALE',
        help_text="Is this car for sale, for hire, or both?"
    )
    
    rent_price_per_day = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Cost per day in Listing Currency (only required if For Hire)"
    )
    
    min_hire_days = models.PositiveIntegerField(
        default=1, 
        help_text="Minimum number of days this car can be rented"
    )

    is_available_for_rent = models.BooleanField(default=True)
    # ==========================

    mileage = models.IntegerField(default=0, help_text="Mileage in km")
    
    engine_size = models.IntegerField(help_text="Engine cc", null=True, blank=True)
    color = models.CharField(max_length=50, default='White')
    
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='FOREIGN')
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='AUTOMATIC')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='PETROL')
    body_type = models.CharField(max_length=20, choices=BODY_TYPE_CHOICES, default='SUV')
    
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # --- AUTO-CLEANUP LOGIC ---
    def save(self, *args, **kwargs):
        """
        Intercepts the save process to standardize Make and Model names.
        """
        if self.make:
            self.make = self.make.strip().title()
            if self.make.lower() == 'bmw':
                self.make = 'BMW'

        if self.model:
            self.model = self.model.strip().title()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.year} {self.make} {self.model} - {self.city}, {self.country}"

class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='car_images/')
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.car.model}"

    def save(self, *args, **kwargs):
        if self.image:
            try:
                img = Image.open(self.image)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                if img.width > 1200:
                    output_size = (1200, (1200 * img.height) // img.width)
                    img.thumbnail(output_size)
                output = BytesIO()
                img.save(output, format='JPEG', quality=75, optimize=True)
                output.seek(0)
                new_name = f"{self.image.name.split('.')[0]}.jpg"
                self.image = InMemoryUploadedFile(
                    output, 
                    'ImageField', 
                    new_name, 
                    'image/jpeg', 
                    sys.getsizeof(output), 
                    None
                )
            except Exception as e:
                print(f"Image compression failed: {e}")

        super().save(*args, **kwargs)

# --- RENTAL BOOKING MODEL ---

class Booking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved (Awaiting Payment)'),
        ('PAID', 'Paid & Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
    )

    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='bookings')
    
    # --- REVERTED TO STANDARD: NO DB_COLUMN ---
    # This expects a column named 'renter_id' in the database.
    # We will create this column in the next step using the migration file.
    renter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rentals')
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking: {self.car.make} {self.car.model} - {self.renter.username}"

    @property
    def total_days(self):
        delta = self.end_date - self.start_date
        return delta.days + 1

# --- ANALYTICS MODELS ---

class CarView(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"View on {self.car} at {self.timestamp}"

class Lead(models.Model):
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

class SearchTerm(models.Model):
    term = models.CharField(max_length=100, unique=True)
    count = models.IntegerField(default=1)
    last_searched = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.term} ({self.count})"