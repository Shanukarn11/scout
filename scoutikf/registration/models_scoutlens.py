from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ScoutLensPosition(models.TextChoices):
    ATTACKING_MIDFIELDER = "Attacking_Midfielder", "Attacking Midfielder"
    CENTER_BACK = "Center_Back", "Center Back"
    CENTRAL_FORWARD_STRIKER = "Central_Forward_Striker", "Central Forward/Striker"
    CENTRAL_MIDFIELDER = "Central_Midfielder", "Central Midfielder"
    DEFENSIVE_MIDFIELDER = "Defensive_Midfielder", "Defensive Midfielder"
    GOAL_KEEPER = "Goal_Keeper", "Goal Keeper"
    LEFT_BACK = "Left_Back", "Left Back"
    LEFT_MIDFIELDER = "Left_Midfielder", "Left Midfielder"
    LEFT_WING = "Left_Wing", "Left Wing"
    RIGHT_BACK = "Right_Back", "Right Back"
    RIGHT_MIDFIELDER = "Right_Midfielder", "Right Midfielder"
    RIGHT_WING = "Right_Wing", "Right Wing"


SCOUTLENS_RATING_GROUPS = {
    ScoutLensPosition.ATTACKING_MIDFIELDER: 2,
    ScoutLensPosition.CENTER_BACK: 3,
    ScoutLensPosition.CENTRAL_FORWARD_STRIKER: 2,
    ScoutLensPosition.CENTRAL_MIDFIELDER: 4,
    ScoutLensPosition.DEFENSIVE_MIDFIELDER: 4,
    ScoutLensPosition.GOAL_KEEPER: 1,
    ScoutLensPosition.LEFT_BACK: 3,
    ScoutLensPosition.LEFT_MIDFIELDER: 4,
    ScoutLensPosition.LEFT_WING: 2,
    ScoutLensPosition.RIGHT_BACK: 3,
    ScoutLensPosition.RIGHT_MIDFIELDER: 4,
    ScoutLensPosition.RIGHT_WING: 2,
}


class ScoutLensPaymentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ORDER_CREATED = "order_created", "Order Created"
    VERIFICATION_PENDING = "verification_pending", "Verification Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class ScoutLensPageContent(models.Model):
    """Admin-editable copy for the standalone ScoutLens registration journey."""

    registration_heading = models.CharField(max_length=160, default="Player registration")
    registration_intro = models.CharField(
        max_length=300,
        default="Enter the player details below. Your fee is calculated securely on the server.",
    )
    mobile_label = models.CharField(max_length=100, default="WhatsApp number")
    mobile_help = models.CharField(
        max_length=200,
        default="Enter an active 10-digit Indian WhatsApp number.",
    )
    success_heading = models.CharField(max_length=160, default="Registration confirmed")
    success_message = models.TextField(
        default="Your payment is verified and you are successfully registered for IKF ScoutLens."
    )
    whatsapp_message = models.TextField(
        default="You will receive a WhatsApp message with all information related to your registration within 24 hours."
    )
    return_button_text = models.CharField(max_length=100, default="Return to ScoutLens")
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def current(cls):
        content, _ = cls.objects.get_or_create(pk=1)
        return content

    def __str__(self):
        return "ScoutLens page content"

    class Meta:
        verbose_name = "ScoutLens Page Content"
        verbose_name_plural = "ScoutLens Page Content"


class ScoutLensFee(models.Model):
    code = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=160)
    position = models.CharField(
        max_length=40, choices=ScoutLensPosition.choices, blank=True,
        help_text="Leave blank to use this as the default fee for every position without a specific fee.",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    active = models.BooleanField(default=True, db_index=True)
    valid_from = models.DateTimeField(blank=True, null=True, db_index=True)
    valid_until = models.DateTimeField(blank=True, null=True, db_index=True)
    priority = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Fee must be greater than zero."})
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValidationError({"valid_until": "Valid until must be later than valid from."})

    @classmethod
    def available(cls, position=""):
        now = timezone.now()
        valid = cls.objects.filter(active=True).filter(
            Q(valid_from__isnull=True) | Q(valid_from__lte=now),
            Q(valid_until__isnull=True) | Q(valid_until__gte=now),
        )
        if position:
            specific = valid.filter(position=position).order_by("-priority", "-id").first()
            if specific:
                return specific
        return valid.filter(position="").order_by("-priority", "-id").first()

    def __str__(self):
        scope = self.get_position_display() if self.position else "Default"
        return f"{self.title} — {scope} — {self.currency} {self.amount}"

    class Meta:
        db_table = "scoutlens_fees"
        ordering = ("-active", "-priority", "title")
        verbose_name = "ScoutLens Fee"
        verbose_name_plural = "ScoutLens Fees"


class ScoutLensDiscount(models.Model):
    class Type(models.TextChoices):
        FLAT = "flat", "Flat amount"
        PERCENT = "percent", "Percentage"

    fee = models.ForeignKey(ScoutLensFee, related_name="discounts", on_delete=models.CASCADE)
    code = models.CharField(
        max_length=80, unique=True, db_index=True,
        help_text="Used in affiliate links, for example ?ref=PARTNER20.",
    )
    affiliate_name = models.CharField(max_length=160, blank=True)
    discount_type = models.CharField(max_length=10, choices=Type.choices, default=Type.FLAT)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True, db_index=True)
    valid_from = models.DateTimeField(blank=True, null=True, db_index=True)
    valid_until = models.DateTimeField(blank=True, null=True, db_index=True)
    uses_count = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.value <= 0:
            raise ValidationError({"value": "Discount must be greater than zero."})
        if self.discount_type == self.Type.PERCENT and self.value > 100:
            raise ValidationError({"value": "Percentage discount cannot exceed 100%."})
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValidationError({"valid_until": "Valid until must be later than valid from."})

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def is_available(self):
        now = timezone.now()
        return (
            self.active
            and (self.valid_from is None or self.valid_from <= now)
            and (self.valid_until is None or self.valid_until >= now)
            and self.fee.active
        )

    def discount_for(self, base_amount):
        if self.discount_type == self.Type.PERCENT:
            discount = (base_amount * self.value / Decimal("100")).quantize(Decimal("0.01"))
        else:
            discount = self.value
        return min(base_amount, discount)

    def __str__(self):
        return f"{self.code} — {self.affiliate_name or 'Affiliate'}"

    class Meta:
        db_table = "scoutlens_discounts"
        ordering = ("-active", "code")
        verbose_name = "ScoutLens Discount"
        verbose_name_plural = "ScoutLens Discounts"


