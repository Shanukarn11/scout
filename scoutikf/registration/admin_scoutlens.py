from django.contrib import admin, messages

from .models_scoutlens import (
    ScoutLens,
    ScoutLensDiscount,
    ScoutLensFee,
    ScoutLensPageContent,
    ScoutLensPaymentEvent,
)
from .services_scoutlens import ScoutLensPaymentError, reconcile_payment, send_interakt_confirmation


@admin.register(ScoutLens)
class ScoutLensAdmin(admin.ModelAdmin):
    list_display = (
        "registration_id", "player_name", "mobile", "position", "dob", "base_amount", "discount_amount", "amount",
        "status", "payment_verified", "created_at",
        "whatsapp_sent",
    )
    list_filter = ("status", "payment_verified", "whatsapp_sent", "position", "created_at")
    search_fields = (
        "registration_id", "player_name", "mobile", "razorpay_order_id", "razorpay_payment_id",
    )
    ordering = ("-created_at",)
    actions = ("reconcile_selected_payments", "retry_whatsapp_confirmations")
    readonly_fields = (
        "registration_id", "position_rating_group", "fee", "discount", "affiliate_code",
        "base_amount", "discount_amount", "amount", "currency", "status",
        "razorpay_order_id", "razorpay_payment_id", "razorpay_signature", "payment_verified",
        "paid_at", "payment_error_code", "payment_error_description", "payment_error_source",
        "payment_error_reason", "reconciliation_attempts", "last_reconciled_at",
        "last_reconciliation_result", "created_at", "updated_at",
        "whatsapp_sent", "whatsapp_sent_at", "whatsapp_attempts", "whatsapp_last_error",
    )
    fieldsets = (
        ("Player", {"fields": ("registration_id", "player_name", "mobile", "position", "position_rating_group", "dob")}),
        ("Pricing", {"fields": ("fee", "discount", "affiliate_code", "base_amount", "discount_amount", "amount", "currency")}),
        ("Payment", {"fields": ("status", "payment_verified", "paid_at")}),
        ("Razorpay", {"fields": ("razorpay_order_id", "razorpay_payment_id", "razorpay_signature")}),
        ("Failure details", {"classes": ("collapse",), "fields": ("payment_error_code", "payment_error_description", "payment_error_source", "payment_error_reason")}),
        ("Reconciliation", {"fields": ("reconciliation_attempts", "last_reconciled_at", "last_reconciliation_result")}),
        ("WhatsApp / Interakt", {"fields": ("whatsapp_sent", "whatsapp_sent_at", "whatsapp_attempts", "whatsapp_last_error")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    @admin.action(description="Reconcile selected payments with Razorpay")
    def reconcile_selected_payments(self, request, queryset):
        paid_count = 0
        unchanged_count = 0
        error_count = 0
        for registration in queryset[:100]:
            try:
                _, paid, _ = reconcile_payment(registration.pk)
                if paid:
                    paid_count += 1
                else:
                    unchanged_count += 1
            except ScoutLensPaymentError:
                error_count += 1
        self.message_user(
            request,
            f"Reconciliation finished: {paid_count} paid, {unchanged_count} unchanged, {error_count} errors.",
            level=messages.WARNING if error_count else messages.SUCCESS,
        )

    @admin.action(description="Retry ScoutLens WhatsApp confirmations")
    def retry_whatsapp_confirmations(self, request, queryset):
        sent_count = 0
        failed_count = 0
        eligible = queryset.filter(status="paid", payment_verified=True, whatsapp_sent=False)[:100]
        for registration in eligible:
            sent, _ = send_interakt_confirmation(registration.pk)
            if sent:
                sent_count += 1
            else:
                failed_count += 1
        self.message_user(
            request,
            f"WhatsApp retry finished: {sent_count} sent, {failed_count} failed.",
            level=messages.WARNING if failed_count else messages.SUCCESS,
        )


@admin.register(ScoutLensPageContent)
class ScoutLensPageContentAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Registration form", {"fields": (
            "registration_heading", "registration_intro", "mobile_label", "mobile_help",
        )}),
        ("Payment verified message", {"fields": (
            "success_heading", "success_message", "whatsapp_message", "return_button_text",
        )}),
        ("Last change", {"fields": ("updated_at",)}),
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not ScoutLensPageContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(ScoutLensFee)
class ScoutLensFeeAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "position", "amount", "currency", "active", "valid_from", "valid_until", "priority")
    list_filter = ("active", "position", "currency")
    search_fields = ("code", "title")
    ordering = ("-active", "-priority", "title")


@admin.register(ScoutLensDiscount)
class ScoutLensDiscountAdmin(admin.ModelAdmin):
    list_display = ("code", "affiliate_name", "fee", "discount_type", "value", "active", "uses_count", "valid_until")
    list_filter = ("active", "discount_type", "fee")
    search_fields = ("code", "affiliate_name", "fee__code", "fee__title")
    readonly_fields = ("uses_count", "created_at", "updated_at")
    ordering = ("-active", "code")


@admin.register(ScoutLensPaymentEvent)
class ScoutLensPaymentEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "registration", "source", "event_type", "outcome", "provider_payment_id")
    list_filter = ("source", "event_type", "outcome", "created_at")
    search_fields = (
        "registration__registration_id", "registration__player_name", "registration__mobile",
        "provider_order_id", "provider_payment_id", "message",
    )
    readonly_fields = (
        "registration", "source", "event_type", "outcome",
        "provider_order_id", "provider_payment_id", "message", "payload", "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
