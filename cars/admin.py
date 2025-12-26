from django.contrib import admin
from .models import Car, CarImage, CarLead  # <--- Changed to CarLead

class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    inlines = [CarImageInline]
    list_display = ('make', 'model', 'year', 'price', 'status', 'dealer')
    list_filter = ('status', 'make', 'transmission')
    search_fields = ('make', 'model', 'dealer__username')

# --- UPDATED: REGISTER CAR LEAD ---
@admin.register(CarLead)
class CarLeadAdmin(admin.ModelAdmin):
    list_display = ('action', 'car', 'timestamp', 'ip_address') 
    list_filter = ('action', 'timestamp') 
    search_fields = ('car__make', 'car__model') 
    readonly_fields = ('timestamp', 'ip_address', 'action', 'car')