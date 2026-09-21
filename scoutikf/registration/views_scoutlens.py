from django.conf import settings
from django.core import signing
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .forms_scoutlens import ScoutLensNotifyForm, ScoutLensRegistrationForm
from .models_scoutlens import (
    ScoutLens,
    ScoutLensPageContent,
    ScoutLensPaymentEvent,
    ScoutLensPaymentStatus,
    ScoutLensPosition,
    ScoutLensSession,
    ScoutLensToBeNotifiedPlayer,
)
from .registration_control import require_registration_open
from .services_scoutlens import (
    ScoutLensPaymentError,
    mark_paid,
    pricing_quote,
    razorpay_client,
    reconcile_payment,
    record_event,
)


TOKEN_SALT = "registration.scoutlens.payment"


def _token_for(registration):
    return signing.dumps({"id": registration.pk, "registration_id": str(registration.registration_id)}, salt=TOKEN_SALT)


def _registration_from_request(request):
    token = request.POST.get("payment_token", "")
    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=24 * 60 * 60)
    except signing.BadSignature as exc:
        raise ScoutLensPaymentError("This payment session is invalid or has expired.") from exc
    registration = get_object_or_404(ScoutLens, pk=data.get("id"), registration_id=data.get("registration_id"))
    return registration


def _error(message, *, status=400, errors=None):
    payload = {"ok": False, "message": message}
    if errors:
        payload["errors"] = errors
    return JsonResponse(payload, status=status)


@require_GET
def landing(request):
    sessions = []
    for session in ScoutLensSession.objects.filter(active=True):
        try:
            _, _, _, _, amount = pricing_quote(session.position)
        except ScoutLensPaymentError:
            amount = None
        sessions.append({"session": session, "fee": amount})
    return render(request, "scout_lens.html", {
        "scoutlens_sessions": sessions,
    })


@require_POST
def notify_me(request):
    normalized_number = "".join(character for character in request.POST.get("whatsapp_number", "") if character.isdigit())
    if len(normalized_number) == 12 and normalized_number.startswith("91"):
        normalized_number = normalized_number[2:]
    requested_position = request.POST.get("position", "")
    if normalized_number and ScoutLensToBeNotifiedPlayer.objects.filter(
        whatsapp_number=normalized_number,
        position=requested_position,
    ).exists():
        return JsonResponse({
            "ok": True,
            "message": "This WhatsApp number is already on the notification list for this position.",
        })

    form = ScoutLensNotifyForm(request.POST)
    if not form.is_valid():
        errors = {name: [str(error) for error in field_errors] for name, field_errors in form.errors.items()}
        return _error("Please correct the highlighted fields.", errors=errors)

    try:
        with transaction.atomic():
            form.save()
    except IntegrityError:
        return JsonResponse({
            "ok": True,
            "message": "This WhatsApp number is already on the notification list for this position.",
        })
    return JsonResponse({
        "ok": True,
        "message": "You are on the list. We will notify you on WhatsApp when this ScoutLens session opens.",
    })


@require_GET
@require_registration_open(
    "scoutlens",
    page=True,
    template_name="scoutlens/registration_closed.html",
    display_name="ScoutLens",
)
def registration_form(request):
    affiliate_code = (request.GET.get("ref") or request.GET.get("affiliate") or "").strip().upper()[:80]
    requested_position = request.GET.get("position", "")
    if requested_position not in ScoutLensPosition.values:
        requested_position = ""
    affiliate_error = ""
    try:
        _, discount, base_amount, discount_amount, final_amount = pricing_quote(affiliate_code=affiliate_code)
    except ScoutLensPaymentError as exc:
        affiliate_error = str(exc)
        try:
            _, discount, base_amount, discount_amount, final_amount = pricing_quote()
        except ScoutLensPaymentError:
            return render(request, "scoutlens/pricing_unavailable.html", status=503)
    return render(request, "scoutlens/register.html", {
        "page_content": ScoutLensPageContent.current(),
        "form": ScoutLensRegistrationForm(initial={
            "affiliate_code": affiliate_code,
            "position": requested_position,
        }),
        "scoutlens_fee": final_amount,
        "scoutlens_base_fee": base_amount,
        "scoutlens_discount": discount_amount,
        "affiliate_discount": discount,
        "affiliate_error": affiliate_error,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    })


