from django.contrib import admin
from django.utils.html import format_html
from .models import Wallet, Transaction, PayoutRequest

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_balance', 'get_total_earned', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__dealer_profile__phone_number')
    readonly_fields = ('balance', 'total_earned')

    def get_balance(self, obj):
        return format_html("<b>KES {}</b>", f"{obj.balance:,.2f}")
    get_balance.short_description = "Current Balance"

    def get_total_earned(self, obj):
        return f"KES {obj.total_earned:,.2f}"
    get_total_earned.short_description = "Lifetime Earnings"

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'wallet_user', 'transaction_type', 'get_amount', 'description', 'reference')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('wallet__user__username', 'reference', 'description')
    ordering = ('-created_at',)

    def wallet_user(self, obj):
        return obj.wallet.user.username
    wallet_user.short_description = "Dealer"

    def get_amount(self, obj):
        color = "green" if obj.transaction_type == 'CREDIT' else "red"
        return format_html('<span style="color: {}; font-weight: bold;">KES {:,.2f}</span>', color, obj.amount)
    get_amount.short_description = "Amount"

@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'get_dealer', 'mpesa_number', 'get_amount', 'status_badge')
    list_filter = ('status', 'created_at')
    search_fields = ('wallet__user__username', 'mpesa_number')
    actions = ['mark_as_processed', 'mark_as_rejected']
    ordering = ('-created_at',)

    def get_dealer(self, obj):
        return obj.wallet.user.username
    get_dealer.short_description = "Dealer"

    def get_amount(self, obj):
        return f"KES {obj.amount:,.2f}"
    get_amount.short_description = "Requested Amount"

    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'PROCESSED': 'green',
            'REJECTED': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.status
        )
    status_badge.short_description = "Status"

    # --- ADMIN ACTIONS ---
    def mark_as_processed(self, request, queryset):
        rows_updated = queryset.update(status='PROCESSED', processed_at=timezone.now())
        self.message_user(request, f"{rows_updated} request(s) marked as PROCESSED.")
    mark_as_processed.short_description = "Mark selected as PAID (Processed)"

    def mark_as_rejected(self, request, queryset):
        # Note: In a real app, you might want to refund the wallet balance here
        rows_updated = queryset.update(status='REJECTED')
        self.message_user(request, f"{rows_updated} request(s) marked as REJECTED.")
    mark_as_rejected.short_description = "Reject selected requests"
    
from django.utils import timezone