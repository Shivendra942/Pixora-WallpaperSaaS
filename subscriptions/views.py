from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import razorpay

from .models import Subscription, Plan


# Razorpay client
client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


# 🔎 Check if user is premium
def is_premium(user):
    sub = Subscription.objects.filter(user=user, active=True).first()
    return sub and sub.expiry > timezone.now()


# 📊 Get subscription info
def get_subscription(request):
    if request.user.is_authenticated:
        sub = Subscription.objects.filter(user=request.user, active=True).first()

        if sub:
            days_left = (sub.expiry - timezone.now()).days
            return sub, days_left

    return None, 0


# 🔥 CREATE ORDER (FIXED)
@login_required
def create_order(request, plan_id):
    try:
        print("👉 Requested plan_id:", plan_id)

        # ✅ SAFE PLAN FETCH
        plan = get_object_or_404(Plan, id=plan_id)

        print("✅ Plan:", plan.name, plan.price)

        order = client.order.create({
            "amount": int(plan.price * 100),
            "currency": "INR",
            "payment_capture": 1
        })

        return JsonResponse({
            "order_id": order["id"],
            "amount": order["amount"],
            "key": settings.RAZORPAY_KEY_ID
        })

    except Exception as e:
        print("🔥 ERROR in create_order:", str(e))
        return JsonResponse({"error": str(e)}, status=500)


# 🔥 PAYMENT SUCCESS
@csrf_exempt
@login_required
def payment_success(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    payment_id = request.POST.get("razorpay_payment_id")
    order_id = request.POST.get("razorpay_order_id")
    signature = request.POST.get("razorpay_signature")
    plan_id = request.POST.get("plan_id")

    try:
        # VERIFY SIGNATURE
        client.utility.verify_payment_signature({
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": order_id,
            "razorpay_signature": signature
        })

        # GET PLAN SAFELY
        plan = get_object_or_404(Plan, id=plan_id)

        # SAVE SUBSCRIPTION
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

    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({"status": "failed", "error": "Signature mismatch"}, status=400)

    except Exception as e:
        return JsonResponse({"status": "failed", "error": str(e)}, status=500)


# 📄 PLANS PAGE (FIXED)
def plans(request):
    plans = Plan.objects.all()
    return render(request, 'subscriptions/plans.html', {
        'plans': plans
    })

@login_required
def subscribe(request):
    Subscription.objects.update_or_create(
        user=request.user,
        defaults={
            "active": True,
            "start_date": timezone.now(),
            "expiry": timezone.now() + timedelta(days=30)
        }
    )
    return redirect('premium')