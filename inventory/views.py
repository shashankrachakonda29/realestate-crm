import os
import tempfile
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from developers.models import Developer
from locations.models import Location
from projects.models import Project
from .models import Inventory
from .services.gemini_extractor import GeminiModelUnavailable, GeminiTemporaryUnavailable, extract_property_from_files
from .services.import_mapper import (
    PREVIEW_FIELDS,
    configuration_to_inventory,
    decimal_value as mapped_decimal_value,
    integer_value,
    inventory_configuration_matches,
    json_field_report,
    mapping_warnings,
    non_empty_inventory_values,
    validate_preview_configurations,
)


def decimal_value(value):
    if not value:
        return Decimal("0")
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def inventory_list(request):
    search = request.GET.get("search", "").strip()
    project_id = request.GET.get("project", "").strip()
    location_id = request.GET.get("location", "").strip()
    property_type = request.GET.get("property_type", "").strip()
    status = request.GET.get("status", "").strip()
    bhk = request.GET.get("bhk", "").strip()
    inventory = Inventory.objects.select_related("project", "project__developer", "project__location").order_by("project__name")
    if search:
        inventory = inventory.filter(project__name__icontains=search)
    if project_id:
        inventory = inventory.filter(project_id=project_id)
    if location_id:
        inventory = inventory.filter(project__location_id=location_id)
    if property_type:
        inventory = inventory.filter(property_type=property_type)
    if status:
        inventory = inventory.filter(status=status)
    if bhk:
        inventory = inventory.filter(bhk=bhk)
    page_obj = Paginator(inventory, 50).get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    projects = Project.objects.filter(is_active=True).order_by("name")
    locations = Project.objects.filter(is_active=True).select_related("location").values("location_id", "location__name").distinct().order_by("location__name")
    return render(request, "inventory/list.html", {
        "inventory": page_obj, "page_obj": page_obj, "query_string": query_params.urlencode(),
        "search": search, "projects": projects, "locations": locations,
        "property_types": Inventory.PropertyType.choices, "statuses": Inventory.Status.choices,
        "selected_project": project_id, "selected_location": location_id,
        "selected_property_type": property_type, "selected_status": status, "selected_bhk": bhk,
    })


def inventory_create(request):
    projects = Project.objects.filter(is_active=True).select_related("developer", "location").order_by("name")
    if request.method == "POST":
        basic_sale_price = decimal_value(request.POST.get("basic_sale_price"))
        extra_area = decimal_value(request.POST.get("extra_built_up_area_sq_ft"))
        extra_rate = decimal_value(request.POST.get("extra_built_up_rate_per_sq_ft"))
        gst = decimal_value(request.POST.get("gst_amount"))
        amenities = decimal_value(request.POST.get("amenities_charges"))
        facing = decimal_value(request.POST.get("facing_charges"))
        discount = decimal_value(request.POST.get("discount"))
        unit_size = decimal_value(request.POST.get("unit_size_sq_ft"))
        basic_sale_price_2 = extra_area * extra_rate
        total = basic_sale_price + basic_sale_price_2 + gst + amenities + facing - discount
        price_per_sq_ft = total / unit_size if unit_size > 0 else Decimal("0")
        values = {field.name: request.POST.get(field.name) or None for field in Inventory._meta.fields if field.name not in {"id", "project", "created_at", "updated_at"}}
        values.update(project_id=request.POST.get("project"), basic_sale_price=basic_sale_price, extra_built_up_rate_per_sq_ft=extra_rate, basic_sale_price_2=basic_sale_price_2, gst_amount=gst, amenities_charges=amenities, facing_charges=facing, discount=discount, total_unit_cost=total, price_per_sq_ft_incl_gst=price_per_sq_ft)
        Inventory.objects.create(**values)
        return redirect("inventory_list")
    return render(request, "inventory/form.html", {"title": "Add Inventory", "inventory_item": None, "projects": projects, "property_types": Inventory.PropertyType.choices, "statuses": Inventory.Status.choices})


