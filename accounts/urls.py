from django.urls import path
from .views import register, user_logout, CustomLoginView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register, name='register'),
    path('logout/', user_logout, name='logout'),
]