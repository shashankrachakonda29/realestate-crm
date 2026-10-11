from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from developers.models import Developer
from inventory.models import Inventory
from locations.models import Location
from .models import Project


class ProtectedProjectDeletionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="project-editor",
            password="safe-test-password",
        )
        self.client.force_login(self.user)

    def test_project_starting_price_is_stored_in_crores_on_create_and_edit(self):
        developer = Developer.objects.create(name="Price Developer")
        location = Location.objects.create(name="Price Location")
        payload = {
            "name": "Price Project",
            "developer": str(developer.pk),
            "location": str(location.pk),
            "project_type": Project.ProjectType.VILLAS,
            "project_status": Project.ProjectStatus.LAUNCHED,
            "starting_price": "13.5",
        }

        response = self.client.post(reverse("project_create"), payload)

        self.assertRedirects(response, reverse("project_list"))
        project = Project.objects.get(name="Price Project")
        self.assertEqual(project.starting_price, "13.5")

        response = self.client.post(
            reverse("project_edit", kwargs={"pk": project.pk}),
            {**payload, "starting_price": "15.25"},
        )

        self.assertRedirects(
            response,
            reverse("project_detail", kwargs={"pk": project.pk}),
        )
        project.refresh_from_db()
        self.assertEqual(project.starting_price, "15.25")

    def test_invalid_project_starting_prices_do_not_create_project(self):
        developer = Developer.objects.create(name="Invalid Price Developer")
        location = Location.objects.create(name="Invalid Price Location")
        for value in ("not-a-number", "-1", "NaN", "1e20"):
            with self.subTest(starting_price=value):
                project_name = f"Invalid Price Project {value}"
                response = self.client.post(
                    reverse("project_create"),
                    {
                        "name": project_name,
                        "developer": str(developer.pk),
                        "location": str(location.pk),
                        "project_type": Project.ProjectType.VILLAS,
                        "project_status": Project.ProjectStatus.LAUNCHED,
                        "starting_price": value,
                    },
                    follow=True,
                )

                self.assertEqual(response.status_code, 200)
                self.assertFalse(Project.objects.filter(name=project_name).exists())
                self.assertContains(response, "Starting price")

    def test_project_with_inventory_cannot_be_deleted(self):
        developer = Developer.objects.create(name="Protected Developer")
        project = Project.objects.create(
            name="Protected Project",
            developer=developer,
            project_type=Project.ProjectType.VILLAS,
        )
        Inventory.objects.create(
            project=project,
            property_type=Inventory.PropertyType.VILLA,
        )
        response = self.client.post(
            reverse("project_delete", kwargs={"pk": project.pk}),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())
        self.assertContains(response, "cannot be deleted while it has inventory records")
