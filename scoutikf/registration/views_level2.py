# registration/views_level2.py
from decimal import Decimal
import threading

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from django.templatetags.static import static

import razorpay

from .models import Scout, ScoutLevel2, ScoutCourse, ScoutCourseDiscount,MasterLabels

# ---- optional: import your Interakt helpers ---------------------------------
try:
    # adjust the import path to where your helpers live
    from .utils import send_whatsapp_public_message, interakt_add_user
except Exception:
    # fallbacks: define no-op if not available to avoid crashes
    def send_whatsapp_public_message(*args, **kwargs):
        return None
    def interakt_add_user(*args, **kwargs):
        return None


# ---------------- helpers ----------------

def _to_decimal(val):
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0.00")


def _get_level2_course():
    """
    Pick the Level-2 course.

    Priority:
      1) settings.LEVEL2_DEFAULT_COURSE_ID (if set and exists)
      2) course__iexact == "Level 2"
      3) id == 4
      4) first course
    """
    cid = getattr(settings, "LEVEL2_DEFAULT_COURSE_ID", None)
    if cid:
        c = ScoutCourse.objects.filter(id=str(cid)).first()
        if c:
            return c

    c = ScoutCourse.objects.filter(course__iexact="Level 2").first()
    if c:
        return c

    c = ScoutCourse.objects.filter(id="4").first()
    if c:
        return c

    return ScoutCourse.objects.first()


def _compute_amount(course_id, discount_code):
    """
    Server-side pricing. NEVER trust client amounts.
    """
    course = get_object_or_404(ScoutCourse, id=course_id)
    base = _to_decimal(course.amount or "0")
    discount = Decimal("0.00")

    # If you don't use discount codes, leave discount at 0.
    if discount_code:
        row = ScoutCourseDiscount.objects.filter(course=course, type__id=discount_code).first()
        if row and row.discount:
            discount = _to_decimal(row.discount)

    final_amt = base - discount
    if final_amt < 0:
        final_amt = Decimal("0.00")
    return base, discount, final_amt


def _get_scout_from_request(request):
    """
    Accept either the new ikf_level_1_id or the legacy ikfuniqueid.
    """
    ikf_lvl1 = (request.POST.get("ikf_level_1_id") or "").strip()
    if ikf_lvl1:
        return get_object_or_404(Scout, ikf_level_1_id=ikf_lvl1)

    ikf_old = (request.POST.get("ikfuniqueid") or "").strip()
    if ikf_old:
        return get_object_or_404(Scout, ikfuniqueid=ikf_old)

    raise ValueError("ikf_level_1_id or ikfuniqueid required")


# ---------------- views ----------------

@require_GET
def level2_form(request):
    """
    Render Level-2 page.
    Pass:
      - courses (for label mapping)
      - level2_course_id / level2_course_amount
      - razorpay_key_id
    """
    courses = list(ScoutCourse.objects.all().values("id", "course", "amount"))
    level2_course = _get_level2_course()
    ctx = {
        "courses": courses,
        "level2_course_id": level2_course.id if level2_course else "",
        "level2_course_amount": str(level2_course.amount or "") if level2_course else "",
        "razorpay_key_id": getattr(settings, "RAZORPAY_KEY_ID", ""),
    }
    return render(request, "player/level2.html", ctx)


