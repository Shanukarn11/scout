from django.db import models


class InteraktTemplate(models.Model):
    class Project(models.TextChoices):
        SCOUT = "scout", "Scout (Level 1)"
        LEVEL_2 = "level_2", "Scout Level 2"
        SCOUT_LENS = "scout_lens", "ScoutLens"

    project_name = models.CharField(max_length=40, choices=Project.choices, unique=True)
    template_id = models.CharField(max_length=160)
    lang_for_template = models.CharField(
        max_length=20,
        default="en",
        help_text="Interakt template language code, for example en or hi.",
    )
    active = models.BooleanField(default=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def configured_for(cls, project_name):
        try:
            return cls.objects.get(project_name=project_name, active=True)
        except cls.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.get_project_name_display()} — {self.template_id} ({self.lang_for_template})"

    class Meta:
        ordering = ("project_name",)
        verbose_name = "Interakt Template"
        verbose_name_plural = "Interakt Templates"
