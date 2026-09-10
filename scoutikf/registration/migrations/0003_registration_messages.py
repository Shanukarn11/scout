from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registration", "0002_registrationcontrol"),
    ]

    operations = [
        migrations.RenameField(
            model_name="registrationcontrol",
            old_name="closed_message",
            new_name="common_message",
        ),
        migrations.AlterField(
            model_name="registrationcontrol",
            name="common_message",
            field=models.CharField(blank=True, default="", max_length=300),
        ),
        migrations.AddField(
            model_name="registrationcontrol",
            name="level1_message",
            field=models.CharField(
                default="Level-1 registrations are temporarily closed. Please check back later.",
                max_length=300,
            ),
        ),
        migrations.AddField(
            model_name="registrationcontrol",
            name="level2_message",
            field=models.CharField(
                default="Level-2 registrations are temporarily closed. Please check back later.",
                max_length=300,
            ),
        ),
    ]
