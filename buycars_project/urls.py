from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView 
from cars import views as car_views 
from users import views as user_views 
from django.conf import settings
from django.conf.urls.static import static

# --- SEO IMPORTS ---
from django.contrib.sitemaps.views import sitemap
from cars.sitemaps import StaticViewSitemap, CarSitemap

# --- SITEMAP CONFIGURATION ---
sitemaps = {
    'static': StaticViewSitemap,
    'cars': CarSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- SEO ROUTES (Sitemap & Robots) ---
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    
    # --- GOOGLE MERCHANT FEED ---
    path('feeds/google-cars.xml', car_views.google_inventory_feed, name='google_inventory_feed'),

    # --- SUPER ADMIN (CEO Dashboard) ---
    path('super-admin/', user_views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/verify/<int:user_id>/', user_views.verify_dealer, name='verify_dealer'),
    path('platform/', car_views.platform_dashboard, name='platform_dashboard'), 

    # --- PASSWORD RESET ROUTES ---
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="auth/password_reset.html"), name='reset_password'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_sent.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_form.html"), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"), name='password_reset_complete'),

    # --- PUBLIC SIDE ---
    path('', car_views.public_homepage, name='home'),
    path('set-currency/', car_views.set_currency, name='set_currency'),
    path('car/<int:car_id>/', car_views.car_detail, name='car_detail'), 
    path('brands/', car_views.all_brands, name='brands_list'),
    path('dealer/<str:username>/', car_views.dealer_showroom, name='dealer_showroom'),
    
    # --- MESSAGING SYSTEM (NEW) ---
    path('chat/start/<int:car_id>/', car_views.start_conversation, name='start_conversation'),
    path('chat/inbox/', car_views.inbox, name='inbox'),
    path('chat/<int:conversation_id>/', car_views.conversation_detail, name='conversation_detail'),

    # --- INSTITUTIONAL IMPACT ---
    path('impact/', car_views.impact_hub, name='impact_hub'),
    path('1-million-trees/', car_views.impact_hub), 
    
    # --- LEGAL & GOVERNANCE ROUTES ---
    path('legal/<slug:slug>/', car_views.policy_page, name='policy_page'),

    # --- DRIVING CHANGE MANIFESTO ---
    path('driving-change/', car_views.driving_change_page, name='driving_change'),

    # --- TRANSPARENCY HUB ---
    path('transparency/', car_views.transparency_hub, name='transparency_hub'),

    # --- FINANCING PAGE ---
    path('financing/', car_views.financing_page, name='financing_page'),

    # --- DEALERSHIP NETWORK PAGE ---
    path('network/', car_views.dealership_network, name='dealership_network'),

    # --- PARTNERSHIP PORTAL ---
    path('partners/', car_views.partners_page, name='partners_page'),

    # --- DIASPORA LANDING PAGE ---
    path('diaspora/', car_views.diaspora_landing, name='diaspora_landing'),

    # --- BOOKING PAGE ---
    path('book/<int:car_id>/', car_views.book_car, name='book_car'),

    # --- DEALER LANDING PAGE ---
    path('sell/', TemplateView.as_view(template_name='saas/sell.html'), name='sell_page'),

    # --- LEAD TRACKING ---
    path('track/<int:car_id>/<str:action_type>/', car_views.track_action, name='track_action'),

    # --- AUTHENTICATION & RENTER DASHBOARD ---
    path('', include('users.urls')), 
    path('renter/dashboard/', user_views.renter_dashboard, name='renter_dashboard'),

    # --- DEALER SIDE ---
    path('dashboard/', car_views.dealer_dashboard, name='dealer_dashboard'),
    path('dashboard/add/', car_views.add_car, name='add_car'), 
    path('dashboard/report/', car_views.download_report, name='download_report'),
    path('dashboard/tools/agreement/', car_views.create_agreement, name='create_agreement'),
    
    # --- DEALER ACADEMY ---
    path('dashboard/academy/', car_views.dealer_academy, name='dealer_academy'),
    path('dashboard/academy/lesson/<int:module_id>/', car_views.dealer_academy_lesson, name='academy_lesson'),
    
    # --- PRICING PAGE ---
    path('pricing/', TemplateView.as_view(template_name='saas/pricing.html'), name='pricing'),
    
    # --- DEALER SETTINGS & SUPPORT ---
    path('dashboard/settings/', user_views.profile_settings, name='profile_settings'),
    path('dashboard/support/', user_views.support_view, name='dealer_support'),
    
    # --- EDIT & DELETE ROUTES ---
    path('dashboard/edit/<int:car_id>/', car_views.edit_car, name='edit_car'),
    path('dashboard/delete/<int:car_id>/', car_views.delete_car, name='delete_car'),
    path('dashboard/car/<int:car_id>/mark-sold/', car_views.mark_as_sold, name='mark_as_sold'),

    # --- IMAGE MANAGEMENT ---
    path('dashboard/car/<int:car_id>/image/<int:image_id>/set-main/', car_views.set_main_image, name='set_main_image'),
    path('dashboard/image/delete/<int:image_id>/', car_views.delete_car_image, name='delete_car_image'),

    # --- PAYMENTS & FINANCES ---
    path('payments/', include('payments.urls')), 
    path('wallet/', include('wallet.urls')), 
    
    # Add this inside urlpatterns:
path('admin-tools/fix-chat-db/', car_views.fix_chat_db, name='fix_chat_db'),

    # --- ADMIN TOOLS ---
    path('admin-tools/send-reports/', user_views.trigger_weekly_report, name='trigger_weekly_report'),
    path('admin-tools/check-subs/', user_views.trigger_subscription_check, name='trigger_subscription_check'),
    path('admin-tools/force-migrate/', car_views.run_migrations_view, name='force_migrate'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)