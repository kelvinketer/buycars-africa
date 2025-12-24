from django.contrib import admin
from .models import SubscriptionPlan, DealerSubscription

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'max_cars')

@admin.register(DealerSubscription)
class DealerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('dealer', 'plan', 'end_date', 'is_active')
    list_filter = ('is_active', 'plan')