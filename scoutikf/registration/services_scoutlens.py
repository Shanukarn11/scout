from decimal import Decimal

import razorpay
import requests
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models_scoutlens import (
    ScoutLens,
    ScoutLensDiscount,
    ScoutLensFee,
    ScoutLensPaymentEvent,
    ScoutLensPaymentStatus,
)
from .models_interakt import InteraktTemplate


class ScoutLensPaymentError(Exception):
    pass


def pricing_quote(position="", affiliate_code=""):
    fee = ScoutLensFee.available(position)
    if not fee:
        raise ScoutLensPaymentError("No active ScoutLens fee is configured for this position.")

    code = (affiliate_code or "").strip().upper()
    discount = None
    discount_amount = Decimal("0.00")
    if code:
        discount = ScoutLensDiscount.objects.select_related("fee").filter(code__iexact=code, fee=fee).first()
        if not discount or not discount.is_available():
            raise ScoutLensPaymentError("This affiliate discount is invalid or no longer active.")
        discount_amount = discount.discount_for(fee.amount)

    final_amount = (fee.amount - discount_amount).quantize(Decimal("0.01"))
    if final_amount <= 0:
        raise ScoutLensPaymentError("The final payment amount must be greater than zero.")
    return fee, discount, fee.amount, discount_amount, final_amount


def razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise ScoutLensPaymentError("Payment service is temporarily unavailable.")
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def record_event(registration, *, source, event_type, outcome="", message="", payload=None,
                 provider_order_id="", provider_payment_id=""):
    return ScoutLensPaymentEvent.objects.create(
        registration=registration,
        source=source,
        event_type=event_type,
        outcome=outcome,
        message=str(message)[:500],
        payload=payload or {},
        provider_order_id=provider_order_id or "",
        provider_payment_id=provider_payment_id or "",
    )


