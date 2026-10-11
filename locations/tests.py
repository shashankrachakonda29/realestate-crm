from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from developers.models import Developer
from projects.models import Project
from .models import Location


class ProtectedLocationDeletionTests(TestCase):
    def test_location_used_by_project_cannot_be_deleted(self):
        user = get_user_model().objects.create_user(
            username="location-delete-user",
            password="safe-test-password",
        )
        location = Location.objects.create(name="Protected Location")
        developer = Developer.objects.create(name="Location Developer")
        project = Project.objects.create(
            name="Location Project",
            developer=developer,
            location=location,
            project_type=Project.ProjectType.VILLAS,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("location_delete", kwargs={"pk": location.pk}),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Location.objects.filter(pk=location.pk).exists())
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())
        self.assertContains(response, "cannot be deleted because it is used by a project")

# Create your tests here.
