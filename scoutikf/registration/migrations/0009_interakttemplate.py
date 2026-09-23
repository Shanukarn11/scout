from django.db import migrations, models


DEFAULT_TEMPLATES = (
    ("scout", "scouting_certification_2025", "en"),
    ("level_2", "cfsa_level_2_certification", "en"),
    ("scout_lens", "scoutlens_registration_confirmation", "en"),
)


def seed_interakt_templates(apps, schema_editor):
    InteraktTemplate = apps.get_model("registration", "InteraktTemplate")
    for project_name, template_id, language in DEFAULT_TEMPLATES:
        InteraktTemplate.objects.get_or_create(
            project_name=project_name,
            defaults={
                "template_id": template_id,
                "lang_for_template": language,
                "active": True,
            },
        )


def remove_seeded_interakt_templates(apps, schema_editor):
    InteraktTemplate = apps.get_model("registration", "InteraktTemplate")
    InteraktTemplate.objects.filter(project_name__in=[row[0] for row in DEFAULT_TEMPLATES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0008_scoutlenssession"),
    ]

    operations = [
        migrations.CreateModel(
            name="InteraktTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("project_name", models.CharField(choices=[("scout", "Scout (Level 1)"), ("level_2", "Scout Level 2"), ("scout_lens", "ScoutLens")], max_length=40, unique=True)),
                ("template_id", models.CharField(max_length=160)),
                ("lang_for_template", models.CharField(default="en", help_text="Interakt template language code, for example en or hi.", max_length=20)),
                ("active", models.BooleanField(db_index=True, default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Interakt Template",
                "verbose_name_plural": "Interakt Templates",
                "ordering": ("project_name",),
            },
        ),
        migrations.RunPython(seed_interakt_templates, remove_seeded_interakt_templates),
    ]