def send_interakt_confirmation(registration_id):
    """Send the ScoutLens confirmation once; failures remain independently retryable."""
    with transaction.atomic():
        registration = ScoutLens.objects.select_for_update().get(pk=registration_id)
        if registration.whatsapp_sent:
            return True, "WhatsApp confirmation was already sent."
        registration.whatsapp_attempts += 1
        registration.save(update_fields=("whatsapp_attempts", "updated_at"))
        # Keep the row lock while sending so simultaneous callbacks/admin retries
        # cannot send the same paid-registration confirmation twice.
        api_key = settings.INTERAKT_API_KEY
        template = InteraktTemplate.configured_for(InteraktTemplate.Project.SCOUT_LENS)
        if not api_key or not template:
            message = "Interakt API key or ScoutLens template is not configured."
            registration.whatsapp_last_error = message
            registration.save(update_fields=("whatsapp_last_error", "updated_at"))
            record_event(
                registration,
                source=ScoutLensPaymentEvent.Source.SYSTEM,
                event_type="whatsapp_not_configured",
                outcome="pending",
                message=message,
            )
            return False, message

        payload = {
            "countryCode": "+91",
            "phoneNumber": registration.mobile,
            "callbackData": f"ScoutLens:{registration.registration_id}",
            "type": "Template",
            "template": {
                "name": template.template_id,
                "languageCode": template.lang_for_template,
                "headerValues": [],
                "bodyValues": [registration.player_name],
            },
        }
        try:
            response = requests.post(
                "https://api.interakt.ai/v1/public/message/",
                headers={"Authorization": f"Basic {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:
            message = f"Interakt confirmation failed: {exc}"[:500]
            registration.whatsapp_last_error = message
            registration.save(update_fields=("whatsapp_last_error", "updated_at"))
            record_event(
                registration,
                source=ScoutLensPaymentEvent.Source.SYSTEM,
                event_type="whatsapp_failed",
                outcome="error",
                message=message,
            )
            return False, message

        registration.whatsapp_sent = True
        registration.whatsapp_sent_at = timezone.now()
        registration.whatsapp_last_error = ""
        registration.save(update_fields=("whatsapp_sent", "whatsapp_sent_at", "whatsapp_last_error", "updated_at"))
        record_event(
            registration,
            source=ScoutLensPaymentEvent.Source.SYSTEM,
            event_type="whatsapp_sent",
            outcome="success",
            message=f"Interakt template {template.template_id} sent successfully.",
        )
        return True, "WhatsApp confirmation sent."


def _payment_matches(registration, payment):
    expected_paise = int(registration.amount * 100)
    if payment.get("order_id") != registration.razorpay_order_id:
        return False, "Payment belongs to a different order."
    if int(payment.get("amount") or 0) != expected_paise:
        return False, "Payment amount does not match the registration amount."
    if (payment.get("currency") or "").upper() != registration.currency:
        return False, "Payment currency does not match."
    if payment.get("status") != "captured":
        return False, f"Payment is {payment.get('status') or 'not captured'} on Razorpay."
    return True, "Captured payment verified with Razorpay."


@transaction.atomic
def mark_paid(registration_id, payment, *, source, signature=""):
    registration = ScoutLens.objects.select_for_update().get(pk=registration_id)
    was_already_paid = registration.status == ScoutLensPaymentStatus.PAID and registration.payment_verified
    if was_already_paid:
        return registration, True, "Payment was already verified."
    matches, message = _payment_matches(registration, payment)
    if not matches:
        registration.status = ScoutLensPaymentStatus.VERIFICATION_PENDING
        registration.last_reconciliation_result = message
        registration.save(update_fields=("status", "last_reconciliation_result", "updated_at"))
        record_event(
            registration,
            source=source,
            event_type="payment_validation",
            outcome="pending",
            message=message,
            payload={"status": payment.get("status"), "amount": payment.get("amount"), "currency": payment.get("currency")},
            provider_order_id=payment.get("order_id", ""),
            provider_payment_id=payment.get("id", ""),
        )
        return registration, False, message

    registration.razorpay_payment_id = payment.get("id")
    if signature:
        registration.razorpay_signature = signature
    registration.payment_verified = True
    registration.status = ScoutLensPaymentStatus.PAID
    registration.paid_at = registration.paid_at or timezone.now()
    registration.payment_error_code = ""
    registration.payment_error_description = ""
    registration.payment_error_source = ""
    registration.payment_error_reason = ""
    registration.last_reconciliation_result = message
    registration.save(update_fields=(
        "razorpay_payment_id", "razorpay_signature", "payment_verified", "status", "paid_at",
        "payment_error_code", "payment_error_description", "payment_error_source",
        "payment_error_reason", "last_reconciliation_result", "updated_at",
    ))
    if registration.discount_id and not registration.discount_counted:
        ScoutLensDiscount.objects.filter(pk=registration.discount_id).update(uses_count=F("uses_count") + 1)
        registration.discount_counted = True
        registration.save(update_fields=("discount_counted", "updated_at"))
    record_event(
        registration,
        source=source,
        event_type="payment_captured",
        outcome="paid",
        message=message,
        payload={"status": payment.get("status"), "amount": payment.get("amount"), "currency": payment.get("currency")},
        provider_order_id=payment.get("order_id", ""),
        provider_payment_id=payment.get("id", ""),
    )
    if not was_already_paid and not registration.whatsapp_sent:
        transaction.on_commit(lambda pk=registration.pk: send_interakt_confirmation(pk))
    return registration, True, message


def reconcile_payment(registration_id, *, source=ScoutLensPaymentEvent.Source.RECONCILIATION):
    with transaction.atomic():
        registration = ScoutLens.objects.select_for_update().get(pk=registration_id)
        registration.reconciliation_attempts += 1
        registration.last_reconciled_at = timezone.now()
        registration.save(update_fields=("reconciliation_attempts", "last_reconciled_at", "updated_at"))

    if registration.status == ScoutLensPaymentStatus.PAID and registration.payment_verified:
        return registration, True, "Payment was already verified."
    if not registration.razorpay_order_id:
        message = "No Razorpay order exists for this registration."
        registration.last_reconciliation_result = message
        registration.save(update_fields=("last_reconciliation_result", "updated_at"))
        return registration, False, message

    client = razorpay_client()
    try:
        if registration.razorpay_payment_id:
            payments = [client.payment.fetch(registration.razorpay_payment_id)]
        else:
            response = client.order.payments(registration.razorpay_order_id)
            payments = response.get("items", []) if isinstance(response, dict) else []
    except Exception as exc:
        message = f"Razorpay reconciliation failed: {exc}"
        registration.last_reconciliation_result = message[:500]
        registration.save(update_fields=("last_reconciliation_result", "updated_at"))
        record_event(
            registration,
            source=source,
            event_type="reconciliation_error",
            outcome="error",
            message=message,
            provider_order_id=registration.razorpay_order_id,
        )
        raise ScoutLensPaymentError("Could not check Razorpay right now. Please try again.") from exc

    captured = next((payment for payment in payments if payment.get("status") == "captured"), None)
    candidate = captured or (payments[0] if payments else None)
    if candidate:
        return mark_paid(registration.pk, candidate, source=source)

    message = "No payment has been recorded against this Razorpay order yet."
    registration.last_reconciliation_result = message
    registration.save(update_fields=("last_reconciliation_result", "updated_at"))
    record_event(
        registration,
        source=source,
        event_type="reconciliation_complete",
        outcome="not_found",
        message=message,
        provider_order_id=registration.razorpay_order_id,
    )
    return registration, False, message
