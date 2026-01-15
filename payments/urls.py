from django.urls import path
from . import views

urlpatterns = [
    # 1. Booking Checkout (For Renting/Buying)
    path('checkout/<int:booking_id>/', views.checkout, name='checkout'),

    # 2. Subscription Checkout (For Dealers) -- NEW
    path('subscribe/<str:plan_type>/', views.subscription_checkout, name='subscription_checkout'),

    # 3. API to trigger M-Pesa STK Push
    path('initiate/', views.initiate_payment, name='initiate_payment'),

    # 4. M-Pesa Callback (Safaricom calls this)
    path('callback/', views.mpesa_callback, name='mpesa_callback'),

    # 5. Status Check Endpoint (Polling)
    path('check-status/', views.check_payment_status, name='check_payment_status'),

    # 6. Flutterwave Card Verification Redirect
    path('verify-card/', views.verify_flutterwave, name='verify_flutterwave'),
]