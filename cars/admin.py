from django.contrib import admin
from .models import Car, CarImage, CarLead

class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    inlines = [CarImageInline]
    # Added 'is_featured' so you can see it in the table
    list_display = ('id', 'make', 'model', 'year', 'price', 'status', 'dealer', 'is_featured')
    
    # This allows you to toggle "Featured" status directly from the list view!
    list_editable = ('status', 'is_featured')
    
    list_filter = ('status', 'is_featured', 'make', 'transmission')
    search_fields = ('make', 'model', 'dealer__username')

@admin.register(CarLead)
class CarLeadAdmin(admin.ModelAdmin):
    list_display = ('action', 'car', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('car__make', 'car__model')
    readonly_fields = ('timestamp', 'ip_address', 'action', 'car')