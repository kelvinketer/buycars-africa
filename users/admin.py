from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DealerProfile

class DealerProfileInline(admin.StackedInline):
    model = DealerProfile
    can_delete = False
    verbose_name_plural = 'Dealer Profile'

class CustomUserAdmin(UserAdmin):
    # ADDED 'phone_number' to this list so you see it immediately in the table
    list_display = ('username', 'email', 'phone_number', 'role', 'is_verified', 'is_staff')
    
    # Filters allow you to click "Show me only Dealers" on the right sidebar
    list_filter = ('role', 'is_verified', 'is_staff')
    
    # This enables editing the Profile (Logo/City) inside the User page
    inlines = (DealerProfileInline,)
    
    # This adds the fields to the "Edit User" page
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Contact Info', {'fields': ('role', 'phone_number', 'is_verified')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(DealerProfile)