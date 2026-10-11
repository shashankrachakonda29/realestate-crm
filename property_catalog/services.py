from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    CatalogConfiguration,
    CatalogDeveloper,
    CatalogLocation,
    CatalogProject,
    CatalogProjectAmenity,
    CatalogProjectHighlight,
    PropertyCatalog,
)


class PropertyCatalogImportError(Exception):
    pass


DEVELOPER_FIELDS = (
    "developer_type",
    "contact_person",
    "phone",
    "email",
    "website",
)
PROJECT_DETAIL_FIELDS = (
    "status",
    "total_land_area",
    "total_towers",
    "total_floors",
    "total_units",
    "starting_price",
    "price_per_sqft",
)
LOCATION_FIELDS = (
    "locality",
    "city",
    "district",
    "state",
    "pincode",
    "google_maps_url",
)
CONFIGURATION_FIELDS = (
    "property_type",
    "type_name",
    "description",
    "bhk",
    "bedrooms",
    "bathrooms",
    "balconies",
    "built_up_area_sq_ft",
    "carpet_area_sq_ft",
    "super_built_up_area_sq_ft",
    "plot_area_sq_yd",
    "plot_area_sq_ft",
    "road_width_ft",
    "floor",
    "office_area_sq_ft",
    "retail_area_sq_ft",
    "frontage_ft",
    "suitable_for",
    "facing",
    "parking",
    "parking_count",
    "basic_price",
    "price_per_sqft",
    "price_per_sqyd",
    "maintenance_charges",
    "availability",
    "possession",
    "amenities",
    "features",
    "notes",
)
CONFIGURATION_IDENTITY_FIELDS = {
    "property_type",
    "type_name",
    "bhk",
    "bedrooms",
    "built_up_area_sq_ft",
    "super_built_up_area_sq_ft",
    "carpet_area_sq_ft",
    "plot_area_sq_yd",
    "plot_area_sq_ft",
    "office_area_sq_ft",
    "retail_area_sq_ft",
}


def normalize_name(value):
    """Match catalog names after trimming outer whitespace, case-insensitively."""
    return str(value or "").strip().casefold()


def _validate_model_fields(model, values, path):
    instance = model()
    for field_name, value in values.items():
        try:
            model._meta.get_field(field_name).clean(value, instance)
        except ValidationError as exc:
            detail = "; ".join(str(message) for message in exc.messages)
            raise PropertyCatalogImportError(
                f"{path} has invalid {field_name}: {detail}"
            ) from exc


def validate_catalog_data(data):
    if not isinstance(data, dict):
        raise PropertyCatalogImportError("JSON root must be an object.")
    developers = data.get("developers")
    if not isinstance(developers, list):
        raise PropertyCatalogImportError("'developers' must be a list.")
    if not developers:
        raise PropertyCatalogImportError("At least one developer is required.")

    for developer_index, developer in enumerate(developers, start=1):
        if not isinstance(developer, dict):
            raise PropertyCatalogImportError(
                f"Developer {developer_index} must be an object."
            )
        if not normalize_name(developer.get("name")):
            raise PropertyCatalogImportError(
                f"Developer {developer_index} must have a name."
            )
        _validate_model_fields(
            CatalogDeveloper,
            _developer_create_values(developer),
            f"Developer '{developer['name']}'",
        )
        projects = developer.get("projects", [])
        if not isinstance(projects, list):
            raise PropertyCatalogImportError(
                f"Projects for '{developer['name']}' must be a list."
            )

        for project_index, project in enumerate(projects, start=1):
            if not isinstance(project, dict):
                raise PropertyCatalogImportError(
                    f"Project {project_index} under '{developer['name']}' must be an object."
                )
            if not normalize_name(project.get("name")):
                raise PropertyCatalogImportError(
                    f"Project {project_index} under '{developer['name']}' must have a name."
                )
            project_path = f"Project '{project['name']}'"
            _validate_model_fields(
                CatalogProject,
                _project_create_values(project),
                project_path,
            )
            for key in ("project_details", "location"):
                value = project.get(key)
                if value is not None and not isinstance(value, dict):
                    raise PropertyCatalogImportError(
                        f"'{key}' for project '{project['name']}' must be an object."
                    )
            for key in ("highlights", "amenities", "configurations"):
                value = project.get(key, [])
                if not isinstance(value, list):
                    raise PropertyCatalogImportError(
                        f"'{key}' for project '{project['name']}' must be a list."
                    )
                if key in {"highlights", "amenities"} and any(
                    not isinstance(item, str) for item in value
                ):
                    raise PropertyCatalogImportError(
                        f"'{key}' for project '{project['name']}' must contain only text values."
                    )
            if project.get("location"):
                _validate_model_fields(
                    CatalogLocation,
                    {
                        field: project["location"].get(field, "")
                        for field in LOCATION_FIELDS
                    },
                    f"{project_path} location",
                )
            for text in project.get("highlights", []):
                _validate_model_fields(
                    CatalogProjectHighlight,
                    {"text": text},
                    f"{project_path} highlight",
                )
            for name in project.get("amenities", []):
                _validate_model_fields(
                    CatalogProjectAmenity,
                    {"name": name},
                    f"{project_path} amenity",
                )
            for configuration_index, configuration in enumerate(
                project.get("configurations", []),
                start=1,
            ):
                if not isinstance(configuration, dict):
                    raise PropertyCatalogImportError(
                        f"Configuration {configuration_index} under '{project['name']}' must be an object."
                    )
                if not normalize_name(configuration.get("type_name")):
                    raise PropertyCatalogImportError(
                        f"Configuration {configuration_index} under '{project['name']}' must have a type_name."
                    )
                if not normalize_name(configuration.get("property_type")):
                    raise PropertyCatalogImportError(
                        f"Configuration {configuration_index} under '{project['name']}' must have a property_type."
                    )
                _validate_model_fields(
                    CatalogConfiguration,
                    _configuration_create_values(configuration),
                    f"Configuration '{configuration['type_name']}' under '{project['name']}'",
                )


