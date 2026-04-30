from django.urls import path
from . import views
from .views import WallpaperListAPI

urlpatterns = [
    path('', views.home, name='home'),

    path('download/<int:id>/', views.download_wallpaper, name='download'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('categories/', views.categories_page, name='categories'),

    # 👁 DETAIL PAGE
    path('detail/<int:id>/', views.wallpaper_detail, name='detail'),

    # 💰 BUY
    path('buy/<int:id>/', views.buy_wallpaper, name='buy'),
    path('payment-success/', views.payment_success, name='payment_success'),

    # ❤️ LIKE
    path('like/<int:wallpaper_id>/', views.toggle_like, name='toggle_like'),

    # 🔒 IMAGE SERVING (IMPORTANT)
    path('wallpaper/<int:id>/', views.serve_wallpaper, name='serve_wallpaper'),

    # OPTIONAL (OLD)
    path('secure-image/<int:id>/', views.secure_image, name='secure_image'),

    # API
    path('api/wallpapers/', WallpaperListAPI.as_view(), name='api_wallpapers'),

    # PREMIUM
    path('premium/', views.premium_wallpapers, name='premium'),
]