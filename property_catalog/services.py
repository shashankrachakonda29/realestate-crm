import json

from django.db import transaction

from .models import (
    PropertyCatalog,
    CatalogDeveloper,
    CatalogProject,
    CatalogLocation,
    CatalogConfiguration,
    CatalogProjectHighlight,
    CatalogProjectAmenity,
)


class PropertyCatalogImportError(Exception):
    pass


@transaction.atomic
def import_catalog(data):

    if not isinstance(data, dict):
        raise PropertyCatalogImportError(
            "JSON root must be an object."
        )

    developers = data.get("developers")

    if not isinstance(developers, list):
        raise PropertyCatalogImportError(
            "'developers' must be a list."
        )

    catalog = PropertyCatalog.objects.create(
        name=data.get(
            "catalog_name",
            "Property Catalog"
        ),
        version=data.get(
            "version",
            "1.0"
        ),
    )

    for developer_data in developers:

        if not developer_data.get("name"):
            raise PropertyCatalogImportError(
                "Developer name is required."
            )

        developer = CatalogDeveloper.objects.create(
            catalog=catalog,
            name=developer_data["name"],
            developer_type=developer_data.get(
                "developer_type",
                ""
            ),
            contact_person=developer_data.get(
                "contact_person",
                ""
            ),
            phone=developer_data.get(
                "phone",
                ""
            ),
            email=developer_data.get(
                "email",
                ""
            ),
            website=developer_data.get(
                "website",
                ""
            ),
        )

        projects = developer_data.get(
            "projects",
            []
        )

        if not isinstance(projects, list):
            raise PropertyCatalogImportError(
                f"Projects for '{developer.name}' must be a list."
            )

        for project_data in projects:

            project_details = project_data.get(
                "project_details",
                {}
            )

            project = CatalogProject.objects.create(

                developer=developer,

                name=project_data.get(
                    "name",
                    ""
                ),

                project_type=project_data.get(
                    "project_type",
                    "OTHER"
                ),

                status=project_details.get(
                    "status",
                    ""
                ),

                total_land_area=project_details.get(
                    "total_land_area",
                    ""
                ),

                total_towers=project_details.get(
                    "total_towers"
                ),

                total_floors=project_details.get(
                    "total_floors"
                ),

                total_units=project_details.get(
                    "total_units"
                ),

                starting_price=project_details.get(
                    "starting_price"
                ),

                price_per_sqft=project_details.get(
                    "price_per_sqft"
                ),

                channel_partner_notes=project_data.get(
                    "channel_partner_notes",
                    ""
                ),
            )

            # =========================
            # LOCATION
            # =========================

            location_data = project_data.get(
                "location"
            )

            if location_data:

                CatalogLocation.objects.create(

                    project=project,

                    locality=location_data.get(
                        "locality",
                        ""
                    ),

                    city=location_data.get(
                        "city",
                        ""
                    ),

                    district=location_data.get(
                        "district",
                        ""
                    ),

                    state=location_data.get(
                        "state",
                        ""
                    ),

                    pincode=location_data.get(
                        "pincode",
                        ""
                    ),

                    google_maps_url=location_data.get(
                        "google_maps_url",
                        ""
                    ),
                )

            # =========================
            # HIGHLIGHTS
            # =========================

            highlights = project_data.get(
                "highlights",
                []
            )

            for highlight in highlights:

                if isinstance(highlight, str):

                    CatalogProjectHighlight.objects.create(
                        project=project,
                        text=highlight,
                    )

            # =========================
            # AMENITIES
            # =========================

            amenities = project_data.get(
                "amenities",
                []
            )

            for amenity in amenities:

                if isinstance(amenity, str):

                    CatalogProjectAmenity.objects.create(
                        project=project,
                        name=amenity,
                    )

            # =========================
            # CONFIGURATIONS
            # =========================

            configurations = project_data.get(
                "configurations",
                []
            )

            for configuration_data in configurations:

                CatalogConfiguration.objects.create(

                    project=project,

                    property_type=configuration_data.get(
                        "property_type",
                        "OTHER"
                    ),

                    type_name=configuration_data.get(
                        "type_name",
                        ""
                    ),

                    description=configuration_data.get(
                        "description",
                        ""
                    ),

                    bhk=configuration_data.get(
                        "bhk",
                        ""
                    ),

                    bedrooms=configuration_data.get(
                        "bedrooms"
                    ),

                    bathrooms=configuration_data.get(
                        "bathrooms"
                    ),

                    balconies=configuration_data.get(
                        "balconies"
                    ),

                    built_up_area_sq_ft=configuration_data.get(
                        "built_up_area_sq_ft"
                    ),

                    carpet_area_sq_ft=configuration_data.get(
                        "carpet_area_sq_ft"
                    ),

                    super_built_up_area_sq_ft=configuration_data.get(
                        "super_built_up_area_sq_ft"
                    ),

                    plot_area_sq_yd=configuration_data.get(
                        "plot_area_sq_yd"
                    ),

                    plot_area_sq_ft=configuration_data.get(
                        "plot_area_sq_ft"
                    ),

                    road_width_ft=configuration_data.get(
                        "road_width_ft"
                    ),

                    floor=configuration_data.get(
                        "floor",
                        ""
                    ),

                    office_area_sq_ft=configuration_data.get(
                        "office_area_sq_ft"
                    ),

                    retail_area_sq_ft=configuration_data.get(
                        "retail_area_sq_ft"
                    ),

                    frontage_ft=configuration_data.get(
                        "frontage_ft"
                    ),

                    suitable_for=configuration_data.get(
                        "suitable_for",
                        ""
                    ),

                    facing=configuration_data.get(
                        "facing",
                        ""
                    ),

                    parking=configuration_data.get(
                        "parking",
                        ""
                    ),

                    parking_count=configuration_data.get(
                        "parking_count"
                    ),

                    basic_price=configuration_data.get(
                        "basic_price"
                    ),

                    price_per_sqft=configuration_data.get(
                        "price_per_sqft"
                    ),

                    price_per_sqyd=configuration_data.get(
                        "price_per_sqyd"
                    ),

                    maintenance_charges=configuration_data.get(
                        "maintenance_charges"
                    ),

                    availability=configuration_data.get(
                        "availability",
                        ""
                    ),

                    possession=configuration_data.get(
                        "possession",
                        ""
                    ),

                    amenities=configuration_data.get(
                        "amenities",
                        []
                    ),

                    features=configuration_data.get(
                        "features",
                        []
                    ),

                    notes=configuration_data.get(
                        "notes",
                        ""
                    ),
                )

    return catalog