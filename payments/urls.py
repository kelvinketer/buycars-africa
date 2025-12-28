from django.urls import path
from . import views

urlpatterns = [
    # 1. The Page where they enter the number (GET request)
    path('pay/<str:plan_type>/', views.initiate_payment, name='initiate_payment'),

    # 2. The Form Submission Handler (POST request) <--- THIS WAS MISSING
    path('process/', views.process_payment, name='process_payment'),

    # 3. The Callback (Safaricom calls this)
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    
    # 4. Status Check Endpoint (For polling)
    path('check-status/', views.check_payment_status, name='check_payment_status'),
]