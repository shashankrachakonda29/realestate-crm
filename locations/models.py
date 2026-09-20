from django.db import models


class Location(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True
    )

    city = models.CharField(
        max_length=100,
        default="Hyderabad"
    )

    state = models.CharField(
        max_length=100,
        default="Telangana"
    )

    pincode = models.CharField(
        max_length=10,
        blank=True
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    google_maps_url = models.URLField(
        blank=True
    )

    description = models.TextField(
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
        return f"{self.name}, {self.city}"