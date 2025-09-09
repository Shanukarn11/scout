# registration/views_level2.py
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST
import razorpay

from .models import (
    Scout, ScoutLevel2, ScoutCourse, ScoutCourseDiscount
)

# ---------- helpers ----------
RAZORPAY_KEY_ID=""
RAZORPAY_KEY_SECRET=""
def _to_decimal(val):
    try:
        return Decimal(str(val).strip())
    except Exception:
        return Decimal("0.00")

def _bad_request(msg):
    return JsonResponse({"error": True, "message": msg}, status=400)

def _compute_amount(course_id, discount_code):
    """
    Server-side pricing. NEVER trust client amount.
    """
    course = get_object_or_404(ScoutCourse, id=course_id)
    base = _to_decimal(course.amount or "0")
    discount = Decimal("0.00")
    if discount_code:
        row = ScoutCourseDiscount.objects.filter(
            course=course, type__id=discount_code
        ).first()
        if row and row.discount:
            discount = _to_decimal(row.discount)
    final_amt = base - discount
    if final_amt < 0:
        final_amt = Decimal("0.00")
    return base, discount, final_amt

# ---------- views ----------

@require_GET
def level2_form(request):
    """
    Render the Level-2 page with available courses to build the label map.
    """
    courses = list(ScoutCourse.objects.all().values("id", "course", "amount"))
    return render(request, "player/level2.html", {"courses": courses})

@require_POST
def level2_prefill(request):
    """
    Input: ikfuniqueid
    Output: Scout data (prefill), and any existing Level-2 choices.
    """
    ikf = (request.POST.get("ikfuniqueid") or "").strip()
    if not ikf:
        return _bad_request("ikfuniqueid required")

    scout = get_object_or_404(Scout, ikfuniqueid=ikf)

    scout_data = {
        "ikfuniqueid": scout.ikfuniqueid,
        "first_name": scout.first_name,
        "last_name": scout.last_name,
        "gender": scout.gender,
        "dob": scout.dob.isoformat() if scout.dob else None,
        "email": scout.email,
        "mobile": scout.mobile,
        "associated_years": scout.associated_years,
        "associated_as": scout.associated_as,
        "course": scout.course_id,  # default selection
    }

    l2 = getattr(scout, "level2", None)
    l2_data = None
    if l2:
        l2_data = {
            "course": l2.course_id,
            "discount_code": l2.discount_code,
            "final_amount": str(l2.final_amount) if l2.final_amount is not None else None,
            "status": l2.status,
            "order_id": l2.order_id,
        }

    return JsonResponse({"scout": scout_data, "level2": l2_data})

@require_POST
@transaction.atomic
def level2_save(request):
    """
    Save Level-2 selections (course/discount) and price snapshot.
    The UI is preview-only: we don't edit profile fields here.
    """
    ikf = (request.POST.get("ikfuniqueid") or "").strip()
    if not ikf:
        return _bad_request("ikfuniqueid required")

    scout = get_object_or_404(Scout, ikfuniqueid=ikf)

    # Fallback to L1 course if not posted
    course_id = (request.POST.get("course") or "").strip() or (scout.course_id or "")
    if not course_id:
        return _bad_request("course is required")

    discount_code = (request.POST.get("discount_code") or "").strip() or None

    # Upsert Level-2
    l2, _ = ScoutLevel2.objects.select_for_update().get_or_create(scout=scout)
    l2.course_id = course_id
    l2.discount_code = discount_code

    base, disc, final_amt = _compute_amount(course_id, discount_code)
    l2.base_amount = base
    l2.discount_rupees = disc
    l2.final_amount = final_amt
    l2.save()

    return JsonResponse({
        "error": False,
        "message": "saved",
        "final_amount": str(final_amt),
        "status": l2.status
    })

@require_POST
@transaction.atomic
def level2_order(request):
    """
    Create Razorpay order for Level-2 final_amount.
    """
    ikf = (request.POST.get("ikfuniqueid") or "").strip()
    if not ikf:
        return _bad_request("ikfuniqueid required")

    scout = get_object_or_404(Scout, ikfuniqueid=ikf)
    l2 = get_object_or_404(ScoutLevel2, scout=scout)

    # Recompute for safety
    base, disc, final_amt = _compute_amount(l2.course_id, l2.discount_code)
    l2.base_amount, l2.discount_rupees, l2.final_amount = base, disc, final_amt

    # Convert to paise safely
    amount_paise = int((final_amt * 100).to_integral_value())

    try:
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        resp = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"{scout.ikfuniqueid}-L2",
            "notes": {"scout_id": scout.id, "level2_id": l2.id}
        })
    except Exception as e:
        return _bad_request(f"Razorpay error: {e}")

    l2.order_id = resp.get("id")
    l2.status = "order_created"
    l2.save(update_fields=["order_id", "status", "base_amount", "discount_rupees", "final_amount"])

    return JsonResponse({"error": False, "order_id": l2.order_id, "amount": str(final_amt)})

@require_POST
@transaction.atomic
def level2_payment_status(request):
    """
    Update Level-2 payment status after checkout.
    (You can also implement a Razorpay webhook; this is the front-channel update.)
    """
    ikf = (request.POST.get("ikfuniqueid") or "").strip()
    oid = request.POST.get("razorpay_order_id")
    pid = request.POST.get("razorpay_payment_id")
    sig = request.POST.get("razorpay_signature")

    if not ikf or not oid:
        return _bad_request("ikfuniqueid and razorpay_order_id are required")

    scout = get_object_or_404(Scout, ikfuniqueid=ikf)
    l2 = get_object_or_404(ScoutLevel2, scout=scout, order_id=oid)

    # Optional: verify signature using Razorpay utility
    # client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    # client.utility.verify_payment_signature({
    #     "razorpay_order_id": oid, "razorpay_payment_id": pid, "razorpay_signature": sig
    # })

    l2.payment_id = pid
    l2.payment_signature = sig
    l2.status = "paid"
    l2.save(update_fields=["payment_id", "payment_signature", "status"])

    return JsonResponse({"error": False, "message": "payment saved", "status": l2.status})
