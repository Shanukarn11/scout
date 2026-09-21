from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import RegistrationControl, Scout, ScoutLevel2
from .models_scoutlens import (
    ScoutLens,
    ScoutLensDiscount,
    ScoutLensFee,
    ScoutLensPageContent,
    ScoutLensPaymentEvent,
    ScoutLensPaymentStatus,
    ScoutLensPosition,
    ScoutLensToBeNotifiedPlayer,
)
from .services_scoutlens import mark_paid, reconcile_payment
from .views_scoutlens import _token_for


TEST_SETTINGS = {
    "RAZORPAY_KEY_ID": "rzp_test_example",
    "RAZORPAY_KEY_SECRET": "test-secret",
    "INTERAKT_API_KEY": "test-interakt-key",
    "SCOUTLENS_INTERAKT_TEMPLATE_ID": "scoutlens_registration_confirmation",
    "STORAGES": {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
}


@override_settings(**TEST_SETTINGS)
class ScoutLensRegistrationTests(TestCase):
    def registration_data(self):
        return {
            "player_name": "Aarav Sharma",
            "mobile": "9876543210",
            "position": ScoutLensPosition.GOAL_KEEPERS,
            "dob": "2010-06-15",
        }

    def create_registration(self, **overrides):
        data = {
            "player_name": "Aarav Sharma",
            "mobile": "9876543210",
            "position": ScoutLensPosition.GOAL_KEEPERS,
            "position_rating_group": 1,
            "dob": date(2010, 6, 15),
            "amount": Decimal("1999.00"),
        }
        data.update(overrides)
        return ScoutLens.objects.create(**data)

    def test_scoutlens_admin_changelist_renders_with_mysql(self):
        admin_user = get_user_model().objects.create_superuser(
            username="scoutlens-admin",
            email="admin@example.com",
            password="test-only-password",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:registration_scoutlens_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ScoutLens Registrations")

    def test_registration_and_success_copy_comes_from_admin_content_table(self):
        content = ScoutLensPageContent.current()
        content.mobile_label = "Player WhatsApp number"
        content.mobile_help = "Use the WhatsApp number checked every day."
        content.success_heading = "You are registered"
        content.success_message = "Your ScoutLens seat is confirmed."
        content.whatsapp_message = "Full information will arrive on WhatsApp within 24 hours."
        content.save()

        response = self.client.get(reverse("scout_lens_register"))

        self.assertContains(response, "Player WhatsApp number")
        self.assertContains(response, "Use the WhatsApp number checked every day.")
        self.assertContains(response, 'data-success-heading="You are registered"')
        self.assertContains(response, "Full information will arrive on WhatsApp within 24 hours.")

    def test_landing_shows_five_grouped_positions(self):
        response = self.client.get(reverse("scout_lens"))

        self.assertEqual(response.status_code, 200)
        for label in ("Goal keepers", "Defenders", "Midfielders", "Wingers", "Strikers"):
            self.assertContains(response, label)
        self.assertNotContains(response, "Central Midfielder")
        self.assertContains(response, 'id="scoutlens-notify"')

    def test_notify_me_saves_name_whatsapp_and_position_once(self):
        payload = {
            "name": "Riya Sharma",
            "whatsapp_number": "+91 98765 43210",
            "position": ScoutLensPosition.DEFENDERS,
        }

        first = self.client.post(reverse("scout_lens_notify"), payload)
        second = self.client.post(reverse("scout_lens_notify"), payload)

        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.json()["ok"])
        self.assertEqual(second.status_code, 200)
        self.assertIn("already", second.json()["message"].lower())
        notification = ScoutLensToBeNotifiedPlayer.objects.get()
        self.assertEqual(notification.name, "Riya Sharma")
        self.assertEqual(notification.whatsapp_number, "9876543210")
        self.assertEqual(notification.position, ScoutLensPosition.DEFENDERS)

    def test_notify_me_rejects_invalid_whatsapp_and_position(self):
        response = self.client.post(reverse("scout_lens_notify"), {
            "name": "Riya Sharma",
            "whatsapp_number": "123",
            "position": "Center_Back",
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn("whatsapp_number", response.json()["errors"])
        self.assertIn("position", response.json()["errors"])
        self.assertFalse(ScoutLensToBeNotifiedPlayer.objects.exists())

    def test_registration_switch_blocks_new_scoutlens_payments_only(self):
        control = RegistrationControl.current()
        control.scoutlens_open = False
        control.scoutlens_message = "ScoutLens applications are paused while scouts are busy."
        control.common_message = "Please check again next week."
        control.save()

        landing = self.client.get(reverse("scout_lens"))
        form = self.client.get(reverse("scout_lens_register"))
        start = self.client.post(reverse("scout_lens_start"), self.registration_data())
        order = self.client.post(reverse("scout_lens_order"), {})
        verification = self.client.post(reverse("scout_lens_verify_payment"), {})

        self.assertEqual(landing.status_code, 200)
        self.assertEqual(form.status_code, 200)
        self.assertContains(form, "ScoutLens applications are paused while scouts are busy.")
        self.assertContains(form, "Please check again next week.")
        self.assertNotContains(form, "<header")
        self.assertNotContains(form, "<footer")
        self.assertEqual(form["Cache-Control"], "no-store, no-cache, must-revalidate, max-age=0")
        self.assertEqual(start.status_code, 403)
        self.assertEqual(start.json()["registration_level"], "scoutlens")
        self.assertEqual(order.status_code, 403)
        self.assertEqual(order.json()["registration_level"], "scoutlens")
        self.assertEqual(verification.status_code, 403)
        self.assertNotIn("registration_level", verification.json())
        self.assertFalse(ScoutLens.objects.exists())

    def test_start_creates_only_scoutlens_registration(self):
        response = self.client.post(reverse("scout_lens_start"), self.registration_data())

        self.assertEqual(response.status_code, 200)
        registration = ScoutLens.objects.get()
        self.assertEqual(registration.position_rating_group, 1)
        self.assertEqual(registration.amount, Decimal("1999.00"))
        self.assertEqual(registration.status, ScoutLensPaymentStatus.DRAFT)
        self.assertEqual(Scout.objects.count(), 0)
        self.assertEqual(ScoutLevel2.objects.count(), 0)

    def test_invalid_form_does_not_create_registration(self):
        data = self.registration_data()
        data.update({"mobile": "123", "dob": date.today().isoformat()})

        response = self.client.post(reverse("scout_lens_start"), data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("mobile", response.json()["errors"])
        self.assertIn("dob", response.json()["errors"])
        self.assertFalse(ScoutLens.objects.exists())

    def test_country_code_mobile_is_normalized(self):
        data = self.registration_data()
        data["mobile"] = "+91 98765 43210"

        response = self.client.post(reverse("scout_lens_start"), data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ScoutLens.objects.get().mobile, "9876543210")

    def test_affiliate_link_discount_is_calculated_from_database(self):
        fee = ScoutLensFee.objects.get(code="scoutlens-default")
        ScoutLensDiscount.objects.create(
            fee=fee,
            code="partner20",
            affiliate_name="Test Partner",
            discount_type=ScoutLensDiscount.Type.PERCENT,
            value=Decimal("20.00"),
        )
        data = self.registration_data()
        data["affiliate_code"] = "partner20"

        response = self.client.post(reverse("scout_lens_start"), data)

        self.assertEqual(response.status_code, 200)
        registration = ScoutLens.objects.get()
        self.assertEqual(registration.fee, fee)
        self.assertEqual(registration.discount.code, "PARTNER20")
        self.assertEqual(registration.affiliate_code, "PARTNER20")
        self.assertEqual(registration.base_amount, Decimal("1999.00"))
        self.assertEqual(registration.discount_amount, Decimal("399.80"))
        self.assertEqual(registration.amount, Decimal("1599.20"))

    def test_invalid_affiliate_code_is_rejected_without_registration(self):
        data = self.registration_data()
        data["affiliate_code"] = "NOT-A-REAL-AFFILIATE"

        response = self.client.post(reverse("scout_lens_start"), data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid", response.json()["message"].lower())
        self.assertFalse(ScoutLens.objects.exists())

    def test_missing_fee_keeps_landing_available_and_disables_registration(self):
        ScoutLensFee.objects.all().delete()

        landing = self.client.get(reverse("scout_lens"))
        form = self.client.get(reverse("scout_lens_register"))
        start = self.client.post(reverse("scout_lens_start"), self.registration_data())

        self.assertEqual(landing.status_code, 200)
        self.assertContains(landing, "TBD")
        self.assertNotContains(landing, 'class="mfk-btn-pill-primary"')
        self.assertEqual(form.status_code, 503)
        self.assertContains(form, "fee is not available", status_code=503)
        self.assertEqual(start.status_code, 400)
        self.assertFalse(ScoutLens.objects.exists())

    @patch("registration.views_scoutlens.razorpay_client")
    def test_invalid_razorpay_order_response_is_rejected(self, client_factory):
        registration = self.create_registration()
        client = Mock()
        client.order.create.return_value = {
            "id": "order_bad", "amount": 1, "currency": "INR", "status": "created",
        }
        client_factory.return_value = client

        response = self.client.post(reverse("scout_lens_order"), {
            "payment_token": _token_for(registration),
        })

        self.assertEqual(response.status_code, 502)
        registration.refresh_from_db()
        self.assertIsNone(registration.razorpay_order_id)
        self.assertTrue(ScoutLensPaymentEvent.objects.filter(
            registration=registration, event_type="order_create_invalid_response"
        ).exists())

    @patch("registration.views_scoutlens.razorpay_client")
    def test_captured_payment_is_verified_and_marked_paid(self, client_factory):
        registration = self.create_registration(razorpay_order_id="order_123", status=ScoutLensPaymentStatus.ORDER_CREATED)
        client = Mock()
        client.utility.verify_payment_signature.return_value = None
        client.payment.fetch.return_value = {
            "id": "pay_123", "order_id": "order_123", "amount": 199900,
            "currency": "INR", "status": "captured",
        }
        client_factory.return_value = client

        response = self.client.post(reverse("scout_lens_verify_payment"), {
            "payment_token": _token_for(registration),
            "razorpay_order_id": "order_123",
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": "valid-signature",
        })

        self.assertEqual(response.status_code, 200)
        registration.refresh_from_db()
        self.assertEqual(registration.status, ScoutLensPaymentStatus.PAID)
        self.assertTrue(registration.payment_verified)
        self.assertEqual(registration.razorpay_payment_id, "pay_123")

    @patch("registration.views_scoutlens.razorpay_client")
    def test_invalid_signature_never_marks_payment_paid(self, client_factory):
        registration = self.create_registration(razorpay_order_id="order_123", status=ScoutLensPaymentStatus.ORDER_CREATED)
        client = Mock()
        client.utility.verify_payment_signature.side_effect = ValueError("bad signature")
        client_factory.return_value = client

        response = self.client.post(reverse("scout_lens_verify_payment"), {
            "payment_token": _token_for(registration),
            "razorpay_order_id": "order_123",
            "razorpay_payment_id": "pay_uncertain",
            "razorpay_signature": "bad-signature",
        })

        self.assertEqual(response.status_code, 202)
        registration.refresh_from_db()
        self.assertEqual(registration.status, ScoutLensPaymentStatus.VERIFICATION_PENDING)
        self.assertFalse(registration.payment_verified)

    @patch("registration.views_scoutlens.razorpay_client")
    def test_failed_verification_does_not_reuse_another_registration_payment_id(self, client_factory):
        existing = self.create_registration(
            mobile="9876543211", razorpay_payment_id="pay_duplicate",
        )
        registration = self.create_registration(
            mobile="9876543212", razorpay_order_id="order_new",
            status=ScoutLensPaymentStatus.ORDER_CREATED,
        )
        client = Mock()
        client.utility.verify_payment_signature.side_effect = ValueError("bad signature")
        client_factory.return_value = client

        response = self.client.post(reverse("scout_lens_verify_payment"), {
            "payment_token": _token_for(registration),
            "razorpay_order_id": "order_new",
            "razorpay_payment_id": existing.razorpay_payment_id,
            "razorpay_signature": "bad-signature",
        })

        self.assertEqual(response.status_code, 202)
        registration.refresh_from_db()
        self.assertIsNone(registration.razorpay_payment_id)
        self.assertEqual(registration.status, ScoutLensPaymentStatus.VERIFICATION_PENDING)

    @patch("registration.services_scoutlens.razorpay_client")
    def test_reconciliation_recovers_captured_payment(self, client_factory):
        registration = self.create_registration(razorpay_order_id="order_recovery", status=ScoutLensPaymentStatus.FAILED)
        client = Mock()
        client.order.payments.return_value = {"items": [{
            "id": "pay_recovered", "order_id": "order_recovery", "amount": 199900,
            "currency": "INR", "status": "captured",
        }]}
        client_factory.return_value = client

        registration, paid, _ = reconcile_payment(registration.pk)

        self.assertTrue(paid)
        self.assertEqual(registration.status, ScoutLensPaymentStatus.PAID)
        self.assertTrue(registration.payment_verified)
        self.assertEqual(registration.reconciliation_attempts, 1)

    @patch("registration.services_scoutlens.razorpay_client")
    def test_reconciliation_does_not_accept_wrong_amount(self, client_factory):
        registration = self.create_registration(razorpay_order_id="order_wrong_amount", status=ScoutLensPaymentStatus.FAILED)
        client = Mock()
        client.order.payments.return_value = {"items": [{
            "id": "pay_wrong", "order_id": "order_wrong_amount", "amount": 100,
            "currency": "INR", "status": "captured",
        }]}
        client_factory.return_value = client

        registration, paid, _ = reconcile_payment(registration.pk)

        self.assertFalse(paid)
        self.assertEqual(registration.status, ScoutLensPaymentStatus.VERIFICATION_PENDING)
        self.assertFalse(registration.payment_verified)

    @patch("registration.services_scoutlens.requests.post")
    def test_paid_registration_sends_one_interakt_confirmation(self, post):
        fee = ScoutLensFee.objects.get(code="scoutlens-default")
        discount = ScoutLensDiscount.objects.create(
            fee=fee,
            code="MESSAGE100",
            affiliate_name="Message Partner",
            discount_type=ScoutLensDiscount.Type.FLAT,
            value=Decimal("100.00"),
        )
        registration = self.create_registration(
            fee=fee,
            discount=discount,
            affiliate_code=discount.code,
            base_amount=Decimal("1999.00"),
            discount_amount=Decimal("100.00"),
            amount=Decimal("1899.00"),
            razorpay_order_id="order_message",
        )
        response = Mock()
        response.raise_for_status.return_value = None
        post.return_value = response
        payment = {
            "id": "pay_message", "order_id": "order_message", "amount": 189900,
            "currency": "INR", "status": "captured",
        }

        with self.captureOnCommitCallbacks(execute=True):
            mark_paid(registration.pk, payment, source="reconciliation")

        registration.refresh_from_db()
        self.assertTrue(registration.whatsapp_sent)
        self.assertEqual(registration.whatsapp_attempts, 1)
        discount.refresh_from_db()
        self.assertEqual(discount.uses_count, 1)
        self.assertEqual(post.call_count, 1)
        sent_payload = post.call_args.kwargs["json"]
        self.assertEqual(sent_payload["template"]["name"], "scoutlens_registration_confirmation")
        self.assertEqual(sent_payload["template"]["bodyValues"], ["Aarav Sharma"])

        with self.captureOnCommitCallbacks(execute=True):
            mark_paid(registration.pk, payment, source="reconciliation")
        self.assertEqual(post.call_count, 1)
        discount.refresh_from_db()
        self.assertEqual(discount.uses_count, 1)
        self.assertEqual(ScoutLensPaymentEvent.objects.filter(
            registration=registration, event_type="payment_captured"
        ).count(), 1)
