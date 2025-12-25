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
    
    # FIX: Changed <int:pk> to <int:car_id> to match your views.py
    path('car/<int:car_id>/', car_views.car_detail, name='car_detail'), 
    
    # --- AUTHENTICATION (Keep these safe!) ---
    path('login/', user_views.login_view, name='login'),
    path('signup/', user_views.signup_view, name='signup'),
    path('logout/', user_views.logout_view, name='logout'),

    # --- DEALER SIDE ---
    path('dashboard/', car_views.dealer_dashboard, name='dealer_dashboard'),
    path('add-car/', car_views.add_car, name='add_car'),
]

# Allow images to load in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)