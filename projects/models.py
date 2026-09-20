from django.db import models

from developers.models import Developer
from locations.models import Location


class Project(models.Model):

    class ProjectType(models.TextChoices):
        VILLAS = "VILLAS", "Villas"
        APARTMENTS = "APARTMENTS", "Apartments"
        PLOTS = "PLOTS", "Plots"
        FARM_LANDS = "FARM_LANDS", "Farm Lands"
        COMMERCIAL = "COMMERCIAL", "Commercial"
        OTHER = "OTHER", "Other"

    name = models.CharField(
        max_length=250
    )

    developer = models.ForeignKey(
        Developer,
        on_delete=models.PROTECT,
        related_name="projects"
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="projects"
    )

    project_type = models.CharField(
        max_length=30,
        choices=ProjectType.choices
    )

    description = models.TextField(
        blank=True
    )

    total_land_acres = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    total_land_guntas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    total_units = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    bhk = models.CharField(
        max_length=100,
        blank=True
    )

    possession_date = models.DateField(
        null=True,
        blank=True
    )

    rera_number = models.CharField(
        max_length=100,
        blank=True
    )

    rera_status = models.CharField(
        max_length=50,
        blank=True
    )

    amenities = models.TextField(
        blank=True
    )

    website = models.URLField(
        blank=True
    )

    google_maps_url = models.URLField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name