from django.contrib import admin

from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "state",
        "pincode",
        "is_active",
        "created_at",
    )

    list_filter = (
        "city",
        "state",
        "is_active",
    )

    search_fields = (
        "name",
        "city",
        "pincode",
    )

    ordering = (
        "name",
    )