import django.core.validators
import django.db.models.deletion
import uuid
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0003_registration_messages'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationcontrol',
            name='scoutlens_open',
            field=models.BooleanField(default=True, verbose_name='ScoutLens registration open'),
        ),
        migrations.AddField(
            model_name='registrationcontrol',
            name='scoutlens_message',
            field=models.CharField(default='ScoutLens registrations are temporarily closed. Please check back later.', max_length=300),
        ),
        migrations.CreateModel(
            name='ScoutLens',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('player_name', models.CharField(db_index=True, max_length=200)),
                ('mobile', models.CharField(db_index=True, max_length=10, validators=[django.core.validators.RegexValidator('^[6-9][0-9]{9}$', 'Enter a valid 10-digit Indian mobile number.')])),
                ('position', models.CharField(choices=[('Attacking_Midfielder', 'Attacking Midfielder'), ('Center_Back', 'Center Back'), ('Central_Forward_Striker', 'Central Forward/Striker'), ('Central_Midfielder', 'Central Midfielder'), ('Defensive_Midfielder', 'Defensive Midfielder'), ('Goal_Keeper', 'Goal Keeper'), ('Left_Back', 'Left Back'), ('Left_Midfielder', 'Left Midfielder'), ('Left_Wing', 'Left Wing'), ('Right_Back', 'Right Back'), ('Right_Midfielder', 'Right Midfielder'), ('Right_Wing', 'Right Wing')], db_index=True, max_length=40)),
                ('position_rating_group', models.PositiveSmallIntegerField(db_index=True, editable=False)),
                ('dob', models.DateField(db_index=True)),
                ('amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('order_created', 'Order Created'), ('verification_pending', 'Verification Pending'), ('paid', 'Paid'), ('failed', 'Failed'), ('refunded', 'Refunded')], db_index=True, default='draft', max_length=32)),
                ('razorpay_order_id', models.CharField(blank=True, max_length=191, null=True, unique=True)),
                ('razorpay_payment_id', models.CharField(blank=True, max_length=191, null=True, unique=True)),
                ('razorpay_signature', models.CharField(blank=True, max_length=400, null=True)),
                ('payment_verified', models.BooleanField(db_index=True, default=False)),
                ('paid_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('payment_error_code', models.CharField(blank=True, max_length=100)),
                ('payment_error_description', models.CharField(blank=True, max_length=500)),
                ('payment_error_source', models.CharField(blank=True, max_length=100)),
                ('payment_error_reason', models.CharField(blank=True, max_length=100)),
                ('reconciliation_attempts', models.PositiveIntegerField(default=0)),
                ('last_reconciled_at', models.DateTimeField(blank=True, null=True)),
                ('last_reconciliation_result', models.CharField(blank=True, max_length=500)),
                ('whatsapp_sent', models.BooleanField(db_index=True, default=False)),
                ('whatsapp_sent_at', models.DateTimeField(blank=True, null=True)),
                ('whatsapp_attempts', models.PositiveIntegerField(default=0)),
                ('whatsapp_last_error', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'ScoutLens Registration',
                'verbose_name_plural': 'ScoutLens Registrations',
                'ordering': ('-created_at',),
                'indexes': [models.Index(fields=['mobile', 'created_at'], name='sl_mobile_created_idx'), models.Index(fields=['status', 'created_at'], name='sl_status_created_idx')],
            },
        ),
        migrations.CreateModel(
            name='ScoutLensPaymentEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(choices=[('checkout', 'Checkout'), ('reconciliation', 'Reconciliation'), ('system', 'System')], max_length=20)),
                ('event_type', models.CharField(db_index=True, max_length=100)),
                ('outcome', models.CharField(blank=True, db_index=True, max_length=32)),
                ('provider_order_id', models.CharField(blank=True, db_index=True, max_length=191)),
                ('provider_payment_id', models.CharField(blank=True, db_index=True, max_length=191)),
                ('message', models.CharField(blank=True, max_length=500)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('registration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_events', to='registration.scoutlens')),
            ],
            options={
                'verbose_name': 'ScoutLens Payment Event',
                'verbose_name_plural': 'ScoutLens Payment Events',
                'ordering': ('-created_at',),
            },
        ),
    ]
