from django.db import migrations, models


def seed_scoutlens_page_content(apps, schema_editor):
    ScoutLensPageContent = apps.get_model("registration", "ScoutLensPageContent")
    ScoutLensPageContent.objects.get_or_create(pk=1)


def remove_scoutlens_page_content(apps, schema_editor):
    ScoutLensPageContent = apps.get_model("registration", "ScoutLensPageContent")
    ScoutLensPageContent.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0005_scoutlensdiscount_scoutlensfee_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScoutLensPageContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("registration_heading", models.CharField(default="Player registration", max_length=160)),
                ("registration_intro", models.CharField(default="Enter the player details below. Your fee is calculated securely on the server.", max_length=300)),
                ("mobile_label", models.CharField(default="WhatsApp number", max_length=100)),
                ("mobile_help", models.CharField(default="Enter an active 10-digit Indian WhatsApp number.", max_length=200)),
                ("success_heading", models.CharField(default="Registration confirmed", max_length=160)),
                ("success_message", models.TextField(default="Your payment is verified and you are successfully registered for IKF ScoutLens.")),
                ("whatsapp_message", models.TextField(default="You will receive a WhatsApp message with all information related to your registration within 24 hours.")),
                ("return_button_text", models.CharField(default="Return to ScoutLens", max_length=100)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "ScoutLens Page Content",
                "verbose_name_plural": "ScoutLens Page Content",
            },
        ),
        migrations.RunPython(seed_scoutlens_page_content, remove_scoutlens_page_content),
    ]
