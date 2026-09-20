from django.db import models
from django.conf import settings


class Lead(models.Model):

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        CONTACTED = "CONTACTED", "Contacted"
        INTERESTED = "INTERESTED", "Interested"
        SITE_VISIT = "SITE_VISIT", "Site Visit"
        NEGOTIATION = "NEGOTIATION", "Negotiation"
        BOOKED = "BOOKED", "Booked"
        LOST = "LOST", "Lost"
        ON_HOLD = "ON_HOLD", "On Hold"

    class Source(models.TextChoices):
        META_ADS = "META_ADS", "Meta Ads"
        GOOGLE_ADS = "GOOGLE_ADS", "Google Ads"
        WEBSITE = "WEBSITE", "Website"
        INSTAGRAM = "INSTAGRAM", "Instagram"
        FACEBOOK = "FACEBOOK", "Facebook"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        REFERRAL = "REFERRAL", "Referral"
        WALK_IN = "WALK_IN", "Walk In"
        CALL = "CALL", "Direct Call"
        OTHER = "OTHER", "Other"

    name = models.CharField(
        max_length=200
    )

    phone = models.CharField(
        max_length=20
    )

    email = models.EmailField(
        blank=True
    )

    source = models.CharField(
        max_length=30,
        choices=Source.choices,
        default=Source.OTHER
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.NEW
    )

    interested_project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads"
    )

    budget_min = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    budget_max = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    preferred_location = models.CharField(
        max_length=200,
        blank=True
    )

    preferred_property_type = models.CharField(
        max_length=50,
        blank=True
    )

    bhk = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    requirement = models.TextField(
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    next_follow_up = models.DateTimeField(
        null=True,
        blank=True
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_leads"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.name} - {self.phone}"

class LeadActivity(models.Model):

    class ActivityType(models.TextChoices):
        CALL = "CALL", "Call"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        SITE_VISIT = "SITE_VISIT", "Site Visit"
        MEETING = "MEETING", "Meeting"
        FOLLOW_UP = "FOLLOW_UP", "Follow Up"
        NOTE = "NOTE", "Note"

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="activities",
    )

    activity_type = models.CharField(
        max_length=20,
        choices=ActivityType.choices,
    )

    subject = models.CharField(
        max_length=200,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    activity_date = models.DateTimeField()

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_activities",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.lead.name} - {self.get_activity_type_display()}"