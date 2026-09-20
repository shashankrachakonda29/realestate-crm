from django.contrib import admin

from .models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):

    list_display = (
        "unit_number",
        "project",
        "property_type",
        "bhk",
        "facing",
        "unit_price",
        "status",
        "cp_commission_percent",
        "offer_valid_till",
    )

    list_filter = (
        "property_type",
        "status",
        "bhk",
        "facing",
        "project",
    )

    search_fields = (
        "unit_number",
        "project__name",
        "rera_number",
        "source",
    )

    ordering = (
        "project",
        "unit_number",
    )

    fieldsets = (
        (
            "Property Information",
            {
                "fields": (
                    "project",
                    "unit_number",
                    "property_type",
                    "bhk",
                    "plot_size_sq_yards",
                    "plot_size_sq_ft",
                    "saleable_area_sq_ft",
                    "extra_built_up_area_sq_ft",
                    "built_up_area_sq_ft",
                    "facing",
                    "floors",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "current_price",
                    "basic_sale_price_per_sq_ft",
                    "basic_sale_price",
                    "amenities_charges",
                    "facing_charges",
                    "gst_amount",
                    "price_per_sq_ft_incl_gst",
                    "total_unit_cost",
                    "unit_size_sq_ft",
                    "unit_facing",
                    "unit_price",
                    "discount",
                    "booking_amount",
                )
            },
        ),
        (
            "Availability & Payment",
            {
                "fields": (
                    "available_units",
                    "status",
                    "payment_plan",
                    "possession_date",
                    "offer_valid_till",
                )
            },
        ),
        (
            "RERA & Amenities",
            {
                "fields": (
                    "rera_number",
                    "amenities",
                )
            },
        ),
        (
            "CP Commission",
            {
                "fields": (
                    "cp_commission_percent",
                    "commission_terms",
                )
            },
        ),
        (
            "Documents & Links",
            {
                "fields": (
                    "brochure_url",
                    "price_sheet_url",
                    "inventory_sheet_url",
                    "website_url",
                    "google_maps_url",
                )
            },
        ),
        (
            "Tracking",
            {
                "fields": (
                    "source",
                    "date_received",
                    "notes",
                )
            },
        ),
    )