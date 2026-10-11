# property_catalog/models.py

from django.db import models


class PropertyCatalog(models.Model):

    name = models.CharField(
        max_length=200
    )

    version = models.CharField(
        max_length=20,
        default="1.0"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class CatalogDeveloper(models.Model):

    catalog = models.ForeignKey(
        PropertyCatalog,
        on_delete=models.CASCADE,
        related_name="developers"
    )

    name = models.CharField(
        max_length=200
    )

    developer_type = models.CharField(
        max_length=100,
        blank=True
    )

    contact_person = models.CharField(
        max_length=150,
        blank=True
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    website = models.URLField(
        blank=True
    )

    def __str__(self):
        return self.name


class CatalogProject(models.Model):

    developer = models.ForeignKey(
        CatalogDeveloper,
        on_delete=models.CASCADE,
        related_name="projects"
    )

    name = models.CharField(
        max_length=200
    )

    project_type = models.CharField(
        max_length=50
    )

    status = models.CharField(
        max_length=50,
        blank=True
    )

    total_land_area = models.CharField(
        max_length=100,
        blank=True
    )

    total_towers = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    total_floors = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    total_units = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    starting_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    price_per_sqft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    channel_partner_notes = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.name


class CatalogLocation(models.Model):

    project = models.OneToOneField(
        CatalogProject,
        on_delete=models.CASCADE,
        related_name="location"
    )

    locality = models.CharField(
        max_length=150,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    district = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    pincode = models.CharField(
        max_length=10,
        blank=True
    )

    google_maps_url = models.URLField(
        blank=True
    )

    def __str__(self):
        return f"{self.locality}, {self.city}"


class CatalogConfiguration(models.Model):

    PROPERTY_TYPE_CHOICES = [
        ("APARTMENT", "Apartment"),
        ("VILLA", "Villa"),
        ("PLOT", "Plot"),
        ("COMMERCIAL", "Commercial"),
        ("FARM_LAND", "Farm Land"),
        ("OTHER", "Other"),
    ]

    FACING_CHOICES = [
        ("EAST", "East"),
        ("WEST", "West"),
        ("NORTH", "North"),
        ("SOUTH", "South"),
        ("NORTH_EAST", "North-East"),
        ("NORTH_WEST", "North-West"),
        ("SOUTH_EAST", "South-East"),
        ("SOUTH_WEST", "South-West"),
        ("OTHER", "Other"),
    ]

    project = models.ForeignKey(
        CatalogProject,
        on_delete=models.CASCADE,
        related_name="configurations"
    )

    # ==============================
    # BASIC
    # ==============================

    property_type = models.CharField(
        max_length=50,
        choices=PROPERTY_TYPE_CHOICES
    )

    type_name = models.CharField(
        max_length=150
    )

    description = models.TextField(
        blank=True
    )

    # ==============================
    # RESIDENTIAL
    # Apartment / Villa
    # ==============================

    bhk = models.CharField(
        max_length=20,
        blank=True
    )

    bedrooms = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    bathrooms = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    balconies = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    built_up_area_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    carpet_area_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    super_built_up_area_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # ==============================
    # VILLA / PLOT / FARM LAND
    # ==============================

    plot_area_sq_yd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    plot_area_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    road_width_ft = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    # ==============================
    # COMMERCIAL
    # ==============================

    floor = models.CharField(
        max_length=50,
        blank=True
    )

    office_area_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    retail_area_sq_ft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    frontage_ft = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    suitable_for = models.CharField(
        max_length=300,
        blank=True
    )

    # ==============================
    # DIRECTION / PARKING
    # ==============================

    facing = models.CharField(
        max_length=50,
        choices=FACING_CHOICES,
        blank=True
    )

    parking = models.CharField(
        max_length=150,
        blank=True
    )

    parking_count = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    # ==============================
    # PRICE
    # ==============================

    basic_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    price_per_sqft = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    price_per_sqyd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    maintenance_charges = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # ==============================
    # STATUS
    # ==============================

    availability = models.CharField(
        max_length=50,
        blank=True
    )

    possession = models.CharField(
        max_length=100,
        blank=True
    )

    # ==============================
    # FEATURES
    # ==============================

    amenities = models.JSONField(
        default=list,
        blank=True
    )

    features = models.JSONField(
        default=list,
        blank=True
    )

    # ==============================
    # NOTES
    # ==============================

    notes = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.type_name

class CatalogProjectHighlight(models.Model):

    project = models.ForeignKey(
        CatalogProject,
        on_delete=models.CASCADE,
        related_name="highlights"
    )

    text = models.CharField(
        max_length=300
    )

    def __str__(self):
        return self.text


class CatalogProjectAmenity(models.Model):

    project = models.ForeignKey(
        CatalogProject,
        on_delete=models.CASCADE,
        related_name="amenities"
    )

    name = models.CharField(
        max_length=150
    )

    def __str__(self):
        return self.name