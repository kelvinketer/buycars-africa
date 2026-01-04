from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView 
from cars import views as car_views 
from users import views as user_views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- SUPER ADMIN (CEO Dashboard) ---
    path('super-admin/', user_views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/verify/<int:user_id>/', user_views.verify_dealer, name='verify_dealer'),

    # --- PASSWORD RESET ROUTES ---
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="auth/password_reset.html"), 
         name='reset_password'),

    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_sent.html"), 
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_form.html"), 
         name='password_reset_confirm'),

    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"), 
         name='password_reset_complete'),

    # --- PUBLIC SIDE ---
    path('', car_views.public_homepage, name='home'),
    path('car/<int:car_id>/', car_views.car_detail, name='car_detail'), 
    path('brands/', car_views.all_brands, name='brands_list'),
    path('dealer/<str:username>/', car_views.dealer_showroom, name='dealer_showroom'),
    
    # --- [NEW] BOOKING PAGE ---
    path('book/<int:car_id>/', car_views.book_car, name='book_car'),

    # --- DEALER LANDING PAGE ---
    path('sell/', TemplateView.as_view(template_name='saas/sell.html'), name='sell_page'),

    # --- LEAD TRACKING ---
    path('track/<int:car_id>/<str:action_type>/', car_views.track_action, name='track_action'),

    # --- AUTHENTICATION (Delegated to users/urls.py) ---
    # This single line handles login, logout, signup, select account, and renter signup
    path('', include('users.urls')), 

    # --- DEALER SIDE ---
    path('dashboard/', car_views.dealer_dashboard, name='dealer_dashboard'),
    path('add-car/', car_views.add_car, name='add_car'),
    
    # MONTHLY REPORT PDF ROUTE
    path('dashboard/report/', car_views.download_report, name='download_report'),
    
    # --- PRICING PAGE ---
    path('pricing/', TemplateView.as_view(template_name='saas/pricing.html'), name='pricing'),
    
    # --- DEALER SETTINGS & SUPPORT ---
    path('dashboard/settings/', user_views.profile_settings, name='profile_settings'),
    path('dashboard/support/', user_views.support_view, name='dealer_support'),
    
    # --- EDIT & DELETE ROUTES ---
    path('dashboard/edit/<int:car_id>/', car_views.edit_car, name='edit_car'),
    path('dashboard/delete/<int:car_id>/', car_views.delete_car, name='delete_car'),
    
    # --- [NEW] MARK AS SOLD ---
    path('dashboard/car/<int:car_id>/mark-sold/', car_views.mark_as_sold, name='mark_as_sold'),

    # --- IMAGE MANAGEMENT ---
    path('dashboard/car/<int:car_id>/image/<int:image_id>/set-main/', car_views.set_main_image, name='set_main_image'),
    path('dashboard/image/delete/<int:image_id>/', car_views.delete_car_image, name='delete_car_image'),

    # --- PAYMENTS (M-PESA) ---
    path('payments/', include('payments.urls')), 

    # --- WALLET (EARNINGS) ---
    path('wallet/', include('wallet.urls')), 

    # --- MANUAL ADMIN TOOLS ---
    path('admin-tools/send-reports/', user_views.trigger_weekly_report, name='trigger_weekly_report'),
    path('admin-tools/check-subs/', user_views.trigger_subscription_check, name='trigger_subscription_check'),
]

# Allow images to load in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)