from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import razorpay

from .models import Subscription, Plan


# 🔐 Razorpay client (define once)
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


@login_required
def create_order(request, plan_id):
    try:
        print("👉 Requested plan_id:", plan_id)

        # ✅ Check plan exists
        plan = Plan.objects.filter(id=plan_id).first()
        if not plan:
            print("❌ Plan not found")
            return JsonResponse({"error": "Plan not found"}, status=404)

        print("✅ Plan:", plan.name, plan.price)

        # ✅ Create Razorpay order
        order = client.order.create({
            "amount": int(plan.price * 100),  # ₹ → paise
            "currency": "INR",
            "payment_capture": 1
        })

        print("✅ Order created:", order)

        return JsonResponse({
            "order_id": order.get("id"),
            "amount": order.get("amount"),
            "key": settings.RAZORPAY_KEY_ID
        })

    except Exception as e:
        print("🔥 ERROR in create_order:", str(e))
        return JsonResponse({"error": str(e)}, status=500)


# 💰 PAYMENT SUCCESS (with verification)
@csrf_exempt
@login_required
def payment_success(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    payment_id = request.POST.get("razorpay_payment_id")
    order_id = request.POST.get("razorpay_order_id")
    signature = request.POST.get("razorpay_signature")
    plan_id = request.POST.get("plan_id")

    # 🔎 Debug logs (optional but useful)
    print("PAYMENT DATA:", payment_id, order_id, signature, plan_id)

    try:
        # 🔐 VERIFY PAYMENT SIGNATURE
        client.utility.verify_payment_signature({
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": order_id,
            "razorpay_signature": signature
        })

        # ✅ Get plan
        plan = Plan.objects.get(id=plan_id)

        # ✅ Save subscription
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

    except Plan.DoesNotExist:
        return JsonResponse({"status": "failed", "error": "Invalid plan"}, status=400)

    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({"status": "failed", "error": "Signature mismatch"}, status=400)

    except Exception as e:
        return JsonResponse({"status": "failed", "error": str(e)}, status=500)


# 🧾 Manual subscribe (fallback/testing)
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


# 📄 Plans page
def plans(request):
    return render(request, 'subscriptions/plans.html')