def inventory_detail(request, pk):
    item = get_object_or_404(Inventory.objects.select_related("project", "project__developer", "project__location"), pk=pk)
    return render(request, "inventory/detail.html", {"inventory_item": item})


def inventory_edit(request, pk):
    item = get_object_or_404(Inventory, pk=pk)
    projects = Project.objects.filter(is_active=True).select_related("developer", "location").order_by("name")
    if request.method == "POST":
        for field in Inventory._meta.fields:
            if field.name not in {"id", "project", "created_at", "updated_at"} and field.name in request.POST:
                setattr(item, field.name, request.POST.get(field.name) or None)
        item.project_id = request.POST.get("project")
        item.save()
        return redirect("inventory_detail", pk=item.pk)
    return render(request, "inventory/form.html", {"title": "Edit Inventory", "inventory_item": item, "projects": projects, "property_types": Inventory.PropertyType.choices, "statuses": Inventory.Status.choices})


def inventory_delete(request, pk):
    item = get_object_or_404(Inventory, pk=pk)
    if request.method == "POST":
        item.delete()
        return redirect("inventory_list")
    return render(request, "inventory/detail.html", {"inventory_item": item, "confirm_delete": True})


def import_project_name(data):
    return str(data.get("project_name") or "").strip()


def normalized_import_name(value):
    return " ".join(str(value or "").strip().split()).casefold()


def find_import_project(data):
    name = import_project_name(data)
    if not name:
        return None
    normalized = normalized_import_name(name)
    return next(
        (
            project
            for project in Project.objects.select_related("developer", "location")
            if normalized_import_name(project.name) == normalized
        ),
        None,
    )


def import_project_type(value):
    normalized = str(value or "").strip().upper().replace("-", " ")
    return {
        "VILLA": Project.ProjectType.VILLAS,
        "VILLAS": Project.ProjectType.VILLAS,
        "APARTMENT": Project.ProjectType.APARTMENTS,
        "APARTMENTS": Project.ProjectType.APARTMENTS,
        "PLOT": Project.ProjectType.PLOTS,
        "PLOTS": Project.ProjectType.PLOTS,
        "FARM": Project.ProjectType.FARM_LANDS,
        "FARM LAND": Project.ProjectType.FARM_LANDS,
        "FARM LANDS": Project.ProjectType.FARM_LANDS,
        "COMMERCIAL": Project.ProjectType.COMMERCIAL,
        "OTHER": Project.ProjectType.OTHER,
    }.get(normalized, "")


def import_project_values(data):
    information = data.get("project_information") or {}
    pricing = data.get("pricing_information") or {}
    configurations = data.get("unit_configurations") or []
    first_configuration = configurations[0] if configurations else {}
    amenities = data.get("amenities", pricing.get("amenities", ""))
    if isinstance(amenities, list):
        amenities = ", ".join(str(item).strip() for item in amenities)
    return {
        "name": import_project_name(data),
        "project_type": import_project_type(data.get("property_type") or first_configuration.get("unit_type")),
        "description": str(data.get("description") or information.get("description") or "").strip(),
        "total_land_acres": mapped_decimal_value(information.get("project_area")),
        "total_units": integer_value(information.get("total_villas") or information.get("total_units")),
        "bhk": str(information.get("bhk_types") or "").strip(),
        "rera_number": str(data.get("rera_number") or "").strip(),
        "amenities": str(amenities or "").strip(),
        "website": str(data.get("website") or "").strip(),
        "google_maps_url": str(data.get("google_maps_url") or "").strip(),
        "is_active": True,
    }


def find_import_developer(data):
    developer = data.get("developer")
    name = str(developer.get("name") if isinstance(developer, dict) else developer or "").strip()
    normalized = normalized_import_name(name)
    return next(
        (
            developer
            for developer in Developer.objects.filter(is_active=True)
            if normalized_import_name(developer.name) == normalized
        ),
        None,
    ) if name else None


