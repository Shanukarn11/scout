from datetime import date

from django.db import migrations, models


SESSIONS = (
    ("Goal_Keepers", "Goal keepers", date(2026, 10, 2), True, 10),
    ("Defenders", "Defenders", None, False, 20),
    ("Midfielders", "Midfielders", None, False, 30),
    ("Wingers", "Wingers", None, False, 40),
    ("Strikers", "Strikers", None, False, 50),
)


def seed_scoutlens_sessions(apps, schema_editor):
    ScoutLensSession = apps.get_model("registration", "ScoutLensSession")
    for position, display_name, session_date, registration_open, display_order in SESSIONS:
        ScoutLensSession.objects.get_or_create(
            position=position,
            defaults={
                "display_name": display_name,
                "session_date": session_date,
                "mode": "Live Online",
                "duration": "2–3 hours",
                "registration_open": registration_open,
                "active": True,
                "display_order": display_order,
            },
        )


def remove_seeded_scoutlens_sessions(apps, schema_editor):
    ScoutLensSession = apps.get_model("registration", "ScoutLensSession")
    ScoutLensSession.objects.filter(position__in=[row[0] for row in SESSIONS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0007_scoutlenstobenotifiedplayer_positions"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScoutLensSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position", models.CharField(choices=[("Goal_Keepers", "Goal keepers"), ("Defenders", "Defenders"), ("Midfielders", "Midfielders"), ("Wingers", "Wingers"), ("Strikers", "Strikers")], max_length=40, unique=True)),
                ("display_name", models.CharField(blank=True, help_text="Optional public title. Leave blank to use the position name.", max_length=160)),
                ("session_date", models.DateField(blank=True, db_index=True, null=True)),
                ("session_time", models.CharField(blank=True, help_text="For example: 10:00 AM IST", max_length=100)),
                ("mode", models.CharField(default="Live Online", max_length=100)),
                ("duration", models.CharField(blank=True, default="2–3 hours", max_length=100)),
                ("registration_open", models.BooleanField(db_index=True, default=False)),
                ("active", models.BooleanField(db_index=True, default=True, help_text="Uncheck to hide this card from /ScoutLens.")),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "ScoutLens Session",
                "verbose_name_plural": "ScoutLens Sessions",
                "ordering": ("display_order", "id"),
            },
        ),
        migrations.RunPython(seed_scoutlens_sessions, remove_seeded_scoutlens_sessions),
    ]
