from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DealerProfile

class DealerProfileInline(admin.StackedInline):
    model = DealerProfile
    can_delete = False
    verbose_name_plural = 'Dealer Profile'

class CustomUserAdmin(UserAdmin):
    # This adds the "role" column to the list view
    list_display = ('username', 'email', 'role', 'is_staff', 'is_verified')
    list_filter = ('role', 'is_verified', 'is_staff')
    
    # This enables editing the Profile inside the User page
    inlines = (DealerProfileInline,)
    
    # Add 'role' and 'phone_number' to the edit form
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone_number', 'is_verified')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(DealerProfile)