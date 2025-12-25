from django.urls import path
from . import views

urlpatterns = [
    # --- Public Pages ---
    path('', views.public_homepage, name='home'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    
    # --- Dealer Dashboard Pages ---
    path('dashboard/', views.dealer_dashboard, name='dealer_dashboard'),
    path('dashboard/add/', views.add_car, name='add_car'),
]