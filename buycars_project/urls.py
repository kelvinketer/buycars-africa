from django.contrib import admin
from django.urls import path
from cars import views as car_views 
from users import views as user_views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- PUBLIC SIDE ---
    path('', car_views.public_homepage, name='home'),
    path('car/<int:car_id>/', car_views.car_detail, name='car_detail'), 
    
    # --- DEALER SHOWROOM (Public Profile) ---
    path('dealer/<str:username>/', car_views.dealer_showroom, name='dealer_showroom'),

    # --- AUTHENTICATION ---
    path('login/', user_views.login_view, name='login'),
    path('signup/', user_views.signup_view, name='signup'),
    path('logout/', user_views.logout_view, name='logout'),

    # --- DEALER SIDE ---
    path('dashboard/', car_views.dealer_dashboard, name='dealer_dashboard'),
    path('add-car/', car_views.add_car, name='add_car'),
    
    # --- NEW: DEALER SETTINGS ---
    path('dashboard/settings/', user_views.profile_settings, name='profile_settings'),
    
    # --- EDIT & DELETE ROUTES ---
    path('dashboard/edit/<int:car_id>/', car_views.edit_car, name='edit_car'),
    path('dashboard/delete/<int:car_id>/', car_views.delete_car, name='delete_car'),
]

# Allow images to load in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)