def _decimal_key(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value).strip()


DECIMAL_FIELDS = {
    "starting_price",
    "price_per_sqft",
    "basic_price",
    "price_per_sqyd",
    "maintenance_charges",
    "built_up_area_sq_ft",
    "carpet_area_sq_ft",
    "super_built_up_area_sq_ft",
    "plot_area_sq_yd",
    "plot_area_sq_ft",
    "road_width_ft",
    "office_area_sq_ft",
    "retail_area_sq_ft",
    "frontage_ft",
}
INTEGER_FIELDS = {
    "total_towers",
    "total_floors",
    "total_units",
    "bedrooms",
    "bathrooms",
    "balconies",
    "parking_count",
}


def _canonical(value, field_name=None):
    model_field = (field_name or "").rpartition(".")[-1] or field_name or ""
    if model_field in DECIMAL_FIELDS:
        return _decimal_key(value)
    if model_field in INTEGER_FIELDS and value not in (None, ""):
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Decimal(str(value))
    if isinstance(value, (list, tuple)):
        items = [_canonical(item) for item in value]
        if model_field in {"highlights", "amenities", "features"}:
            return tuple(sorted(items, key=lambda item: str(item).casefold()))
        return tuple(items)
    if isinstance(value, dict):
        return tuple(sorted((key, _canonical(item)) for key, item in value.items()))
    if isinstance(value, str):
        return value.strip()
    return value


def _different_fields(existing, incoming):
    return [
        name
        for name, value in incoming.items()
        if _canonical(existing.get(name), name) != _canonical(value, name)
    ]


def _developer_payload(data):
    return {
        field: data[field]
        for field in DEVELOPER_FIELDS
        if field in data
    }


def _developer_values(developer):
    return {field: getattr(developer, field) for field in DEVELOPER_FIELDS}


def _project_payload(data):
    details = data.get("project_details") or {}
    values = {}
    if "project_type" in data:
        values["project_type"] = data["project_type"]
    for field in PROJECT_DETAIL_FIELDS:
        if field in details:
            values[field] = details[field]
    if "channel_partner_notes" in data:
        values["channel_partner_notes"] = data["channel_partner_notes"]
    location = data.get("location")
    if location is not None:
        for field in LOCATION_FIELDS:
            if field in location:
                values[f"location.{field}"] = location[field]
    for key in ("highlights", "amenities"):
        if key in data:
            values[key] = data[key]
    return values


def _project_values(project):
    values = {
        "project_type": project.project_type,
        "channel_partner_notes": project.channel_partner_notes,
        **{field: getattr(project, field) for field in PROJECT_DETAIL_FIELDS},
    }
    location = getattr(project, "location", None)
    if location:
        values.update(
            {f"location.{field}": getattr(location, field) for field in LOCATION_FIELDS}
        )
    else:
        values.update({f"location.{field}": "" for field in LOCATION_FIELDS})
    values["highlights"] = list(
        project.highlights.order_by("text").values_list("text", flat=True)
    )
    values["amenities"] = list(
        project.amenities.order_by("name").values_list("name", flat=True)
    )
    return values


def _configuration_payload(data):
    return {field: data[field] for field in CONFIGURATION_FIELDS if field in data}