def find_import_location(data):
    location = data.get("location")
    value = str(location.get("name") if isinstance(location, dict) else location or "").strip()
    if not value:
        return None
    short_name = value.split(",", 1)[0].strip()
    active_locations = list(Location.objects.filter(is_active=True))
    exact_matches = [
        location for location in active_locations
        if normalized_import_name(location.name) == normalized_import_name(value)
    ]
    if exact_matches:
        return exact_matches[0]
    short_matches = [
        location for location in active_locations
        if normalized_import_name(location.name) == normalized_import_name(short_name)
    ]
    return short_matches[0] if len(short_matches) == 1 else None


def import_relationship_name(value):
    if isinstance(value, dict):
        return str(value.get("name") or "").strip()
    return str(value or "").strip()


def resolve_import_developer(data):
    developer_value = data.get("developer")
    developer_name = import_relationship_name(developer_value)
    if not developer_name:
        return None
    developer = find_import_developer(data)
    developer_data = developer_value if isinstance(developer_value, dict) else {}
    if developer is None:
        inactive_match = next(
            (
                item for item in Developer.objects.all()
                if normalized_import_name(item.name) == normalized_import_name(developer_name)
            ),
            None,
        )
        developer = inactive_match or Developer(name=developer_name)
    developer.name = developer.name or developer_name
    for field in ("description", "website", "contact_person", "phone", "email", "address"):
        value = str(developer_data.get(field) or "").strip()
        if value:
            setattr(developer, field, value)
    developer.is_active = True
    developer.save()
    return developer


def resolve_import_location(data):
    location_value = data.get("location")
    location_name = import_relationship_name(location_value)
    if not location_name:
        return None
    location = find_import_location(data)
    location_data = location_value if isinstance(location_value, dict) else {}
    if location is None:
        location = Location(name=location_name)
    elif not location.name:
        location.name = location_name
    for field in ("city", "state", "pincode", "google_maps_url", "description"):
        value = str(location_data.get(field) or "").strip()
        if value:
            setattr(location, field, value)
    location.is_active = True
    location.save()
    return location


def import_relationship_status(data, project, finder):
    if project:
        return "Existing"
    value = data.get("developer" if finder is find_import_developer else "location")
    name = import_relationship_name(value)
    if not name:
        return "Missing"
    return "Existing" if finder(data) else "New"


def import_project_validation_errors(data):
    if find_import_project(data):
        return []
    errors = []
    if not import_project_name(data):
        errors.append("The JSON project_name is required.")
    if not import_relationship_name(data.get("developer")):
        errors.append("Developer is required for a new project.")
    if not import_relationship_name(data.get("location")):
        errors.append("Location is required for a new project.")
    return errors


def import_configuration_rows(data, filename, project):
    existing_items = list(Inventory.objects.filter(project=project)) if project else []
    rows = []
    for index, configuration in enumerate(data.get("unit_configurations", [])):
        mapped = configuration_to_inventory(configuration, data, filename)
        existing = next(
            (item for item in existing_items if inventory_configuration_matches(item, mapped)),
            None,
        )
        status = "UPDATE" if existing else "NEW"
        rows.append({
            "index": index,
            "fields": [
                (field.replace("_", " ").title(), field, configuration.get(field, ""))
                for field in PREVIEW_FIELDS
            ],
            "status": status,
        })
    return rows