@require_POST
@require_registration_open("scoutlens")
def quote(request):
    try:
        fee, discount, base_amount, discount_amount, final_amount = pricing_quote(
            request.POST.get("position", ""), request.POST.get("affiliate_code", "")
        )
    except ScoutLensPaymentError as exc:
        return _error(str(exc))
    return JsonResponse({
        "ok": True,
        "fee_code": fee.code,
        "base_amount": str(base_amount),
        "discount_amount": str(discount_amount),
        "final_amount": str(final_amount),
        "affiliate_name": discount.affiliate_name if discount else "",
    })


@require_POST
@require_registration_open("scoutlens")
@transaction.atomic
def start_registration(request):
    form = ScoutLensRegistrationForm(request.POST)
    if not form.is_valid():
        errors = {name: [str(error) for error in field_errors] for name, field_errors in form.errors.items()}
        return _error("Please correct the highlighted fields.", errors=errors)

    try:
        fee, discount, base_amount, discount_amount, final_amount = pricing_quote(
            form.cleaned_data["position"], form.cleaned_data["affiliate_code"]
        )
    except ScoutLensPaymentError as exc:
        return _error(str(exc), errors={"affiliate_code": [str(exc)]})

    registration = form.save(commit=False)
    registration.fee = fee
    registration.discount = discount
    registration.affiliate_code = form.cleaned_data["affiliate_code"]
    registration.base_amount = base_amount
    registration.discount_amount = discount_amount
    registration.amount = final_amount
    registration.currency = fee.currency
    registration.status = ScoutLensPaymentStatus.DRAFT
    registration.save()
    record_event(
        registration,
        source=ScoutLensPaymentEvent.Source.SYSTEM,
        event_type="registration_created",
        outcome="draft",
        message="ScoutLens registration created; payment not yet completed.",
    )
    return JsonResponse({
        "ok": True,
        "registration_id": str(registration.registration_id),
        "payment_token": _token_for(registration),
        "amount": str(registration.amount),
        "player_name": registration.player_name,
        "mobile": registration.mobile,
    })


@require_POST
@require_registration_open("scoutlens")
def create_order(request):
    try:
        registration = _registration_from_request(request)
    except ScoutLensPaymentError as exc:
        return _error(str(exc), status=403)

    if registration.status == ScoutLensPaymentStatus.PAID:
        return JsonResponse({"ok": True, "already_paid": True, "registration_id": str(registration.registration_id)})

    with transaction.atomic():
        registration = ScoutLens.objects.select_for_update().get(pk=registration.pk)
        if registration.razorpay_order_id:
            return JsonResponse({
                "ok": True,
                "order_id": registration.razorpay_order_id,
                "amount_paise": int(registration.amount * 100),
                "currency": registration.currency,
            })
        try:
            response = razorpay_client().order.create({
                "amount": int(registration.amount * 100),
                "currency": registration.currency,
                "receipt": f"SL-{registration.pk}-{str(registration.registration_id)[:8]}",
                "notes": {
                    "scoutlens_registration_id": str(registration.registration_id),
                    "position": registration.position,
                },
            })
        except ScoutLensPaymentError as exc:
            return _error(str(exc), status=503)
        except Exception:
            record_event(
                registration,
                source=ScoutLensPaymentEvent.Source.SYSTEM,
                event_type="order_create_failed",
                outcome="error",
                message="Razorpay order creation failed.",
            )
            return _error("We could not start the payment. Please try again.", status=502)

        expected_amount = int(registration.amount * 100)
        order_id = response.get("id") if isinstance(response, dict) else None
        if (
            not order_id
            or int(response.get("amount") or 0) != expected_amount
            or (response.get("currency") or "").upper() != registration.currency
        ):
            record_event(
                registration,
                source=ScoutLensPaymentEvent.Source.SYSTEM,
                event_type="order_create_invalid_response",
                outcome="error",
                message="Razorpay returned an invalid order response.",
            )
            return _error("We could not validate the payment order. Please try again.", status=502)

        registration.razorpay_order_id = order_id
        registration.status = ScoutLensPaymentStatus.ORDER_CREATED
        registration.save(update_fields=("razorpay_order_id", "status", "updated_at"))
        record_event(
            registration,
            source=ScoutLensPaymentEvent.Source.SYSTEM,
            event_type="order_created",
            outcome="success",
            payload={"amount": response.get("amount"), "currency": response.get("currency"), "status": response.get("status")},
            provider_order_id=order_id,
        )

    return JsonResponse({
        "ok": True,
        "order_id": registration.razorpay_order_id,
        "amount_paise": int(registration.amount * 100),
        "currency": registration.currency,
    })


