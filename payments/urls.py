from django.urls import path
from . import views

urlpatterns = [
    # 1. API to trigger the STK Push (AJAX POST from Pricing Page)
    # The frontend sends JSON data here directly.
    path('initiate/', views.initiate_payment, name='initiate_payment'),

    # 2. The Callback (Safaricom calls this to confirm payment)
    path('callback/', views.mpesa_callback, name='mpesa_callback'),

    # 3. Status Check Endpoint (Frontend polls this to see if payment succeeded)
    path('check-status/', views.check_payment_status, name='check_payment_status'),
]