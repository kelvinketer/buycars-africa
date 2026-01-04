from django.urls import path
from . import views

urlpatterns = [
    path('', views.dealer_wallet, name='dealer_wallet'),
]