from django.db import migrations, models
import django.core.validators


POSITION_MAP = {
    "Goal_Keeper": "Goal_Keepers",
    "Center_Back": "Defenders",
    "Left_Back": "Defenders",
    "Right_Back": "Defenders",
    "Attacking_Midfielder": "Midfielders",
    "Central_Midfielder": "Midfielders",
    "Defensive_Midfielder": "Midfielders",
    "Left_Midfielder": "Midfielders",
    "Right_Midfielder": "Midfielders",
    "Left_Wing": "Wingers",
    "Right_Wing": "Wingers",
    "Central_Forward_Striker": "Strikers",
}


def group_existing_positions(apps, schema_editor):
    ScoutLens = apps.get_model("registration", "ScoutLens")
    ScoutLensFee = apps.get_model("registration", "ScoutLensFee")
    for old_position, new_position in POSITION_MAP.items():
        ScoutLens.objects.filter(position=old_position).update(position=new_position)
        ScoutLensFee.objects.filter(position=old_position).update(position=new_position)


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0006_scoutlenspagecontent"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScoutLensToBeNotifiedPlayer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=200)),
                ("whatsapp_number", models.CharField(db_index=True, max_length=10, validators=[django.core.validators.RegexValidator("^[6-9][0-9]{9}$", "Enter a valid 10-digit Indian WhatsApp number.")])),
                ("position", models.CharField(choices=[("Goal_Keepers", "Goal keepers"), ("Defenders", "Defenders"), ("Midfielders", "Midfielders"), ("Wingers", "Wingers"), ("Strikers", "Strikers")], db_index=True, max_length=40)),
                ("notified", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "ScoutLens Player To Be Notified",
                "verbose_name_plural": "ScoutLens Players To Be Notified",
                "ordering": ("-created_at",),
            },
        ),
        migrations.RunPython(group_existing_positions, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="scoutlens",
            name="position",
            field=models.CharField(choices=[("Goal_Keepers", "Goal keepers"), ("Defenders", "Defenders"), ("Midfielders", "Midfielders"), ("Wingers", "Wingers"), ("Strikers", "Strikers")], db_index=True, max_length=40),
        ),
        migrations.AlterField(
            model_name="scoutlensfee",
            name="position",
            field=models.CharField(blank=True, choices=[("Goal_Keepers", "Goal keepers"), ("Defenders", "Defenders"), ("Midfielders", "Midfielders"), ("Wingers", "Wingers"), ("Strikers", "Strikers")], help_text="Leave blank to use this as the default fee for every position without a specific fee.", max_length=40),
        ),
        migrations.AddConstraint(
            model_name="scoutlenstobenotifiedplayer",
            constraint=models.UniqueConstraint(fields=("whatsapp_number", "position"), name="unique_scoutlens_notify_number_position"),
        ),
    ]
