from django.contrib import admin
from .models import Car, CarImage, CarView, Lead, Booking, SearchTerm

class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    inlines = [CarImageInline]
    
    list_display = (
        'id', 
        'make', 
        'model', 
        'year', 
        'listing_type',       
        'price',              
        'rent_price_per_day', 
        'is_available_for_rent',
        'status', 
        'dealer', 
        'is_featured'
    )
    
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

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Updated to match the new Booking model fields
    list_display = ('id', 'car', 'renter', 'start_date', 'end_date', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'start_date', 'created_at')
    search_fields = ('car__make', 'car__model', 'renter__username', 'renter__email')
    readonly_fields = ('total_price', 'created_at', 'updated_at')

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

@admin.register(SearchTerm)
class SearchTermAdmin(admin.ModelAdmin):
    list_display = ('term', 'count', 'last_searched')
    ordering = ('-count',)