from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.public_homepage, name='home'),
    path('set-currency/', views.set_currency, name='set_currency'),  # <--- NEW: Currency Switcher
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    path('showroom/<str:username>/', views.dealer_showroom, name='dealer_showroom'),
    path('brands/', views.all_brands, name='all_brands'),
    path('pricing/', views.pricing_page, name='pricing'),
    
    # Rental / Booking URL
    path('book/<int:car_id>/', views.book_car, name='book_car'),

    # Tracking
    path('cars/track-action/<int:car_id>/<str:action_type>/', views.track_action, name='track_action'),

    # Dealer Dashboard URLs
    path('dashboard/', views.dealer_dashboard, name='dealer_dashboard'),
    path('dashboard/report/', views.download_report, name='download_report'), # <--- Added: Missing Report URL
    path('dashboard/add/', views.add_car, name='add_car'),
    path('dashboard/edit/<int:car_id>/', views.edit_car, name='edit_car'),
    path('dashboard/delete/<int:car_id>/', views.delete_car, name='delete_car'),
    
    # Image Management
    path('dashboard/car/<int:car_id>/image/<int:image_id>/set-main/', views.set_main_image, name='set_main_image'),
    path('dashboard/image/<int:image_id>/delete/', views.delete_car_image, name='delete_car_image'),

    # Quick Actions
    path('dashboard/car/<int:car_id>/mark-sold/', views.mark_as_sold, name='mark_as_sold'),

    # Platform Admin (Staff Only)
    path('platform/', views.platform_dashboard, name='platform_dashboard'), # <--- Added: Missing Platform URL
]