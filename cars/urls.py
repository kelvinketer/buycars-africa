from django.urls import path
from . import views

urlpatterns = [
    # --- MOVED TO TOP to ensure it registers ---
    path('brands/', views.all_brands, name='brands_list'),

    # --- Public Pages ---
    path('', views.public_homepage, name='home'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    
    # --- Dealer Public Profile ---
    path('dealer/<str:username>/', views.dealer_showroom, name='dealer_showroom'),

    # --- Analytics / Lead Tracking ---
    path('track/<int:car_id>/<str:action_type>/', views.track_action, name='track_action'),

    # --- Dealer Dashboard ---
    path('dashboard/', views.dealer_dashboard, name='dealer_dashboard'),
    path('dashboard/add/', views.add_car, name='add_car'),
    path('dashboard/edit/<int:car_id>/', views.edit_car, name='edit_car'),
    path('dashboard/delete/<int:car_id>/', views.delete_car, name='delete_car'),

    # --- Pricing Page ---
    path('pricing/', views.pricing_page, name='pricing'),
]