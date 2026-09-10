from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import RegistrationControl


class HealthCheckTests(SimpleTestCase):
    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class RegistrationControlTests(TestCase):
    def test_levels_are_open_by_default(self):
        control = RegistrationControl.current()
        self.assertTrue(control.level1_open)
        self.assertTrue(control.level2_open)

    def test_closed_level1_blocks_form_and_save_endpoint(self):
        control = RegistrationControl.current()
        control.level1_open = False
        control.closed_message = "Level 1 is paused."
        control.save()

        page = self.client.get(reverse("scoutpage", args=["en", "Scout"]))
        save = self.client.post(reverse("save"))

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Level 1 is paused.")
        self.assertEqual(page["Cache-Control"], "no-store, no-cache, must-revalidate, max-age=0")
        self.assertEqual(save.status_code, 403)
        self.assertEqual(save.json()["registration_level"], 1)

    def test_closed_level2_blocks_form_and_save_endpoint(self):
        control = RegistrationControl.current()
        control.level2_open = False
        control.closed_message = "Level 2 is paused."
        control.save()

        page = self.client.get(reverse("level2_form"))
        save = self.client.post(reverse("level2_save"))

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Level 2 is paused.")
        self.assertEqual(page["Cache-Control"], "no-store, no-cache, must-revalidate, max-age=0")
        self.assertEqual(save.status_code, 403)
        self.assertEqual(save.json()["registration_level"], 2)
