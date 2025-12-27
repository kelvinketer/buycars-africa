from django.urls import path
from . import views

urlpatterns = [
    path('pay/<str:plan_type>/', views.initiate_payment, name='initiate_payment'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    
    # --- NEW: Status Check Endpoint ---
    path('check-status/', views.check_payment_status, name='check_payment_status'),
]