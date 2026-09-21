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
class ScoutLensPageTests(TestCase):
    def test_scout_lens_url_is_case_insensitive(self):
        for url in ("/ScoutLens", "/scoutlens", "/SCOUTLENS/", "/sCoUtLeNs"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "IKF ScoutLens")

    def test_scout_lens_is_standalone(self):
        response = self.client.get(reverse("scout_lens"))

        self.assertContains(response, 'id="scoutlens-main"')
        self.assertNotContains(response, "<header")
        self.assertNotContains(response, "<footer")


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class RegistrationControlTests(TestCase):
    def test_levels_are_open_by_default(self):
        control = RegistrationControl.current()
        self.assertTrue(control.level1_open)
        self.assertTrue(control.level2_open)
        self.assertTrue(control.scoutlens_open)

    def test_closed_level1_blocks_form_and_save_endpoint(self):
        control = RegistrationControl.current()
        control.level1_open = False
        control.level1_message = "Level 1 is paused."
        control.level2_message = "Level 2 should not appear."
        control.common_message = "Our team is reviewing applications."
        control.save()

        page = self.client.get(reverse("scoutpage", args=["en", "Scout"]))
        save = self.client.post(reverse("save"))

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Level 1 is paused.")
        self.assertContains(page, "Our team is reviewing applications.")
        self.assertNotContains(page, "Level 2 should not appear.")
        self.assertEqual(page["Cache-Control"], "no-store, no-cache, must-revalidate, max-age=0")
        self.assertEqual(save.status_code, 403)
        self.assertEqual(save.json()["registration_level"], 1)

    def test_closed_level2_blocks_form_and_save_endpoint(self):
        control = RegistrationControl.current()
        control.level2_open = False
        control.level1_message = "Level 1 should not appear."
        control.level2_message = "Level 2 is paused."
        control.common_message = ""
        control.save()

        page = self.client.get(reverse("level2_form"))
        save = self.client.post(reverse("level2_save"))

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Level 2 is paused.")
        self.assertNotContains(page, "Level 1 should not appear.")
        self.assertNotContains(page, '<p class="registration-paused__note">')
        self.assertEqual(page["Cache-Control"], "no-store, no-cache, must-revalidate, max-age=0")
        self.assertEqual(save.status_code, 403)
        self.assertEqual(save.json()["registration_level"], 2)
