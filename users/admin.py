from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html # <--- Critical for Image Previews
from .models import User, DealerProfile, CustomerProfile # <--- Added CustomerProfile

class DealerProfileInline(admin.StackedInline):
    model = DealerProfile
    can_delete = False
    verbose_name_plural = 'Dealer Profile'

# --- NEW: Custom Actions ---
@admin.action(description='✅ Mark selected users as VERIFIED')
def make_verified(modeladmin, request, queryset):
    queryset.update(is_verified=True)

@admin.action(description='❌ Mark selected users as UNVERIFIED')
def make_unverified(modeladmin, request, queryset):
    queryset.update(is_verified=False)

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

    # --- Register the new actions here ---
    actions = [make_verified, make_unverified]

# --- NEW: RENTER (CUSTOMER) ADMIN ---
@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'id_number', 'is_verified', 'created_at', 'id_preview')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('user__username', 'phone_number', 'id_number')
    readonly_fields = ('id_front_image_preview', 'driving_license_image_preview')

    # Preview for the List View (Small)
    def id_preview(self, obj):
        if obj.id_front_image:
            return format_html('<img src="{}" style="width: 50px; height: auto; border-radius: 4px;" />', obj.id_front_image.url)
        return "No ID"
    id_preview.short_description = "ID Check"

    # Preview for the Detail View (Big)
    def id_front_image_preview(self, obj):
        if obj.id_front_image:
            return format_html('<a href="{}" target="_blank"><img src="{}" style="max-width: 300px; border: 1px solid #ccc;" /></a>', obj.id_front_image.url, obj.id_front_image.url)
        return "No Image"
    
    def driving_license_image_preview(self, obj):
        if obj.driving_license_image:
            return format_html('<a href="{}" target="_blank"><img src="{}" style="max-width: 300px; border: 1px solid #ccc;" /></a>', obj.driving_license_image.url, obj.driving_license_image.url)
        return "No Image"

    # Display these previews in the form
    fieldsets = (
        ('User Info', {'fields': ('user', 'phone_number', 'id_number', 'is_verified')}),
        ('Documents', {'fields': ('id_front_image', 'id_front_image_preview', 'driving_license_image', 'driving_license_image_preview')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(DealerProfile)