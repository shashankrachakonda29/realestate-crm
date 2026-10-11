from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SharedAccessControlTests(TestCase):
    def test_login_authenticates_an_active_user(self):
        user = get_user_model().objects.create_user(
            username="login-user",
            password="safe-test-password",
            role="ADMIN",
        )

        response = self.client.post(
            reverse("login"),
            {"username": user.username, "password": "safe-test-password"},
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_crm_data_routes_require_authentication(self):
        routes = (
            ("developer_list", {}),
            ("developer_create", {}),
            ("developer_detail", {"pk": 1}),
            ("developer_projects", {"pk": 1}),
            ("developer_edit", {"pk": 1}),
            ("developer_delete", {"pk": 1}),
            ("location_list", {}),
            ("location_create", {}),
            ("location_detail", {"pk": 1}),
            ("location_edit", {"pk": 1}),
            ("location_delete", {"pk": 1}),
            ("project_list", {}),
            ("project_create", {}),
            ("project_detail", {"pk": 1}),
            ("project_edit", {"pk": 1}),
            ("project_delete", {"pk": 1}),
            ("project_inventory", {"project_id": 1}),
            ("project_inventory_bhk", {"project_id": 1, "bhk": "2"}),
            ("inventory_list", {}),
            ("inventory_create", {}),
            ("inventory_import", {}),
            ("inventory_detail", {"pk": 1}),
            ("inventory_edit", {"pk": 1}),
            ("inventory_delete", {"pk": 1}),
            ("lead_pipeline", {}),
        )

        for name, kwargs in routes:
            with self.subTest(route=name):
                response = self.client.get(reverse(name, kwargs=kwargs))
                if name == "lead_pipeline":
                    self.assertEqual(response.status_code, 403)
                else:
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response.url.startswith(reverse("login")))

    def test_logout_requires_post_and_uses_csrf_protected_form(self):
        user = get_user_model().objects.create_user(
            username="logout-user",
            password="safe-test-password",
            role="ADMIN",
        )
        self.client.force_login(user)

        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        dashboard = self.client.get(reverse("dashboard"))
        self.assertContains(dashboard, 'method="post" action="/accounts/logout/"')
        self.assertContains(dashboard, "csrfmiddlewaretoken")

        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