def _configuration_values(configuration):
    return {field: getattr(configuration, field) for field in CONFIGURATION_FIELDS}


def configuration_identity(values):
    """A configuration is identified by type/name, bedroom data, and area signature."""
    name = normalize_name(values.get("type_name"))
    property_type = normalize_name(values.get("property_type"))
    bhk = normalize_name(values.get("bhk"))
    bedrooms = values.get("bedrooms")
    if bedrooms not in (None, ""):
        try:
            bedrooms = int(bedrooms)
        except (TypeError, ValueError):
            pass
    areas = tuple(
        _decimal_key(values.get(field))
        for field in (
            "built_up_area_sq_ft",
            "super_built_up_area_sq_ft",
            "carpet_area_sq_ft",
            "plot_area_sq_yd",
            "plot_area_sq_ft",
            "office_area_sq_ft",
            "retail_area_sq_ft",
        )
    )
    return name, property_type, bhk, bedrooms, areas


def find_developer(catalog, name):
    normalized = normalize_name(name)
    return next(
        (
            developer
            for developer in catalog.developers.all()
            if normalize_name(developer.name) == normalized
        ),
        None,
    )


def find_project(developer, name):
    normalized = normalize_name(name)
    return next(
        (
            project
            for project in developer.projects.all()
            if normalize_name(project.name) == normalized
        ),
        None,
    )


def find_configuration(project, values):
    identity = configuration_identity(values)
    return next(
        (
            configuration
            for configuration in project.configurations.all()
            if configuration_identity(_configuration_values(configuration)) == identity
        ),
        None,
    )


def _configuration_create_values(data):
    values = {field: data.get(field) for field in CONFIGURATION_FIELDS}
    values.update(
        {
            "property_type": data.get("property_type", "OTHER"),
            "type_name": str(data.get("type_name", "")).strip(),
            "description": data.get("description", ""),
            "bhk": data.get("bhk", ""),
            "floor": data.get("floor", ""),
            "suitable_for": data.get("suitable_for", ""),
            "facing": data.get("facing", ""),
            "parking": data.get("parking", ""),
            "availability": data.get("availability", ""),
            "possession": data.get("possession", ""),
            "amenities": data.get("amenities", []),
            "features": data.get("features", []),
            "notes": data.get("notes", ""),
        }
    )
    return values


def _project_create_values(data):
    details = data.get("project_details") or {}
    return {
        "name": str(data.get("name", "")).strip(),
        "project_type": data.get("project_type", "OTHER"),
        "status": details.get("status", ""),
        "total_land_area": details.get("total_land_area", ""),
        "total_towers": details.get("total_towers"),
        "total_floors": details.get("total_floors"),
        "total_units": details.get("total_units"),
        "starting_price": details.get("starting_price"),
        "price_per_sqft": details.get("price_per_sqft"),
        "channel_partner_notes": data.get("channel_partner_notes", ""),
    }


def _developer_create_values(data):
    return {
        "name": str(data.get("name", "")).strip(),
        **{field: data.get(field, "") for field in DEVELOPER_FIELDS},
    }


def configuration_conflicts(configuration, incoming_values):
    existing_values = _configuration_values(configuration)
    compared_values = {
        field: value
        for field, value in incoming_values.items()
        if field not in CONFIGURATION_IDENTITY_FIELDS
    }
    return _different_fields(existing_values, compared_values)


def _set_summary_action(summary, action):
    summary[action] += 1
    if action == "conflicting":
        summary["skipped"] += 1