class ScoutLens(models.Model):
    registration_id = models.UUIDField(default=uuid4, unique=True, editable=False, db_index=True)
    player_name = models.CharField(max_length=200, db_index=True)
    mobile = models.CharField(
        max_length=10,
        db_index=True,
        validators=[RegexValidator(r"^[6-9][0-9]{9}$", "Enter a valid 10-digit Indian mobile number.")],
    )
    position = models.CharField(max_length=40, choices=ScoutLensPosition.choices, db_index=True)
    position_rating_group = models.PositiveSmallIntegerField(editable=False, db_index=True)
    dob = models.DateField(db_index=True)

    fee = models.ForeignKey(ScoutLensFee, null=True, on_delete=models.PROTECT, related_name="registrations")
    discount = models.ForeignKey(ScoutLensDiscount, null=True, blank=True, on_delete=models.SET_NULL, related_name="registrations")
    affiliate_code = models.CharField(max_length=80, blank=True, db_index=True)
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(
        max_length=32,
        choices=ScoutLensPaymentStatus.choices,
        default=ScoutLensPaymentStatus.DRAFT,
        db_index=True,
    )

    razorpay_order_id = models.CharField(max_length=191, blank=True, null=True, unique=True)
    razorpay_payment_id = models.CharField(max_length=191, blank=True, null=True, unique=True)
    razorpay_signature = models.CharField(max_length=400, blank=True, null=True)
    payment_verified = models.BooleanField(default=False, db_index=True)
    paid_at = models.DateTimeField(blank=True, null=True, db_index=True)

    payment_error_code = models.CharField(max_length=100, blank=True)
    payment_error_description = models.CharField(max_length=500, blank=True)
    payment_error_source = models.CharField(max_length=100, blank=True)
    payment_error_reason = models.CharField(max_length=100, blank=True)

    reconciliation_attempts = models.PositiveIntegerField(default=0)
    last_reconciled_at = models.DateTimeField(blank=True, null=True)
    last_reconciliation_result = models.CharField(max_length=500, blank=True)

    whatsapp_sent = models.BooleanField(default=False, db_index=True)
    whatsapp_sent_at = models.DateTimeField(blank=True, null=True)
    whatsapp_attempts = models.PositiveIntegerField(default=0)
    whatsapp_last_error = models.CharField(max_length=500, blank=True)
    discount_counted = models.BooleanField(default=False, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.position_rating_group = SCOUTLENS_RATING_GROUPS[self.position]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.player_name} — {self.get_position_display()} — {self.status}"

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "ScoutLens Registration"
        verbose_name_plural = "ScoutLens Registrations"
        indexes = [
            models.Index(fields=("mobile", "created_at"), name="sl_mobile_created_idx"),
            models.Index(fields=("status", "created_at"), name="sl_status_created_idx"),
        ]


class ScoutLensPaymentEvent(models.Model):
    class Source(models.TextChoices):
        CHECKOUT = "checkout", "Checkout"
        RECONCILIATION = "reconciliation", "Reconciliation"
        SYSTEM = "system", "System"

    registration = models.ForeignKey(ScoutLens, related_name="payment_events", on_delete=models.CASCADE)
    source = models.CharField(max_length=20, choices=Source.choices)
    event_type = models.CharField(max_length=100, db_index=True)
    outcome = models.CharField(max_length=32, blank=True, db_index=True)
    provider_order_id = models.CharField(max_length=191, blank=True, db_index=True)
    provider_payment_id = models.CharField(max_length=191, blank=True, db_index=True)
    message = models.CharField(max_length=500, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.registration_id}: {self.event_type} ({self.outcome or 'recorded'})"

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "ScoutLens Payment Event"
        verbose_name_plural = "ScoutLens Payment Events"
