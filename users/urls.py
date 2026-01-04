from django.urls import path
from . import views

urlpatterns = [
    # --- Authentication ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # --- Registration Flow ---
    path('signup/', views.signup_view, name='signup'),             # Dealer Signup (Old Default)
    path('signup/select/', views.select_account, name='select_account'), # New Gateway Page
    path('signup/renter/', views.customer_signup, name='customer_signup'), # New Renter Signup
]