def _import_data(data, catalog, *, persist):
    validate_catalog_data(data)
    summary = {"created": 0, "reused": 0, "skipped": 0, "conflicting": 0}
    records = []
    if persist and catalog is None:
        catalog = PropertyCatalog.objects.create(
            name=data.get("catalog_name", "Property Catalog"),
            version=data.get("version", "1.0"),
        )

    developers_by_name = {}
    if catalog is not None:
        for existing in catalog.developers.all().prefetch_related(
            "projects__configurations",
            "projects__highlights",
            "projects__amenities",
        ):
            developers_by_name.setdefault(normalize_name(existing.name), {
                "object": existing,
                "source": None,
                "projects": {},
            })

    for developer_data in data["developers"]:
        developer_name = str(developer_data["name"]).strip()
        developer_key = normalize_name(developer_name)
        developer_state = developers_by_name.get(developer_key)
        developer_payload = _developer_payload(developer_data)
        if developer_state is None:
            action = "created"
            developer = None
            source = _developer_create_values(developer_data)
            if persist:
                developer = CatalogDeveloper.objects.create(
                    catalog=catalog,
                    **source,
                )
            developer_state = {
                "object": developer,
                "source": source,
                "projects": {},
            }
            developers_by_name[developer_key] = developer_state
            differences = []
        else:
            developer = developer_state["object"]
            existing_values = (
                _developer_values(developer)
                if developer is not None
                else developer_state["source"]
            )
            differences = _different_fields(existing_values, developer_payload)
            action = "conflicting" if differences else "reused"
        _set_summary_action(summary, action)
        records.append({
            "kind": "Developer",
            "path": f"Developer: {developer_name}",
            "action": action,
            "differences": differences,
        })

        projects_by_name = developer_state["projects"]
        if developer is not None and not projects_by_name:
            for existing_project in developer.projects.all():
                projects_by_name.setdefault(
                    normalize_name(existing_project.name),
                    {"object": existing_project, "source": None, "configurations": {}},
                )

        for project_data in developer_data.get("projects", []):
            project_name = str(project_data["name"]).strip()
            project_key = normalize_name(project_name)
            project_state = projects_by_name.get(project_key)
            project_payload = _project_payload(project_data)
            project_path = f"Developer: {developer_name} / Project: {project_name}"

            if project_state is None:
                action = "created"
                project = None
                project_source = {
                    **_project_create_values(project_data),
                    **_project_payload(project_data),
                }
                if persist:
                    project = CatalogProject.objects.create(
                        developer=developer,
                        **_project_create_values(project_data),
                    )
                    _create_project_children(project, project_data)
                project_state = {
                    "object": project,
                    "source": project_source,
                    "configurations": {},
                }
                projects_by_name[project_key] = project_state
                differences = []
            else:
                project = project_state["object"]
                existing_values = (
                    _project_values(project)
                    if project is not None
                    else project_state["source"]
                )
                differences = _different_fields(existing_values, project_payload)
                action = "conflicting" if differences else "reused"
            _set_summary_action(summary, action)
            records.append({
                "kind": "Project",
                "path": project_path,
                "action": action,
                "differences": differences,
            })

            configurations_by_identity = project_state["configurations"]
            if project is not None and not configurations_by_identity:
                for existing_configuration in project.configurations.all():
                    identity = configuration_identity(
                        _configuration_values(existing_configuration)
                    )
                    configurations_by_identity.setdefault(
                        identity,
                        {"object": existing_configuration, "source": None},
                    )

            for configuration_data in project_data.get("configurations", []):
                config_values = _configuration_create_values(configuration_data)
                identity = configuration_identity(config_values)
                config_path = (
                    f"{project_path} / Configuration: {config_values['type_name']}"
                )
                configuration_state = configurations_by_identity.get(identity)
                config_payload = _configuration_payload(configuration_data)
                if configuration_state is None:
                    action = "created"
                    configuration = None
                    if persist:
                        configuration = CatalogConfiguration.objects.create(
                            project=project,
                            **config_values,
                        )
                    configurations_by_identity[identity] = {
                        "object": configuration,
                        "source": config_values,
                    }
                    differences = []
                else:
                    configuration = configuration_state["object"]
                    existing_values = (
                        _configuration_values(configuration)
                        if configuration is not None
                        else configuration_state["source"]
                    )
                    compared = {
                        key: value
                        for key, value in config_payload.items()
                        if key not in CONFIGURATION_IDENTITY_FIELDS
                    }
                    differences = _different_fields(existing_values, compared)
                    action = "conflicting" if differences else "reused"
                _set_summary_action(summary, action)
                records.append({
                    "kind": "Configuration",
                    "path": config_path,
                    "action": action,
                    "differences": differences,
                })

    return catalog, summary, records


def _create_project_children(project, project_data):
    location = project_data.get("location")
    if location:
        CatalogLocation.objects.create(
            project=project,
            **{field: location.get(field, "") for field in LOCATION_FIELDS},
        )
    CatalogProjectHighlight.objects.bulk_create(
        [
            CatalogProjectHighlight(project=project, text=item)
            for item in project_data.get("highlights", [])
            if isinstance(item, str)
        ]
    )
    CatalogProjectAmenity.objects.bulk_create(
        [
            CatalogProjectAmenity(project=project, name=item)
            for item in project_data.get("amenities", [])
            if isinstance(item, str)
        ]
    )


def preview_catalog_import(data, catalog=None):
    _, summary, records = _import_data(data, catalog, persist=False)
    return summary, records


@transaction.atomic
def import_catalog(data, catalog=None):
    if catalog is not None:
        catalog = PropertyCatalog.objects.select_for_update().get(pk=catalog.pk)
    imported_catalog, summary, records = _import_data(
        data,
        catalog,
        persist=True,
    )
    return imported_catalog, summary, records
