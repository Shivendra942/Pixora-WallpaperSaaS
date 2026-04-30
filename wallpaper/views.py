from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import Wallpaper, Category, Purchase
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required
import os
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Wallpaper, Like
from PIL import Image, ImageDraw, ImageFont
import io
from rest_framework.generics import ListAPIView
from .serializers import WallpaperSerializer
from rest_framework.filters import OrderingFilter
from rest_framework.filters import SearchFilter
from django.core.paginator import Paginator
from .models import Wallpaper, Purchase
from PIL import Image, ImageFilter
import io
from django.utils import timezone
from subscriptions.models import Subscription
from subscriptions.models import Plan
from datetime import timedelta


def serve_wallpaper(request, id):
    wallpaper = get_object_or_404(Wallpaper, id=id)

    img = Image.open(wallpaper.image.path)

    # 🔐 Check access
    has_access = False

    if request.user.is_authenticated:
        has_access = Purchase.objects.filter(
            user=request.user,
            wallpaper=wallpaper,
            paid=True
        ).exists()

    # 🎯 Blur if not purchased
    if wallpaper.is_paid and not has_access:
        img = img.filter(ImageFilter.GaussianBlur(12))

    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG")

    return HttpResponse(buffer.getvalue(), content_type="image/jpeg")
@login_required(login_url='login')
def secure_image(request, id):
    wallpaper = get_object_or_404(Wallpaper, id=id)

    # 🔒 Check purchase
    if wallpaper.is_paid:
        purchased = Purchase.objects.filter(
            user=request.user,
            wallpaper=wallpaper,
            paid=True
        ).exists()

        if not purchased:
            return HttpResponse("Unauthorized", status=403)

    # ✅ Serve original image
    img = Image.open(wallpaper.image.path)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")

    return HttpResponse(buffer.getvalue(), content_type="image/jpeg")


from django.db.models import Q, Count
from django.core.paginator import Paginator

def home(request):
    query = request.GET.get('q')
    sort = request.GET.get('sort')

    if query:
        wallpapers = Wallpaper.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query),
            is_paid=False   # ✅ only free
        )
    else:
        wallpapers = Wallpaper.objects.filter(
            is_paid=False   # ✅ only free
        )

    if sort == "popular":
        wallpapers = wallpapers.annotate(
            total_likes=Count('like')
        ).order_by('-downloads', '-total_likes')
    else:
        wallpapers = wallpapers.order_by('-id')

    paginator = Paginator(wallpapers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, 'home.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query
    })
@login_required(login_url='login')
def download_wallpaper(request, id):
    wallpaper = get_object_or_404(Wallpaper, id=id)

    # 🔒 CHECK PURCHASE
    if wallpaper.is_paid:
        purchased = Purchase.objects.filter(
            user=request.user,
            wallpaper=wallpaper,
            paid=True
        ).exists()

        if not purchased:
            return redirect('buy', id=wallpaper.id)

    # normal download
    file_path = wallpaper.image.path
    file_name = os.path.basename(file_path)

    wallpaper.downloads += 1
    wallpaper.save()

    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_name)




def wallpaper_detail(request, id):
    wallpaper = Wallpaper.objects.get(id=id)

    return render(request, 'detail.html', {
        'wallpaper': wallpaper
    })


def category_view(request, slug):
    category = Category.objects.get(slug=slug)
    wallpapers = Wallpaper.objects.filter(category=category)

    return render(request, 'category.html', {
        'category': category,
        'wallpapers': wallpapers
    })

def categories_page(request):
    categories = Category.objects.all()

    data = []

    for cat in categories:
        wallpaper = Wallpaper.objects.filter(category=cat).first()
        data.append({
            'category': cat,
            'image': wallpaper.image.url if wallpaper else None
        })

    return render(request, 'categories.html', {
        'data': data
    })

@login_required(login_url='login')
def buy_wallpaper(request, id):
    wallpaper = get_object_or_404(Wallpaper, id=id)

    if request.method == 'POST':
        Purchase.objects.create(
            user=request.user,
            wallpaper=wallpaper,
            paid=True
        )
        return redirect('detail', id=wallpaper.id)

    return render(request, 'buy.html', {
        'wallpaper': wallpaper
    })



@login_required(login_url='login')
def buy_wallpaper(request, id):
    wallpaper = get_object_or_404(Wallpaper, id=id)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    order = client.order.create({
        "amount": wallpaper.price * 100,   # paise
        "currency": "INR",
        "payment_capture": "1"
    })

    return render(request, 'buy.html', {
        'wallpaper': wallpaper,
        'order_id': order['id'],
        'razorpay_key': settings.RAZORPAY_KEY_ID
    })

@login_required(login_url='login')
def payment_success(request):
    payment_id = request.GET.get('payment_id')
    order_id = request.GET.get('order_id')

    wallpaper_id = request.GET.get('wallpaper_id')

    wallpaper = Wallpaper.objects.get(id=wallpaper_id)

    Purchase.objects.get_or_create(
    user=request.user,
    wallpaper=wallpaper,
    defaults={'paid': True}
)

    return redirect('detail', id=wallpaper.id)



@csrf_exempt
def payment_success(request):

    if request.method == "POST":

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')
        plan_id = request.POST.get('plan_id')

        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)

            plan = Plan.objects.get(id=plan_id)

            Subscription.objects.update_or_create(
                user=request.user,
                defaults={
                    "plan": plan,
                    "active": True,
                    "start_date": timezone.now(),
                    "expiry": timezone.now() + timedelta(days=plan.duration_days)
                }
            )

            return JsonResponse({"status": "success"})

        except:
            return JsonResponse({"status": "failed"}, status=400)
        
def toggle_like(request, wallpaper_id):

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required'}, status=401)

    wallpaper = get_object_or_404(Wallpaper, id=wallpaper_id)

    like, created = Like.objects.get_or_create(
        user=request.user,
        wallpaper=wallpaper
    )

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'count': wallpaper.like_set.count()
    })

def watermarked_image(request, id):
    wallpaper = Wallpaper.objects.get(id=id)

    img = Image.open(wallpaper.image.path).convert("RGBA")

    width, height = img.size

    # create transparent layer
    watermark_layer = Image.new('RGBA', img.size, (255,255,255,0))
    draw = ImageDraw.Draw(watermark_layer)

    text = request.user.username if request.user.is_authenticated else "WALLIFY"

    # position center
    text_position = (width // 4, height // 2)

    draw.text(text_position, text, fill=(255, 0, 0, 120))

    # merge
    watermarked = Image.alpha_composite(img, watermark_layer)

    buffer = io.BytesIO()
    watermarked.convert("RGB").save(buffer, format="JPEG")

    return HttpResponse(buffer.getvalue(), content_type="image/jpeg")



class WallpaperListAPI(ListAPIView):
    serializer_class = WallpaperSerializer
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'downloads']

    def get_queryset(self):
        queryset = Wallpaper.objects.all()
        category = self.request.GET.get('category')

        if category:
            queryset = queryset.filter(category__slug=category)

        return queryset



@login_required(login_url='login')
def premium_wallpapers(request):

    wallpapers = Wallpaper.objects.filter(is_paid=True)

    subscription = Subscription.objects.filter(
        user=request.user,
        active=True
    ).first()

    has_subscription = False

    if subscription and subscription.expiry > timezone.now():
        has_subscription = True

    return render(request, 'premium.html', {
        'wallpapers': wallpapers,
        'has_subscription': has_subscription
    })