@require_POST
def verify_payment(request):
    try:
        registration = _registration_from_request(request)
    except ScoutLensPaymentError as exc:
        return _error(str(exc), status=403)

    order_id = request.POST.get("razorpay_order_id", "").strip()
    payment_id = request.POST.get("razorpay_payment_id", "").strip()
    signature = request.POST.get("razorpay_signature", "").strip()
    if not all((order_id, payment_id, signature)) or order_id != registration.razorpay_order_id:
        return _error("Invalid payment confirmation.")

    try:
        client = razorpay_client()
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
        payment = client.payment.fetch(payment_id)
    except Exception:
        payment_id_in_use = ScoutLens.objects.exclude(pk=registration.pk).filter(
            razorpay_payment_id=payment_id
        ).exists()
        if not payment_id_in_use:
            registration.razorpay_payment_id = payment_id
        registration.status = ScoutLensPaymentStatus.VERIFICATION_PENDING
        update_fields = ["status", "updated_at"]
        if not payment_id_in_use:
            update_fields.append("razorpay_payment_id")
        registration.save(update_fields=update_fields)
        record_event(
            registration,
            source=ScoutLensPaymentEvent.Source.CHECKOUT,
            event_type="verification_failed",
            outcome="pending",
            message="Checkout returned a payment, but server verification did not complete.",
            provider_order_id=order_id,
            provider_payment_id=payment_id,
        )
        return _error("Payment received but verification is pending. Use Check Payment Status.", status=202)

    registration, paid, message = mark_paid(
        registration.pk,
        payment,
        source=ScoutLensPaymentEvent.Source.CHECKOUT,
        signature=signature,
    )
    return JsonResponse({
        "ok": paid,
        "paid": paid,
        "status": registration.status,
        "registration_id": str(registration.registration_id),
        "message": message,
    }, status=200 if paid else 202)


@require_POST
def payment_failed(request):
    try:
        registration = _registration_from_request(request)
    except ScoutLensPaymentError as exc:
        return _error(str(exc), status=403)

    if registration.status != ScoutLensPaymentStatus.PAID:
        registration.status = ScoutLensPaymentStatus.FAILED
        registration.payment_error_code = request.POST.get("code", "")[:100]
        registration.payment_error_description = request.POST.get("description", "")[:500]
        registration.payment_error_source = request.POST.get("source", "")[:100]
        registration.payment_error_reason = request.POST.get("reason", "")[:100]
        payment_id = request.POST.get("payment_id", "")[:191]
        if payment_id and not ScoutLens.objects.exclude(pk=registration.pk).filter(
            razorpay_payment_id=payment_id
        ).exists():
            registration.razorpay_payment_id = payment_id
        registration.save(update_fields=(
            "status", "payment_error_code", "payment_error_description", "payment_error_source",
            "payment_error_reason", "razorpay_payment_id", "updated_at",
        ))
        record_event(
            registration,
            source=ScoutLensPaymentEvent.Source.CHECKOUT,
            event_type="checkout_failed",
            outcome="failed",
            message=registration.payment_error_description or "Razorpay Checkout reported a failure.",
            provider_order_id=registration.razorpay_order_id or "",
            provider_payment_id=registration.razorpay_payment_id or "",
        )
    return JsonResponse({"ok": True, "status": registration.status})


@require_POST
def reconcile(request):
    try:
        registration = _registration_from_request(request)
        registration, paid, message = reconcile_payment(registration.pk)
    except ScoutLensPaymentError as exc:
        return _error(str(exc), status=502)
    return JsonResponse({
        "ok": True,
        "paid": paid,
        "status": registration.status,
        "registration_id": str(registration.registration_id),
        "message": message,
    })
