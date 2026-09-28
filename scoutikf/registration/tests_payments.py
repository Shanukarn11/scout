from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import MasterSeason, Scout, ScoutCourse, ScoutLevel2
from .services_payments import (
    PaymentVerificationError,
    reconcile_level1,
    reconcile_level2,
    verify_level1,
    verify_level2,
)


PAYMENT_SETTINGS = {
    "RAZORPAY_KEY_ID": "rzp_test_example",
    "RAZORPAY_KEY_SECRET": "test-secret",
    "INTERAKT_API_KEY": "",
    "SECURE_SSL_REDIRECT": False,
    "STORAGES": {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
}


@override_settings(**PAYMENT_SETTINGS)
class PaymentSafetyTests(TestCase):
    def setUp(self):
        season = MasterSeason.objects.create(id="S05", en="Season 5", year=2026)
        self.course = ScoutCourse.objects.create(id="L1", course="Level 1", amount="500.00")
        self.scout = Scout.objects.create(
            ikfuniqueid="IKFS05M000001",
            first_name="Test",
            last_name="Scout",
            mobile="9876543210",
            gender="Male",
            dob=date(2008, 1, 1),
            season=season,
            course=self.course,
            order_id="order_level1",
            amount="500.00",
            status="created",
        )
        self.level2 = ScoutLevel2.objects.create(
            scout=self.scout,
            course=self.course,
            final_amount=Decimal("750.00"),
            order_id="order_level2",
            status="order_created",
        )

    @staticmethod
    def client_for(payment):
        client = Mock()
        client.payment.fetch.return_value = payment
        client.order.payments.return_value = {"items": [payment]}
        return client

    @patch("registration.services_payments.razorpay_client")
    def test_level1_verification_requires_captured_matching_payment(self, client_factory):
        payment = {
            "id": "pay_level1", "order_id": "order_level1", "amount": 50000,
            "currency": "INR", "status": "captured",
        }
        client_factory.return_value = self.client_for(payment)

        scout, newly_paid = verify_level1(
            self.scout.pk,
            order_id="order_level1",
            payment_id="pay_level1",
            signature="valid-signature",
        )

        self.assertTrue(newly_paid)
        self.assertEqual(scout.status, "success")
        self.assertEqual(scout.razorpay_payment_id, "pay_level1")

    @patch("registration.services_payments.razorpay_client")
    def test_level1_rejects_amount_mismatch_without_marking_paid(self, client_factory):
        payment = {
            "id": "pay_wrong", "order_id": "order_level1", "amount": 100,
            "currency": "INR", "status": "captured",
        }
        client_factory.return_value = self.client_for(payment)

        with self.assertRaises(PaymentVerificationError):
            verify_level1(
                self.scout.pk,
                order_id="order_level1",
                payment_id="pay_wrong",
                signature="valid-signature",
            )

        self.scout.refresh_from_db()
        self.assertNotEqual(self.scout.status, "success")
        self.assertFalse(self.scout.razorpay_payment_id)

    @patch("registration.services_payments.razorpay_client")
    def test_level1_reconciliation_recovers_captured_payment(self, client_factory):
        payment = {
            "id": "pay_recovered", "order_id": "order_level1", "amount": 50000,
            "currency": "INR", "status": "captured",
        }
        client_factory.return_value = self.client_for(payment)

        scout, paid, _ = reconcile_level1(self.scout.pk)

        self.assertTrue(paid)
        self.assertEqual(scout.status, "success")
        self.assertEqual(scout.razorpay_payment_id, "pay_recovered")

    @patch("registration.services_payments.razorpay_client")
    def test_level2_verification_checks_captured_amount_and_currency(self, client_factory):
        payment = {
            "id": "pay_level2", "order_id": "order_level2", "amount": 75000,
            "currency": "INR", "status": "captured",
        }
        client_factory.return_value = self.client_for(payment)

        level2, newly_paid = verify_level2(
            self.level2.pk,
            order_id="order_level2",
            payment_id="pay_level2",
            signature="valid-signature",
        )

        self.assertTrue(newly_paid)
        self.assertEqual(level2.status, "paid")
        self.assertEqual(level2.payment_id, "pay_level2")

    @patch("registration.services_payments.razorpay_client")
    def test_level2_reconciliation_recovers_captured_payment(self, client_factory):
        payment = {
            "id": "pay_l2_recovered", "order_id": "order_level2", "amount": 75000,
            "currency": "INR", "status": "captured",
        }
        client_factory.return_value = self.client_for(payment)

        level2, paid, _ = reconcile_level2(self.level2.pk)

        self.assertTrue(paid)
        self.assertEqual(level2.status, "paid")
        self.assertEqual(level2.payment_id, "pay_l2_recovered")

    @patch("registration.views.razorpay.Client")
    def test_level1_order_ignores_browser_amount_and_uses_server_price(self, client_class):
        client_class.return_value.order.create.return_value = {
            "id": "order_server_priced", "amount": 50000, "currency": "INR",
        }

        response = self.client.post(reverse("order"), {
            "ikfuniqueid": self.scout.ikfuniqueid,
            "id": self.scout.pk,
            "amount": "1",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["amount"], "500.00")
        sent = client_class.return_value.order.create.call_args.kwargs["data"]
        self.assertEqual(sent["amount"], 50000)
        self.scout.refresh_from_db()
        self.assertEqual(self.scout.order_id, "order_server_priced")
        self.assertEqual(self.scout.amount, "500.00")

    @patch("registration.views_level2.razorpay.Client")
    def test_level2_order_uses_recomputed_server_price(self, client_class):
        client_class.return_value.order.create.return_value = {
            "id": "order_l2_server", "amount": 50000, "currency": "INR",
        }

        response = self.client.post(reverse("level2_order"), {
            "ikfuniqueid": self.scout.ikfuniqueid,
            "amount": "1",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["amount"], "500.00")
        sent = client_class.return_value.order.create.call_args.args[0]
        self.assertEqual(sent["amount"], 50000)
        self.level2.refresh_from_db()
        self.assertEqual(self.level2.order_id, "order_l2_server")

    @patch("registration.services_payments.razorpay_client")
    def test_level2_does_not_accept_authorized_but_uncaptured_payment(self, client_factory):
        payment = {
            "id": "pay_authorized", "order_id": "order_level2", "amount": 75000,
            "currency": "INR", "status": "authorized",
        }
        client_factory.return_value = self.client_for(payment)

        with self.assertRaises(PaymentVerificationError):
            verify_level2(
                self.level2.pk,
                order_id="order_level2",
                payment_id="pay_authorized",
                signature="valid-signature",
            )

        self.level2.refresh_from_db()
        self.assertNotEqual(self.level2.status, "paid")
        self.assertFalse(self.level2.payment_id)

    @patch("registration.services_payments.razorpay_client")
    def test_repeated_level1_callback_is_idempotent(self, client_factory):
        payment = {
            "id": "pay_once", "order_id": "order_level1", "amount": 50000,
            "currency": "INR", "status": "captured",
        }
        client_factory.return_value = self.client_for(payment)

        _, first_is_new = verify_level1(
            self.scout.pk, order_id="order_level1", payment_id="pay_once", signature="signature"
        )
        _, second_is_new = verify_level1(
            self.scout.pk, order_id="order_level1", payment_id="pay_once", signature="signature"
        )

        self.assertTrue(first_is_new)
        self.assertFalse(second_is_new)

    def test_reconciliation_requires_registration_and_order_to_match(self):
        response = self.client.post(reverse("reconcile_scout_payment"), {
            "ikfuniqueid": self.scout.ikfuniqueid,
            "order_id": "order_belonging_to_someone_else",
        })

        self.assertEqual(response.status_code, 404)

    def test_level1_payment_page_uses_environment_key_and_has_recovery(self):
        response = self.client.get(reverse("payment"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rzp_test_example")
        self.assertContains(response, "Check payment status")
        self.assertNotContains(response, "rzp_live_")

    def test_level1_registration_uses_scoutlens_visual_language_without_changing_fields(self):
        response = self.client.get(reverse("scoutpage", args=("en", "Scout")))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="l1-card"')
        self.assertContains(response, "IKF Scout • Level 1")
        self.assertContains(response, "Registration details")
        self.assertContains(response, "Secure payment")
        for field_id in (
            "first_name", "last_name", "gender", "dob", "email", "mobile",
            "associated_years", "course1", "course2", "course3",
        ):
            self.assertContains(response, f'id="{field_id}"')

    def test_level2_page_has_reconciliation_control(self):
        response = self.client.get(reverse("level2_form"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="btnReconcile"')
        self.assertContains(response, reverse("level2_reconcile"))

    def _login_admin(self):
        admin = get_user_model().objects.create_superuser(
            username="payment-admin", email="admin@example.com", password="test-password"
        )
        self.client.force_login(admin)

    def test_registration_control_changelist_has_inline_save_and_message_link(self):
        from .models import RegistrationControl

        RegistrationControl.current()
        self._login_admin()

        response = self.client.get(reverse("admin:registration_registrationcontrol_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="_save"')
        self.assertContains(response, "Edit messages")

    @patch("registration.admin.reconcile_level1")
    def test_level1_admin_reconciliation_action(self, reconcile):
        reconcile.return_value = (self.scout, True, "Captured payment verified with Razorpay.")
        self._login_admin()

        response = self.client.post(reverse("admin:registration_scout_changelist"), {
            "action": "reconcile_selected_payments",
            "_selected_action": str(self.scout.pk),
            "index": "0",
        })

        self.assertEqual(response.status_code, 302)
        reconcile.assert_called_once_with(self.scout.pk)

    @patch("registration.admin.reconcile_level2")
    def test_level2_admin_reconciliation_action(self, reconcile):
        reconcile.return_value = (self.level2, True, "Captured payment verified with Razorpay.")
        self._login_admin()

        response = self.client.post(reverse("admin:registration_scoutlevel2_changelist"), {
            "action": "reconcile_selected_payments",
            "_selected_action": str(self.level2.pk),
            "index": "0",
        })

        self.assertEqual(response.status_code, 302)
        reconcile.assert_called_once_with(self.level2.pk)

    @patch("registration.views.reconcile_level1")
    def test_level1_customer_reconciliation_endpoint(self, reconcile):
        reconcile.return_value = (self.scout, False, "No captured payment exists yet.")

        response = self.client.post(reverse("reconcile_scout_payment"), {
            "ikfuniqueid": self.scout.ikfuniqueid,
            "order_id": self.scout.order_id,
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["paid"])

    @patch("registration.views_level2.reconcile_level2")
    def test_level2_customer_reconciliation_endpoint(self, reconcile):
        reconcile.return_value = (self.level2, False, "No captured payment exists yet.")

        response = self.client.post(reverse("level2_reconcile"), {
            "ikfuniqueid": self.scout.ikfuniqueid,
            "order_id": self.level2.order_id,
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["paid"])