@require_POST
def level2_prefill(request):
    """
    Input: ikf_level_1_id (preferred) OR ikfuniqueid
    Output: scout preview + existing level2 row (if any)
    """
    try:
        scout = _get_scout_from_request(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    scout_data = {
        "ikf_level_1_id": scout.ikf_level_1_id,
        "ikfuniqueid": scout.ikfuniqueid,
        "first_name": scout.first_name,
        "last_name": scout.last_name,
        "gender": scout.gender,
        "dob": scout.dob.isoformat() if getattr(scout, "dob", None) else None,
        "email": scout.email,
        "mobile": scout.mobile,
        "course": scout.course_id,  # completed course shown in preview
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
    Confirm step: upsert ScoutLevel2 with the default Level-2 course and compute amount.
    Does NOT change Scout.course (that's the 'completed' course).
    Accepts: ikf_level_1_id/ikfuniqueid and optional discount_code
    """
    try:
        scout = _get_scout_from_request(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    level2_course = _get_level2_course()
    if not level2_course:
        return HttpResponseBadRequest("Level-2 course not configured")

    discount_code = (request.POST.get("discount_code") or "").strip() or None

    l2, _ = ScoutLevel2.objects.select_for_update().get_or_create(scout=scout)
    l2.course = level2_course
    l2.discount_code = discount_code

    base, disc, final_amt = _compute_amount(level2_course.id, discount_code)
    l2.base_amount = base
    l2.discount_rupees = disc
    l2.final_amount = final_amt
    l2.status = l2.status or "pending"
    l2.save()

    return JsonResponse({"message": "saved", "final_amount": str(final_amt), "status": l2.status})


@require_POST
@transaction.atomic
def level2_order(request):
    """
    Create Razorpay order for Level-2 final_amount.
    Accepts: ikf_level_1_id OR ikfuniqueid
    """
    try:
        scout = _get_scout_from_request(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    l2 = get_object_or_404(ScoutLevel2, scout=scout)

    # Final safety recompute
    base, disc, final_amt = _compute_amount(l2.course_id, l2.discount_code)
    l2.base_amount, l2.discount_rupees, l2.final_amount = base, disc, final_amt
    l2.save(update_fields=["base_amount", "discount_rupees", "final_amount"])

    amount_paise = int(final_amt * 100)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    resp = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"{scout.ikf_level_1_id or scout.ikfuniqueid}-L2",
        "notes": {"scout_id": scout.id, "level2_id": l2.id},
    })
    l2.order_id = resp.get("id")
    l2.status = "order_created"
    l2.save(update_fields=["order_id", "status"])

    return JsonResponse({"order_id": l2.order_id, "amount": str(final_amt)})


@require_POST
@transaction.atomic
def level2_payment_status(request):
    """
    Called by frontend after successful Razorpay Checkout.
    Expects:
      - ikf_level_1_id or ikfuniqueid
      - razorpay_order_id, razorpay_payment_id, razorpay_signature
    Saves payment to ScoutLevel2, then triggers Interakt/WhatsApp in background.
    """
    try:
        scout = _get_scout_from_request(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    oid = (request.POST.get("razorpay_order_id") or "").strip()
    pid = (request.POST.get("razorpay_payment_id") or "").strip()
    sig = (request.POST.get("razorpay_signature") or "").strip()

    if not oid:
        return HttpResponseBadRequest("razorpay_order_id is required")

    l2 = get_object_or_404(ScoutLevel2, scout=scout, order_id=oid)

    # Verify signature (recommended)
    verified = False
    if pid and sig:
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                "razorpay_order_id": oid,
                "razorpay_payment_id": pid,
                "razorpay_signature": sig,
            })
            verified = True
        except Exception:
            verified = False

    l2.payment_id = pid or l2.payment_id
    l2.payment_signature = sig or l2.payment_signature
    l2.status = "paid" if verified else "paid_unverified"
    l2.save(update_fields=["payment_id", "payment_signature", "status"])

    # Kick off WhatsApp + Interakt
    try:
        t1 = threading.Thread(
            target=send_whatsapp_public_message,
            args=(scout.mobile, scout.first_name or "", scout.last_name or "", l2),
            daemon=True,
        )
        t2 = threading.Thread(
            target=interakt_add_user,
            args=(scout.mobile, scout.first_name or "", scout.last_name or "", l2),
            daemon=True,
        )
        t1.start()
        t2.start()
        # If you prefer blocking until both finish:
        # t1.join(); t2.join()
    except Exception:
        pass

    return JsonResponse({"message": "payment saved", "status": l2.status})




def level2_pass(request):
    """
    Render the Level-2 'Enrollment Pass' fully from server context.
    Accepts query param:
      - ?ikf_level_1_id=...   (preferred)
      - or ?ikfuniqueid=...   (fallback)
      - or ?ikf=...           (either of the above)
    """
    ikf = (request.GET.get("ikf_level_1_id")
           or request.GET.get("ikfuniqueid")
           or request.GET.get("ikf") or "").strip()
    if not ikf:
        return HttpResponseBadRequest("ikf_level_1_id or ikfuniqueid is required")

    scout = Scout.objects.filter(ikf_level_1_id=ikf).first()
    if not scout:
        scout = Scout.objects.filter(ikfuniqueid=ikf).first()
    if not scout:
        return HttpResponseBadRequest("Scout not found")

    # Labels (e.g., {{ aap_khelo_mauka_hum_denge }})
    labels = {}
    if MasterLabels:
        lang = "en"
        for item in MasterLabels.objects.all().values("keydata", lang):
            labels[item["keydata"]] = item[lang]
    if "aap_khelo_mauka_hum_denge" not in labels:
        labels["aap_khelo_mauka_hum_denge"] = "Aap Khelo, Mauka Hum Denge"

    # Name / DOB
    full_name = " ".join(filter(None, [scout.first_name, scout.last_name])) or "Scout Name"
    dob_str = ""
    if getattr(scout, "dob", None):
        try:
            dob_str = scout.dob.strftime("%Y/%m/%d")
        except Exception:
            dob_str = str(scout.dob)

    # Profile photo: fall back by gender
    is_male = (scout.gender or "").lower().startswith("m")
    default_pic = static("img/player/default_profilepic_male.jpg") if is_male else static("img/player/default_profilepic_female.jpg")
    # If you actually store a File/ImageField for pic on Scout, use it; else default
    pic_url = default_pic
    if hasattr(scout, "pic_file") and scout.pic_file:
        try:
            pic_url = scout.pic_file.url
        except Exception:
            pic_url = default_pic

    # Barcode path from your convention
    barcode_url = f"/media/barcode/{scout.ikfuniqueid}.png" if scout.ikfuniqueid else ""

    context = {
        **labels,
        "name": full_name,
        "dob": dob_str,
        "gender_short": f"({(scout.gender or '')[:1].upper()})" if scout.gender else "",
        "pic_file": pic_url,
        "barcode_url": barcode_url,
        "ikfuniqueid": scout.ikfuniqueid or "",
        "ikf_level_1_id": scout.ikf_level_1_id or "",
    }
    return render(request, "player/level2pdf.html", context)