def save_import(data, configurations, filename):
    with transaction.atomic():
        developer = resolve_import_developer(data)
        location = resolve_import_location(data)
        project = find_import_project(data)
        if project is None:
            project_values = import_project_values(data)
            project = Project.objects.create(
                developer=developer,
                location=location,
                **project_values,
            )
        else:
            project_values = import_project_values(data)
            if developer is not None:
                project.developer = developer
            if location is not None:
                project.location = location
            for field, value in project_values.items():
                if value not in (None, "") and field not in {"name", "is_active"}:
                    setattr(project, field, value)
            project.is_active = True
            project.save()
        existing_items = list(Inventory.objects.filter(project=project))
        created_count = 0
        updated_count = 0
        for configuration in configurations:
            mapped = configuration_to_inventory(configuration, data, filename)
            existing = next(
                (item for item in existing_items if inventory_configuration_matches(item, mapped)),
                None,
            )
            if existing:
                update_values = non_empty_inventory_values(
                    {key: value for key, value in mapped.items() if key != "source"}
                )
                for field, value in update_values.items():
                    setattr(existing, field, value)
                existing.save()
                updated_count += 1
                continue
            created = Inventory.objects.create(project=project, **mapped)
            existing_items.append(created)
            created_count += 1
    return created_count, updated_count


