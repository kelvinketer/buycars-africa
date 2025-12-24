from django.contrib import admin
from .models import Car, CarImage

class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    inlines = [CarImageInline]
    list_display = ('make', 'model', 'year', 'price', 'status', 'dealer')
    list_filter = ('status', 'make', 'transmission')
    search_fields = ('make', 'model', 'dealer__username')