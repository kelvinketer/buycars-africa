from django.urls import path
from . import views

urlpatterns = [
    path('pay/<str:plan_type>/', views.initiate_payment, name='initiate_payment'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
]