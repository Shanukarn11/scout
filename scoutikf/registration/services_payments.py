"""Razorpay verification and recovery for the legacy Scout payment flows.

This module deliberately uses the existing Scout and ScoutLevel2 columns so
deploying payment hardening never rewrites or removes historical data.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import razorpay
from django.conf import settings
from django.db import transaction

from .models import Scout, ScoutCourseDiscount, ScoutLevel2


class PaymentVerificationError(Exception):
    pass


def razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise PaymentVerificationError("Razorpay is not configured.")
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _money(value):
    try:
        return Decimal(str(value or "0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise PaymentVerificationError("The configured payment amount is invalid.")


def level1_amount(scout):
    """Calculate Level-1 pricing from server-owned course/discount tables."""
    if not scout.course_id or not scout.course:
        raise PaymentVerificationError("The Scout course is not configured.")
    amount = _money(scout.course.amount)
    discount = Decimal("0.00")
    if scout.discount:
        row = ScoutCourseDiscount.objects.filter(
            course_id=scout.course_id, type_id=scout.discount
        ).first()
        if row:
            discount = _money(row.discount)
    final = amount - discount
    if final <= 0:
        raise PaymentVerificationError("The final payment amount must be greater than zero.")
    return final


def _validate_payment(payment, *, order_id, expected_amount):
    if not isinstance(payment, dict):
        raise PaymentVerificationError("Razorpay returned an invalid payment response.")
    if payment.get("order_id") != order_id:
        raise PaymentVerificationError("The Razorpay payment belongs to a different order.")
    expected_paise = int(_money(expected_amount) * 100)
    if int(payment.get("amount") or 0) != expected_paise:
        raise PaymentVerificationError("The Razorpay payment amount does not match this registration.")
    if str(payment.get("currency") or "").upper() != "INR":
        raise PaymentVerificationError("The Razorpay payment currency is invalid.")
    if payment.get("status") != "captured":
        raise PaymentVerificationError(
            f"Payment is {payment.get('status') or 'not captured'} on Razorpay."
        )
    return payment


def _captured_payment_for_order(client, order_id):
    response = client.order.payments(order_id)
    items = response.get("items", []) if isinstance(response, dict) else []
    return next((item for item in items if item.get("status") == "captured"), None)


@transaction.atomic
def verify_level1(scout_id, *, order_id, payment_id, signature):
    scout = Scout.objects.select_for_update().select_related("course").get(pk=scout_id)
    if not scout.order_id or order_id != scout.order_id:
        raise PaymentVerificationError("The payment order does not match this Scout registration.")
    client = razorpay_client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
        payment = client.payment.fetch(payment_id)
    except razorpay.errors.SignatureVerificationError as exc:
        raise PaymentVerificationError("Razorpay signature verification failed.") from exc
    except Exception as exc:
        raise PaymentVerificationError("Unable to verify the payment with Razorpay right now.") from exc
    _validate_payment(payment, order_id=order_id, expected_amount=level1_amount(scout))
    already_paid = scout.status == "success" and scout.razorpay_payment_id == payment_id
    scout.status = "success"
    scout.razorpay_order_id = order_id
    scout.razorpay_payment_id = payment_id
    scout.razorpay_signature = signature
    scout.amount = str(level1_amount(scout))
    scout.error_code = scout.error_description = scout.error_source = scout.error_reason = ""
    scout.save(update_fields=(
        "status", "razorpay_order_id", "razorpay_payment_id", "razorpay_signature",
        "amount", "error_code", "error_description", "error_source", "error_reason", "updated_at",
    ))
    return scout, not already_paid


@transaction.atomic
def reconcile_level1(scout_id):
    scout = Scout.objects.select_for_update().select_related("course").get(pk=scout_id)
    if scout.status == "success" and scout.razorpay_payment_id:
        return scout, True, "Payment was already verified."
    if not scout.order_id:
        return scout, False, "No Razorpay order is recorded for this registration."
    try:
        client = razorpay_client()
        payment = _captured_payment_for_order(client, scout.order_id)
        if not payment:
            return scout, False, "No captured payment exists for this Razorpay order yet."
        _validate_payment(payment, order_id=scout.order_id, expected_amount=level1_amount(scout))
    except PaymentVerificationError:
        raise
    except Exception as exc:
        raise PaymentVerificationError("Unable to check Razorpay right now.") from exc
    already_paid = scout.status == "success" and scout.razorpay_payment_id == payment.get("id")
    scout.status = "success"
    scout.razorpay_order_id = scout.order_id
    scout.razorpay_payment_id = payment.get("id", "")
    scout.amount = str(level1_amount(scout))
    scout.error_code = scout.error_description = scout.error_source = scout.error_reason = ""
    scout.save(update_fields=(
        "status", "razorpay_order_id", "razorpay_payment_id", "amount", "error_code",
        "error_description", "error_source", "error_reason", "updated_at",
    ))
    return scout, True, "Captured payment verified with Razorpay." if not already_paid else "Payment was already verified."


def _level2_amount(level2):
    amount = _money(level2.final_amount)
    if amount <= 0:
        raise PaymentVerificationError("The Level-2 payment amount is invalid.")
    return amount


@transaction.atomic
def verify_level2(level2_id, *, order_id, payment_id, signature):
    level2 = ScoutLevel2.objects.select_for_update().select_related("scout").get(pk=level2_id)
    if not level2.order_id or order_id != level2.order_id:
        raise PaymentVerificationError("The payment order does not match this Level-2 registration.")
    client = razorpay_client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
        payment = client.payment.fetch(payment_id)
    except razorpay.errors.SignatureVerificationError as exc:
        raise PaymentVerificationError("Razorpay signature verification failed.") from exc
    except Exception as exc:
        raise PaymentVerificationError("Unable to verify the payment with Razorpay right now.") from exc
    _validate_payment(payment, order_id=order_id, expected_amount=_level2_amount(level2))
    already_paid = level2.status == "paid" and level2.payment_id == payment_id
    level2.status = "paid"
    level2.payment_id = payment_id
    level2.payment_signature = signature
    level2.save(update_fields=("status", "payment_id", "payment_signature", "updated_at"))
    return level2, not already_paid


@transaction.atomic
def reconcile_level2(level2_id):
    level2 = ScoutLevel2.objects.select_for_update().select_related("scout").get(pk=level2_id)
    if level2.status == "paid" and level2.payment_id:
        return level2, True, "Payment was already verified."
    if not level2.order_id:
        return level2, False, "No Razorpay order is recorded for this registration."
    try:
        client = razorpay_client()
        payment = _captured_payment_for_order(client, level2.order_id)
        if not payment:
            return level2, False, "No captured payment exists for this Razorpay order yet."
        _validate_payment(payment, order_id=level2.order_id, expected_amount=_level2_amount(level2))
    except PaymentVerificationError:
        raise
    except Exception as exc:
        raise PaymentVerificationError("Unable to check Razorpay right now.") from exc
    level2.status = "paid"
    level2.payment_id = payment.get("id", "")
    level2.save(update_fields=("status", "payment_id", "updated_at"))
    return level2, True, "Captured payment verified with Razorpay."
