from django.urls import path
from . import views

urlpatterns = [
    # --- PUBLIC URLS ---
    path('', views.public_homepage, name='home'),
    
    # --- THIS IS THE FIX (New Line) ---
    # We map 'inventory/' to the homepage view since that serves as your car list.
    path('inventory/', views.public_homepage, name='car_list'),
    # ----------------------------------

    path('set-currency/', views.set_currency, name='set_currency'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    path('showroom/<str:username>/', views.dealer_showroom, name='dealer_showroom'),
    path('brands/', views.all_brands, name='all_brands'),
    path('pricing/', views.pricing_page, name='pricing'),
    path('diaspora/', views.diaspora_landing, name='diaspora_landing'),

    # --- RENTAL & BOOKING ---
    path('book/<int:car_id>/', views.book_car, name='book_car'),

    # --- LEAD TRACKING ---
    path('cars/track-action/<int:car_id>/<str:action_type>/', views.track_action, name='track_action'),

    # --- MESSAGING SYSTEM (NEW) ---
    path('chat/start/<int:car_id>/', views.start_conversation, name='start_conversation'),
    path('chat/inbox/', views.inbox, name='inbox'),
    path('chat/conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),

    # --- NOTE: SOCIAL FEATURES REMOVED ---
    # I removed the 'social/follow' and 'social/like' paths because you deleted 
    # those functions in views.py. Keeping them here would crash the site.

    # --- DEALER DASHBOARD ---
    path('dashboard/', views.dealer_dashboard, name='dealer_dashboard'),
    path('dashboard/report/', views.download_report, name='download_report'),
    path('dashboard/add/', views.add_car, name='add_car'), 
    path('dashboard/edit/<int:car_id>/', views.edit_car, name='edit_car'),
    path('dashboard/delete/<int:car_id>/', views.delete_car, name='delete_car'),
    
    # --- IMAGE MANAGEMENT ---
    path('dashboard/car/<int:car_id>/image/<int:image_id>/set-main/', views.set_main_image, name='set_main_image'),
    path('dashboard/image/<int:image_id>/delete/', views.delete_car_image, name='delete_car_image'),

    # --- QUICK ACTIONS ---
    path('dashboard/car/<int:car_id>/mark-sold/', views.mark_as_sold, name='mark_as_sold'),

    # --- PLATFORM ADMIN (Staff Only) ---
    path('platform/', views.platform_dashboard, name='platform_dashboard'),
    
    # --- GOOGLE MERCHANT FEED ---
    path('feeds/google-cars.xml', views.google_inventory_feed, name='google_inventory_feed'),

    # --- DATABASE REPAIR TOOL (Hidden) ---
    path('admin-tools/fix-db/', views.fix_chat_db, name='fix_db'),
]
