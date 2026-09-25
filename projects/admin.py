from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "developer",
        "location",
        "project_type",
        "project_status",
        "total_land_acres",
        "total_units",
        "rera_status",
        "is_active",
        "created_at",
    )

    list_filter = (
        "project_type",
        "project_status",
        "rera_status",
        "is_active",
        "location",
        "developer",
    )

    search_fields = (
        "name",
        "developer__name",
        "location__name",
        "rera_number",
    )

    ordering = (
        "name",
    )

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "developer",
                    "location",
                    "project_type",
                    "project_status",
                    "description",
                )
            },
        ),
        (
            "Project Details",
            {
                "fields": (
                    "total_land_acres",
                    "total_land_guntas",
                    "total_units",
                    "bhk",
                    "possession_date",
                )
            },
        ),
        (
            "RERA & Amenities",
            {
                "fields": (
                    "rera_number",
                    "rera_status",
                    "amenities",
                )
            },
        ),
        (
            "Links",
            {
                "fields": (
                    "website",
                    "google_maps_url",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_active",
                )
            },
        ),
    )