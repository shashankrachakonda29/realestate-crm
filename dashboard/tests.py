from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from developers.models import Developer
from leads.models import Lead
from projects.models import Project
from sitevisits.models import SiteVisit


class DashboardSalesStatisticsTests(TestCase):
    def test_sales_statistics_are_aggregated_for_the_assigned_user(self):
        admin = get_user_model().objects.create_user(
            username="dashboard-admin",
            password="safe-test-password",
            role="ADMIN",
        )
        sales_user = get_user_model().objects.create_user(
            username="dashboard-sales",
            password="safe-test-password",
            role="SALES",
        )
        Lead.objects.create(
            name="New Lead",
            phone="100",
            status=Lead.Status.NEW,
            assigned_to=sales_user,
            next_follow_up=timezone.now(),
        )
        Lead.objects.create(
            name="Interested Lead",
            phone="101",
            status=Lead.Status.INTERESTED,
            assigned_to=sales_user,
        )
        developer = Developer.objects.create(name="Dashboard Developer")
        project = Project.objects.create(
            name="Dashboard Project",
            developer=developer,
            project_type=Project.ProjectType.VILLAS,
        )
        SiteVisit.objects.create(
            lead=Lead.objects.get(phone="100"),
            project=project,
            assigned_to=sales_user,
            visit_date=timezone.localdate(),
            visit_time=time(12, 0),
            status=SiteVisit.Status.CONFIRMED,
        )
        self.client.force_login(admin)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        stats = response.context["sales_team_stats"]
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]["total_leads"], 2)
        self.assertEqual(stats[0]["new_leads"], 1)
        self.assertEqual(stats[0]["interested_leads"], 1)
        self.assertEqual(stats[0]["followups"], 1)
        self.assertEqual(stats[0]["total_site_visits"], 1)
        self.assertEqual(stats[0]["upcoming_site_visits"], 1)

# Create your tests here.
