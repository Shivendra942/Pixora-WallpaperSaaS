from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.models import User
from wallpaper.models import Wallpaper, Purchase
from django.http import HttpResponseForbidden
from wallpaper.models import Purchase, Like, Wallpaper
from subscriptions.models import Subscription
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta





@login_required(login_url='login')
def profile(request):

    # 🔥 PROFILE IMAGE UPDATE
    if request.method == "POST" and request.FILES.get('image'):
        request.user.profile.image = request.FILES.get('image')
        request.user.profile.save()

    # 🛒 PURCHASES
    purchases = Purchase.objects.filter(user=request.user)

    # ❤️ LIKES
    likes = Like.objects.filter(user=request.user)

    # 💎 SUBSCRIPTION
    subscription = Subscription.objects.filter(
        user=request.user,
        active=True
    ).first()

    status = "Inactive"
    days_left = 0

    if subscription:
        if subscription.expiry > timezone.now():
            status = "Active"
            days_left = (subscription.expiry - timezone.now()).days
        else:
            status = "Expired"

    return render(request, 'personalview/profile.html', {
        'purchases': purchases,
        'likes': likes,
        'subscription': subscription,
        'status': status,
        'days_left': days_left
    })


@login_required(login_url='login')
def admin_dashboard(request):

    if not request.user.is_superuser:
        return redirect('home')

    # 🔢 BASIC STATS
    total_users = User.objects.count()
    total_wallpapers = Wallpaper.objects.count()
    total_downloads = Wallpaper.objects.aggregate(
        total=Sum('downloads')
    )['total'] or 0

    total_revenue = Purchase.objects.filter(
        paid=True
    ).aggregate(total=Sum('amount'))['total'] or 0

    # 📈 LAST 7 DAYS ANALYTICS
    today = timezone.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    downloads_data = []
    revenue_data = []

    for day in last_7_days:
        day_downloads = Wallpaper.objects.filter(
            uploaded_at__date=day
        ).aggregate(total=Sum('downloads'))['total'] or 0

        day_revenue = Purchase.objects.filter(
            created_at__date=day,
            paid=True
        ).aggregate(total=Sum('amount'))['total'] or 0

        downloads_data.append(day_downloads)
        revenue_data.append(day_revenue)

    context = {
        "total_users": total_users,
        "total_wallpapers": total_wallpapers,
        "total_downloads": total_downloads,
        "total_revenue": total_revenue,

        "labels": [str(d) for d in last_7_days],
        "downloads_data": downloads_data,
        "revenue_data": revenue_data,
    }

    return render(request, 'personalview/dashboard.html', context)