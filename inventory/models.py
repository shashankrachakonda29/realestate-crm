from django.db import models

from projects.models import Project


class Inventory(models.Model):

    class PropertyType(models.TextChoices):
        VILLA = "VILLA", "Villa"
        APARTMENT = "APARTMENT", "Apartment"
        PLOT = "PLOT", "Plot"
        COMMERCIAL = "COMMERCIAL", "Commercial"
        FARM_LAND = "FARM_LAND", "Farm Land"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        BLOCKED = "BLOCKED", "Blocked"
        BOOKED = "BOOKED", "Booked"
        SOLD = "SOLD", "Sold"
        ON_HOLD = "ON_HOLD", "On Hold"
        NOT_AVAILABLE = "NOT_AVAILABLE", "Not Available"

    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name="inventory",
    )

    unit_number = models.CharField(
        max_length=100,
    )

    property_type = models.CharField(
        max_length=30,
        choices=PropertyType.choices,
    )

    bhk = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    plot_size_sq_yards = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    plot_size_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    saleable_area_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    built_up_area_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    extra_built_up_area_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    facing = models.CharField(
        max_length=50,
        blank=True,
    )

    floors = models.CharField(
        max_length=100,
        blank=True,
    )

    current_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    gst_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    total_unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    discount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    booking_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )
    basic_sale_price_per_sq_ft = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    basic_sale_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    amenities_charges = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    facing_charges = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    price_per_sq_ft_incl_gst = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    unit_size_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    unit_facing = models.CharField(
        max_length=50,
        blank=True,
    )

    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    available_units = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    cp_commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    commission_terms = models.TextField(
        blank=True,
    )

    offer_valid_till = models.DateField(
        null=True,
        blank=True,
    )

    source = models.CharField(
        max_length=200,
        blank=True,
    )

    date_received = models.DateField(
        null=True,
        blank=True,
    )

    payment_plan = models.TextField(
        blank=True,
    )

    possession_date = models.DateField(
        null=True,
        blank=True,
    )

    rera_number = models.CharField(
        max_length=100,
        blank=True,
    )

    amenities = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )

    notes = models.TextField(
        blank=True,
    )
    brochure_url = models.URLField(
        blank=True,
    )

    price_sheet_url = models.URLField(
        blank=True,
    )

    inventory_sheet_url = models.URLField(
        blank=True,
    )

    website_url = models.URLField(
        blank=True,
    )

    google_maps_url = models.URLField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.project.name} - {self.unit_number}"  