from django.conf import settings
from django.db import models

from leads.models import Lead
from projects.models import Project


class SiteVisit(models.Model):

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No Show"
        RESCHEDULED = "RESCHEDULED", "Rescheduled"

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="site_visits",
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="site_visits",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_site_visits",
    )

    visit_date = models.DateField()

    visit_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    notes = models.TextField(
        blank=True,
    )

    outcome = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-visit_date",
            "-visit_time",
        ]

    def __str__(self):
        return f"{self.lead.name} - {self.project.name}"