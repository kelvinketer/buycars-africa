from django.contrib import admin
from .models import Car, CarImage, CarAnalytics # <--- Added CarAnalytics import

class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    inlines = [CarImageInline]
    list_display = ('make', 'model', 'year', 'price', 'status', 'dealer')
    list_filter = ('status', 'make', 'transmission')
    search_fields = ('make', 'model', 'dealer__username')

# --- NEW: REGISTER ANALYTICS ---
@admin.register(CarAnalytics)
class CarAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('action', 'car', 'timestamp', 'ip_address') # Columns to show
    list_filter = ('action', 'timestamp') # Sidebar filters
    search_fields = ('car__make', 'car__model') # Search bar logic
    readonly_fields = ('timestamp', 'ip_address', 'action', 'car') # Prevent editing history