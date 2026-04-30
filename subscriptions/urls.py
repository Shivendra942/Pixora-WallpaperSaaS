from django.urls import path
from . import views

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),
    path('plans/', views.plans, name='plans'),
    path('create-order/<int:plan_id>/', views.create_order, name='create_order'),
    path('payment-success/', views.payment_success, name='payment_success'),  # ✅ ADD THIS
]