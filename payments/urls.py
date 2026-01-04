from django.urls import path
from . import views

urlpatterns = [
    # 1. The Checkout Page (User Interface) - THIS WAS MISSING
    path('checkout/<int:booking_id>/', views.checkout, name='checkout'),

    # 2. API to trigger the STK Push (AJAX POST from Pricing/Checkout Page)
    path('initiate/', views.initiate_payment, name='initiate_payment'),

    # 3. The Callback (Safaricom calls this to confirm payment)
    path('callback/', views.mpesa_callback, name='mpesa_callback'),

    # 4. Status Check Endpoint (Frontend polls this to see if payment succeeded)
    path('check-status/', views.check_payment_status, name='check_payment_status'),
]