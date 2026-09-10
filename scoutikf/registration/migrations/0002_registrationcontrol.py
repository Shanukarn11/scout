from django.db import migrations, models


def create_default_control(apps, schema_editor):
    RegistrationControl = apps.get_model("registration", "RegistrationControl")
    RegistrationControl.objects.get_or_create(pk=1)


class Migration(migrations.Migration):
    dependencies = [
        ("registration", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RegistrationControl",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level1_open", models.BooleanField(default=True, verbose_name="Level-1 registration open")),
                ("level2_open", models.BooleanField(default=True, verbose_name="Level-2 registration open")),
                ("closed_message", models.CharField(default="Registrations are temporarily closed. Please check back later.", max_length=300)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Registration Control",
                "verbose_name_plural": "Registration Control",
            },
        ),
        migrations.RunPython(create_default_control, migrations.RunPython.noop),
    ]