def inventory_import(request):
    def preview_context(data, filename, errors=None, json_import=False):
        configurations = data.get("unit_configurations", [])
        project = find_import_project(data)
        resolved_developer = project.developer if project else find_import_developer(data)
        resolved_location = project.location if project else find_import_location(data)
        return {
            "data": data,
            "filename": filename,
            "rera_number": data.get("rera_number", ""),
            "amenities": ", ".join(str(item) for item in data.get("amenities", [])) if isinstance(data.get("amenities"), list) else data.get("amenities", ""),
            "preview_fields": PREVIEW_FIELDS,
            "configuration_rows": import_configuration_rows(data, filename, project),
            "errors": errors or [],
            "project": project,
            "resolved_project": project,
            "resolved_developer": resolved_developer,
            "resolved_location": resolved_location,
            "project_data": import_project_values(data),
            "project_status": "EXISTING PROJECT" if project else "NEW PROJECT",
            "developer_status": import_relationship_status(data, project, find_import_developer),
            "location_status": import_relationship_status(data, project, find_import_location),
            "source_documents": [item.strip() for item in filename.split(",") if item.strip()],
            "mapping_warnings": mapping_warnings(configurations),
            "json_import": json_import,
            "field_report": json_field_report(data) if json_import else None,
        }
    if request.method == "GET":
        return render(request, "inventory/import.html")
    if request.POST.get("cancel_import") == "1":
        request.session.pop("inventory_extracted_data", None)
        request.session.pop("inventory_import_filename", None)
        return redirect("inventory_list")
    if request.POST.get("confirm_import") == "1":
        data = request.session.get("inventory_extracted_data")
        json_import = request.session.get("inventory_json_import", False)
        filename = request.session.get("inventory_import_filename", "import")
        if not isinstance(data, dict):
            messages.error(request, "No extracted property data found.")
            return redirect("inventory_import")
        raw = data.get("unit_configurations", [])
        configurations = [{field: request.POST.get(f"config_{index}_{field}", "") for field in PREVIEW_FIELDS} for index in range(len(raw))]
        data = {**data, "rera_number": request.POST.get("rera_number", "").strip(), "amenities": request.POST.get("amenities", "").strip()}
        errors = validate_preview_configurations(configurations, data)
        if json_import:
            errors.extend(json_field_report({"unit_configurations": configurations})["invalid_fields"])
        if not configurations: errors.append("Gemini did not return any property configurations.")
        if errors:
            return render(request, "inventory/import_preview.html", preview_context({**data, "unit_configurations": configurations}, filename, errors, json_import))
        project = find_import_project(data)
        if project is None:
            project_values = import_project_values(data)
            if not project_values["name"]:
                errors.append("The JSON project_name is required.")
            if not project_values["project_type"]:
                errors.append("The JSON property_type does not map to a Project type.")
            if not import_relationship_name(data.get("developer")):
                errors.append("Developer is required for a new project.")
            if not import_relationship_name(data.get("location")):
                errors.append("Location is required for a new project.")
            if errors:
                return render(request, "inventory/import_preview.html", preview_context({**data, "unit_configurations": configurations}, filename, errors, json_import))
        try:
            created_count, updated_count = save_import(data, configurations, filename)
        except Exception as exc:
            errors.append(f"Import could not be saved: {exc}")
            return render(
                request,
                "inventory/import_preview.html",
                preview_context({**data, "unit_configurations": configurations}, filename, errors, json_import),
            )
        request.session.pop("inventory_extracted_data", None)
        request.session.pop("inventory_import_filename", None)
        request.session.pop("inventory_json_import", None)
        messages.success(
            request,
            f"Created {created_count} and updated {updated_count} inventory record(s).",
        )
        return redirect("inventory_list")
    max_size = getattr(settings, "INVENTORY_IMPORT_MAX_BYTES", 50 * 1024 * 1024)
    json_file = request.FILES.get("json_file")
    if json_file is not None:
        if not json_file.name.lower().endswith(".json"):
            return render(request, "inventory/import.html", {"error": "Please upload a .json file."})
        if json_file.size > max_size:
            return render(request, "inventory/import.html", {"error": "The JSON file is larger than 50 MB."})
        try:
            import json
            data = json.loads(json_file.read().decode("utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError("JSON must be an object.")
            configurations = data.get("unit_configurations")
            if not isinstance(configurations, list) or not all(isinstance(item, dict) for item in configurations):
                raise ValueError("unit_configurations must be a list of objects.")
            report = json_field_report(data)
            filename = json_file.name
            request.session["inventory_extracted_data"] = data
            request.session["inventory_import_filename"] = filename
            request.session["inventory_json_import"] = True
            preview_errors = report["invalid_fields"] + import_project_validation_errors(data)
            return render(request, "inventory/import_preview.html", preview_context(data, filename, preview_errors, True))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return render(request, "inventory/import.html", {"error": f"Invalid JSON file: {exc}"})
        except ValueError as exc:
            return render(request, "inventory/import.html", {"error": str(exc)})

    uploaded_files = request.FILES.getlist("property_files")
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png"}
    if not uploaded_files:
        return render(request, "inventory/import.html", {"error": "Please choose at least one file."})
    for uploaded_file in uploaded_files:
        extension = os.path.splitext(uploaded_file.name)[1].lower()
        if extension not in allowed_extensions:
            return render(request, "inventory/import.html", {"error": f"Unsupported file: {uploaded_file.name}"})
        if uploaded_file.size > max_size:
            return render(request, "inventory/import.html", {"error": f"{uploaded_file.name} is larger than 50 MB."})
    paths = []
    try:
        directory = os.path.join(settings.MEDIA_ROOT, "inventory_imports")
        os.makedirs(directory, exist_ok=True)
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, dir=directory, prefix="property_", suffix=os.path.splitext(uploaded_file.name)[1].lower()) as temporary_file:
                for chunk in uploaded_file.chunks(): temporary_file.write(chunk)
                paths.append(temporary_file.name)
        data = extract_property_from_files(paths)
    except (GeminiModelUnavailable, GeminiTemporaryUnavailable) as exc:
        return render(request, "inventory/import.html", {"error": str(exc)})
    except Exception as exc:
        return render(request, "inventory/import.html", {"error": f"Extraction failed: {exc}"})
    finally:
        for path in paths:
            if os.path.exists(path): os.unlink(path)
    configurations = data.get("unit_configurations") if isinstance(data, dict) else None
    if not isinstance(configurations, list) or len(configurations) > 100 or not all(isinstance(item, dict) for item in configurations):
        return render(request, "inventory/import.html", {"error": "Gemini returned an invalid configuration list."})
    filename = ", ".join(item.name for item in uploaded_files)
    request.session["inventory_extracted_data"] = data
    request.session["inventory_import_filename"] = filename
    request.session["inventory_json_import"] = False
    return render(request, "inventory/import_preview.html", preview_context(data, filename, import_project_validation_errors(data)))
