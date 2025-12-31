from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.public_homepage, name='home'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    path('showroom/<str:username>/', views.dealer_showroom, name='dealer_showroom'),
    path('brands/', views.all_brands, name='all_brands'),
    path('pricing/', views.pricing_page, name='pricing'),
    
    # Tracking
    path('cars/track-action/<int:car_id>/<str:action_type>/', views.track_action, name='track_action'),

    # Dealer Dashboard URLs
    path('dashboard/', views.dealer_dashboard, name='dealer_dashboard'),
    path('dashboard/add/', views.add_car, name='add_car'),
    path('dashboard/edit/<int:car_id>/', views.edit_car, name='edit_car'),
    path('dashboard/delete/<int:car_id>/', views.delete_car, name='delete_car'),
    
    # NEW: Set Main Image URL
    path('dashboard/car/<int:car_id>/image/<int:image_id>/set-main/', views.set_main_image, name='set_main_image'),
]