from django.urls import path
from . import views

urlpatterns = [
    # 1. The Checkout Page (User Interface)
    path('checkout/<int:booking_id>/', views.checkout, name='checkout'),

    # 2. API to trigger M-Pesa STK Push
    path('initiate/', views.initiate_payment, name='initiate_payment'),

    # 3. M-Pesa Callback (Safaricom calls this)
    path('callback/', views.mpesa_callback, name='mpesa_callback'),

    # 4. Status Check Endpoint (Polling)
    path('check-status/', views.check_payment_status, name='check_payment_status'),

    # 5. NEW: Flutterwave Card Verification Redirect
    path('verify-card/', views.verify_flutterwave, name='verify_flutterwave'),
]