from django.db import models

from developers.models import Developer
from locations.models import Location
# from inventory.models import Inventory


class Project(models.Model):

    class ProjectType(models.TextChoices):
        VILLAS = "VILLAS", "Villas"
        APARTMENTS = "APARTMENTS", "Apartments"
        PLOTS = "PLOTS", "Plots"
        FARM_LANDS = "FARM_LANDS", "Farm Lands"
        COMMERCIAL = "COMMERCIAL", "Commercial"
        OTHER = "OTHER", "Other"

    class ProjectStatus(models.TextChoices):
        COMING_SOON = "COMING_SOON", "Coming Soon"
        PRE_LAUNCH = "PRE_LAUNCH", "Pre Launch"
        LAUNCHED = "LAUNCHED", "Launched"
        UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION", "Under Construction"
        READY_TO_MOVE = "READY_TO_MOVE", "Ready to Move"
        COMPLETED = "COMPLETED", "Completed"
        SOLD_OUT = "SOLD_OUT", "Sold Out"
        ON_HOLD = "ON_HOLD", "On Hold"
        CANCELLED = "CANCELLED", "Cancelled"
        INACTIVE = "INACTIVE", "Inactive"

    name = models.CharField(
        max_length=250
    )

    developer = models.ForeignKey(
        Developer,
        on_delete=models.PROTECT,
        related_name="projects",
        null=True,
        blank=True,
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="projects",
        null=True,
        blank=True,
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

    project_status = models.CharField(
        max_length=30,
        choices=ProjectStatus.choices,
        default=ProjectStatus.COMING_SOON,
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
    # @property
    # def starting_inventory(self):
    #     return (
    #         self.inventory
    #         .filter(
    #             status=Inventory.Status.AVAILABLE,
    #             current_price__isnull=False,
    #         )
    #         .order_by("current_price")
    #         .first()
    #     )

    def __str__(self):
        return self.name