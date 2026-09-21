import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


def seed_default_scoutlens_fee(apps, schema_editor):
    ScoutLensFee = apps.get_model('registration', 'ScoutLensFee')
    ScoutLensFee.objects.get_or_create(
        code='scoutlens-default',
        defaults={
            'title': 'ScoutLens Registration',
            'position': '',
            'amount': Decimal('1999.00'),
            'currency': 'INR',
            'active': True,
            'priority': 0,
        },
    )


def remove_seeded_scoutlens_fee(apps, schema_editor):
    ScoutLensFee = apps.get_model('registration', 'ScoutLensFee')
    ScoutLensFee.objects.filter(code='scoutlens-default').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0004_scoutlens_scoutlenspaymentevent'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScoutLensDiscount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, help_text='Used in affiliate links, for example ?ref=PARTNER20.', max_length=80, unique=True)),
                ('affiliate_name', models.CharField(blank=True, max_length=160)),
                ('discount_type', models.CharField(choices=[('flat', 'Flat amount'), ('percent', 'Percentage')], default='flat', max_length=10)),
                ('value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('active', models.BooleanField(db_index=True, default=True)),
                ('valid_from', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('valid_until', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('uses_count', models.PositiveIntegerField(default=0, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'ScoutLens Discount',
                'verbose_name_plural': 'ScoutLens Discounts',
                'db_table': 'scoutlens_discounts',
                'ordering': ('-active', 'code'),
            },
        ),
        migrations.CreateModel(
            name='ScoutLensFee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=80, unique=True)),
                ('title', models.CharField(max_length=160)),
                ('position', models.CharField(blank=True, choices=[('Attacking_Midfielder', 'Attacking Midfielder'), ('Center_Back', 'Center Back'), ('Central_Forward_Striker', 'Central Forward/Striker'), ('Central_Midfielder', 'Central Midfielder'), ('Defensive_Midfielder', 'Defensive Midfielder'), ('Goal_Keeper', 'Goal Keeper'), ('Left_Back', 'Left Back'), ('Left_Midfielder', 'Left Midfielder'), ('Left_Wing', 'Left Wing'), ('Right_Back', 'Right Back'), ('Right_Midfielder', 'Right Midfielder'), ('Right_Wing', 'Right Wing')], help_text='Leave blank to use this as the default fee for every position without a specific fee.', max_length=40)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('active', models.BooleanField(db_index=True, default=True)),
                ('valid_from', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('valid_until', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('priority', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'ScoutLens Fee',
                'verbose_name_plural': 'ScoutLens Fees',
                'db_table': 'scoutlens_fees',
                'ordering': ('-active', '-priority', 'title'),
            },
        ),
        migrations.AddField(
            model_name='scoutlens',
            name='affiliate_code',
            field=models.CharField(blank=True, db_index=True, max_length=80),
        ),
        migrations.AddField(
            model_name='scoutlens',
            name='base_amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='scoutlens',
            name='discount_amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='scoutlens',
            name='discount_counted',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='scoutlens',
            name='discount',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='registrations', to='registration.scoutlensdiscount'),
        ),
        migrations.AddField(
            model_name='scoutlensdiscount',
            name='fee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discounts', to='registration.scoutlensfee'),
        ),
        migrations.AddField(
            model_name='scoutlens',
            name='fee',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='registrations', to='registration.scoutlensfee'),
        ),
        migrations.RunPython(seed_default_scoutlens_fee, remove_seeded_scoutlens_fee),
    ]
