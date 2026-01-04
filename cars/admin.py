from django.contrib import admin
from .models import Car, CarImage, CarView, Lead, CarBooking

class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    inlines = [CarImageInline]
    
    # 1. FIXED: Added 'is_available_for_rent' to this list
    list_display = (
        'id', 
        'make', 
        'model', 
        'year', 
        'listing_type',       
        'price',              
        'rent_price_per_day', 
        'is_available_for_rent', # <--- THIS WAS MISSING
        'status', 
        'dealer', 
        'is_featured'
    )
    
    # 2. This works now because the field is in the list above
    list_editable = ('status', 'is_featured', 'listing_type', 'is_available_for_rent')
    
    list_filter = ('listing_type', 'status', 'is_featured', 'make', 'transmission', 'is_available_for_rent')
    
    search_fields = ('make', 'model', 'dealer__username', 'registration_number')

    fieldsets = (
        ('Basic Info', {
            'fields': ('dealer', 'registration_number', 'make', 'model', 'year', 'condition', 'color', 'location')
        }),
        ('Listing Details', {
            'fields': ('listing_type', 'price', 'rent_price_per_day', 'min_hire_days', 'is_available_for_rent', 'status', 'is_featured')
        }),
        ('Specs', {
            'fields': ('mileage', 'engine_size', 'transmission', 'fuel_type', 'body_type')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )

@admin.register(CarBooking)
class CarBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'customer', 'start_date', 'end_date', 'total_cost', 'status')
    list_filter = ('status', 'start_date', 'created_at')
    search_fields = ('car__make', 'car__model', 'customer__username', 'customer__email')
    readonly_fields = ('created_at', 'updated_at')

# --- ANALYTICS ---

@admin.register(CarView)
class CarViewAdmin(admin.ModelAdmin):
    list_display = ('car', 'ip_address', 'timestamp')
    readonly_fields = ('timestamp',)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'car', 'timestamp', 'ip_address')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('car__make', 'car__model')
    readonly_fields = ('timestamp', 'ip_address', 'action_type', 'car')