import re
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import DatabaseError, transaction
from django.db.models import Prefetch
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.utils.html import format_html

from .forms import (
    CatalogConfigurationForm,
    CatalogDeveloperForm,
    CatalogProjectForm,
    CatalogSearchForm,
    PropertyCatalogImportForm,
)
from .models import (
    CatalogDeveloper,
    CatalogProject,
    PropertyCatalog,
)
from .services import (
    PropertyCatalogImportError,
    CONFIGURATION_FIELDS,
    configuration_conflicts,
    find_configuration,
    find_developer,
    find_project,
    import_catalog,
    preview_catalog_import,
)


@login_required
def dashboard(request):

    catalogs = PropertyCatalog.objects.order_by(
        "-created_at"
    )

    return render(
        request,
        "property_catalog/dashboard.html",
        {
            "catalogs": catalogs,
        },
    )


@login_required
def import_json(request):

    if request.method == "POST":

        form = PropertyCatalogImportForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            uploaded_file = form.cleaned_data["json_file"]
            try:
                data = form.parse_json(uploaded_file)
                request.session["property_catalog_preview"] = data
                request.session["property_catalog_preview_target"] = (
                    form.cleaned_data["target_catalog"].pk
                    if form.cleaned_data["target_catalog"]
                    else None
                )
                return redirect("property_catalog:preview")
            except PropertyCatalogImportError as exc:
                form.add_error("json_file", str(exc))

    else:
        form = PropertyCatalogImportForm()
        requested_catalog = request.GET.get("catalog")
        if requested_catalog:
            form.fields["target_catalog"].initial = (
                PropertyCatalog.objects.filter(pk=requested_catalog)
                .values_list("pk", flat=True)
                .first()
            )

    return render(
        request,
        "property_catalog/import_json.html",
        {
            "form": form,
        },
    )


@login_required
def preview(request):

    data = request.session.get(
        "property_catalog_preview"
    )

    if not data:

        return redirect(
            "property_catalog:import_json"
        )

    target_id = request.session.get("property_catalog_preview_target")
    target_catalog = (
        PropertyCatalog.objects.filter(pk=target_id).first()
        if target_id
        else None
    )
    if target_id and target_catalog is None:
        return render(
            request,
            "property_catalog/preview.html",
            {
                "data": data,
                "import_error": "The selected destination catalog no longer exists. Upload the JSON again.",
            },
        )

    developers = data.get(
        "developers",
        [],
    )

    project_count = 0
    configuration_count = 0

    for developer in developers:

        projects = developer.get(
            "projects",
            [],
        )

        project_count += len(projects)

        for project in projects:

            configurations = project.get(
                "configurations",
                [],
            )

            configuration_count += len(
                configurations
            )

    try:
        preview_summary, preview_records = preview_catalog_import(
            data,
            target_catalog,
        )
    except PropertyCatalogImportError as exc:
        return render(
            request,
            "property_catalog/preview.html",
            {
                "data": data,
                "developers": developers,
                "developer_count": len(developers),
                "project_count": project_count,
                "configuration_count": configuration_count,
                "import_error": str(exc),
            },
        )

    if request.method == "POST":

        action = request.POST.get(
            "action"
        )

        if action == "confirm":

            try:
                catalog, import_summary, _records = import_catalog(
                    data,
                    target_catalog,
                )
                request.session.pop("property_catalog_preview", None)
                request.session.pop("property_catalog_preview_target", None)
                messages.success(
                    request,
                    "Import complete: "
                    f"{import_summary['created']} created, "
                    f"{import_summary['reused']} reused, "
                    f"{import_summary['skipped']} skipped, "
                    f"{import_summary['conflicting']} conflicts.",
                )
                return redirect(
                    "property_catalog:catalog_detail",
                    pk=catalog.pk,
                )
            except (PropertyCatalogImportError, DatabaseError) as exc:

                return render(
                    request,
                    "property_catalog/preview.html",
                    {
                        "data": data,
                        "developers": developers,
                        "developer_count": len(
                            developers
                        ),
                        "project_count": project_count,
                        "configuration_count": configuration_count,
                        "preview_summary": preview_summary,
                        "preview_records": preview_records,
                        "target_catalog": target_catalog,
                        "import_error": str(exc),
                    },
                )

        if action == "cancel":

            request.session.pop(
                "property_catalog_preview",
                None,
            )
            request.session.pop("property_catalog_preview_target", None)

            return redirect(
                "property_catalog:import_json"
            )

    return render(
        request,
        "property_catalog/preview.html",
        {
            "data": data,
            "developers": developers,
            "developer_count": len(
                developers
            ),
            "project_count": project_count,
            "configuration_count": configuration_count,
            "preview_summary": preview_summary,
            "preview_records": preview_records,
            "target_catalog": target_catalog,
        },
    )


@login_required
def catalog_developer_detail(request, catalog_pk, developer_pk):
    catalog = get_object_or_404(PropertyCatalog, pk=catalog_pk)
    developer = get_object_or_404(
        CatalogDeveloper.objects.prefetch_related(
            "projects__configurations",
        ),
        pk=developer_pk,
        catalog=catalog,
    )
    return render(
        request,
        "property_catalog/developer_detail.html",
        {"catalog": catalog, "developer": developer},
    )


@login_required
def catalog_developer_create(request, catalog_pk):
    catalog = get_object_or_404(PropertyCatalog, pk=catalog_pk)
    form = CatalogDeveloperForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            locked_catalog = PropertyCatalog.objects.select_for_update().get(
                pk=catalog.pk
            )
            existing = find_developer(locked_catalog, form.cleaned_data["name"])
            if existing:
                differences = [
                    field
                    for field in (
                        "developer_type",
                        "contact_person",
                        "phone",
                        "email",
                        "website",
                    )
                    if form.cleaned_data[field] != getattr(existing, field)
                ]
                message = format_html(
                    'A developer with this name already exists: <a href="{}">{}</a>.',
                    reverse(
                        "property_catalog:catalog_developer_detail",
                        kwargs={
                            "catalog_pk": catalog.pk,
                            "developer_pk": existing.pk,
                        },
                    ),
                    existing.name,
                )
                if differences:
                    message += format_html(
                        " Details differ in: {}.",
                        ", ".join(differences),
                    )
                messages.warning(request, message)
                return redirect(
                    "property_catalog:catalog_developer_detail",
                    catalog_pk=catalog.pk,
                    developer_pk=existing.pk,
                )
            developer = form.save(commit=False)
            developer.catalog = locked_catalog
            developer.save()
        messages.success(request, "Developer created.")
        return redirect(
            "property_catalog:catalog_developer_detail",
            catalog_pk=catalog.pk,
            developer_pk=developer.pk,
        )
    return render(
        request,
        "property_catalog/catalog_record_form.html",
        {
            "catalog": catalog,
            "form": form,
            "title": "Add Developer",
            "cancel_url": reverse(
                "property_catalog:catalog_detail",
                kwargs={"pk": catalog.pk},
            ),
        },
    )


@login_required
def catalog_project_create(request, catalog_pk, developer_pk):
    catalog = get_object_or_404(PropertyCatalog, pk=catalog_pk)
    developer = get_object_or_404(
        CatalogDeveloper,
        pk=developer_pk,
        catalog=catalog,
    )
    form = CatalogProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            PropertyCatalog.objects.select_for_update().get(pk=catalog.pk)
            locked_developer = get_object_or_404(
                CatalogDeveloper,
                pk=developer.pk,
                catalog_id=catalog.pk,
            )
            existing = find_project(locked_developer, form.cleaned_data["name"])
            if existing:
                differences = [
                    field
                    for field in (
                        "project_type",
                        "status",
                        "total_land_area",
                        "total_towers",
                        "total_floors",
                        "total_units",
                        "starting_price",
                        "price_per_sqft",
                        "channel_partner_notes",
                    )
                    if form.cleaned_data[field] != getattr(existing, field)
                ]
                message = format_html(
                    'A project with this name already exists: <a href="{}">{}</a>.',
                    reverse(
                        "property_catalog:catalog_project_detail",
                        kwargs={
                            "catalog_pk": catalog.pk,
                            "project_pk": existing.pk,
                        },
                    ),
                    existing.name,
                )
                if differences:
                    message += format_html(
                        " Existing data was kept; differences: {}.",
                        ", ".join(differences),
                    )
                messages.warning(request, message)
                return redirect(
                    "property_catalog:catalog_project_detail",
                    catalog_pk=catalog.pk,
                    project_pk=existing.pk,
                )
            project = form.save(commit=False)
            project.developer = locked_developer
            project.save()
        messages.success(request, "Project created.")
        return redirect(
            "property_catalog:catalog_project_detail",
            catalog_pk=catalog.pk,
            project_pk=project.pk,
        )
    return render(
        request,
        "property_catalog/catalog_record_form.html",
        {
            "catalog": catalog,
            "developer": developer,
            "form": form,
            "title": "Add Project",
            "cancel_url": reverse(
                "property_catalog:catalog_developer_detail",
                kwargs={"catalog_pk": catalog.pk, "developer_pk": developer.pk},
            ),
        },
    )


@login_required
def catalog_project_detail(request, catalog_pk, project_pk):
    catalog = get_object_or_404(PropertyCatalog, pk=catalog_pk)
    project = get_object_or_404(
        CatalogProject.objects.select_related(
            "developer",
            "location",
        ).prefetch_related("configurations"),
        pk=project_pk,
        developer__catalog=catalog,
    )
    return render(
        request,
        "property_catalog/project_detail.html",
        {"catalog": catalog, "project": project},
    )


@login_required
def catalog_configuration_create(request, catalog_pk, project_pk):
    catalog = get_object_or_404(PropertyCatalog, pk=catalog_pk)
    project = get_object_or_404(
        CatalogProject.objects.select_related("developer"),
        pk=project_pk,
        developer__catalog=catalog,
    )
    form = CatalogConfigurationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            PropertyCatalog.objects.select_for_update().get(pk=catalog.pk)
            locked_project = get_object_or_404(
                CatalogProject.objects.select_for_update(),
                pk=project.pk,
                developer__catalog_id=catalog.pk,
            )
            candidate = form.save(commit=False)
            candidate.project = locked_project
            existing = find_configuration(
                locked_project,
                {
                    field: getattr(candidate, field)
                    for field in (
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
                    )
                },
            )
            if existing:
                differences = configuration_conflicts(
                    existing,
                    {
                        field: getattr(candidate, field)
                        for field in CONFIGURATION_FIELDS
                    },
                )
                conflict_text = (
                    " Existing details differ in: "
                    + ", ".join(differences)
                    + "."
                    if differences
                    else ""
                )
                messages.warning(
                    request,
                    format_html(
                        'An equivalent configuration already exists. '
                        '<a href="{}">Review the existing configuration</a> before making changes.{}',
                        reverse(
                            "property_catalog:catalog_project_detail",
                            kwargs={
                                "catalog_pk": catalog.pk,
                                "project_pk": locked_project.pk,
                            },
                        )
                        + f"#configuration-{existing.pk}",
                        conflict_text,
                    ),
                )
                return redirect(
                    reverse(
                        "property_catalog:catalog_project_detail",
                        kwargs={
                            "catalog_pk": catalog.pk,
                            "project_pk": locked_project.pk,
                        },
                    )
                    + f"#configuration-{existing.pk}"
                )
            candidate.save()
        messages.success(request, "Configuration created.")
        return redirect(
            reverse(
                "property_catalog:catalog_project_detail",
                kwargs={"catalog_pk": catalog.pk, "project_pk": project.pk},
            )
            + f"#configuration-{candidate.pk}"
        )
    return render(
        request,
        "property_catalog/catalog_record_form.html",
        {
            "catalog": catalog,
            "project": project,
            "form": form,
            "title": "Add Configuration",
            "cancel_url": reverse(
                "property_catalog:catalog_project_detail",
                kwargs={"catalog_pk": catalog.pk, "project_pk": project.pk},
            ),
        },
    )


@login_required
def catalog_detail(request, pk):
    catalog = get_object_or_404(
        PropertyCatalog,
        pk=pk,
    )

    search_form = CatalogSearchForm(
        request.GET if request.GET else None,
        catalog=catalog,
    )
    filters = {}
    if search_form.is_bound and search_form.is_valid():
        filters = search_form.cleaned_data

    project_queryset = (
        CatalogProject.objects.select_related("location")
        .prefetch_related("configurations", "highlights", "amenities")
        .order_by("name", "pk")
    )
    developers = list(
        catalog.developers.prefetch_related(
            Prefetch("projects", queryset=project_queryset),
        )
    )

    total_projects = 0
    total_configurations = 0
    project_type_counts = {}
    filtered_developers = []

    for developer in developers:
        matching_projects = []
        for project in developer.projects.all():
            if not _matches_project_filters(project, developer, filters):
                continue

            project_configurations = list(project.configurations.all())
            matching_project_text = _matches_keyword(project, developer, filters.get("keyword", ""))
            matching_project_notes = _matches_project_notes(
                project,
                filters.get("notes", ""),
            )
            matching_configurations = []
            for configuration in project_configurations:
                _decorate_configuration(configuration)
                if _matches_configuration_filters(
                    configuration,
                    project,
                    filters,
                    include_keyword=bool(filters.get("keyword")) and not matching_project_text,
                    include_notes=bool(filters.get("notes")) and not matching_project_notes,
                ):
                    matching_configurations.append(configuration)

            has_configuration_filters = _has_configuration_filters(filters)
            if has_configuration_filters and not matching_configurations:
                continue
            if filters.get("keyword") and not matching_project_text and not matching_configurations:
                continue
            if filters.get("notes") and not matching_project_notes and not matching_configurations:
                continue

            project.matching_configurations = matching_configurations
            project.matching_configuration_count = len(matching_configurations)
            configuration_prices = [
                item.basic_price for item in matching_configurations
                if item.basic_price is not None
            ]
            configuration_price_per_sqft = [
                item.price_per_sqft for item in matching_configurations
                if item.price_per_sqft is not None
            ]
            project.display_starting_price = (
                project.starting_price
                if project.starting_price is not None
                else min(configuration_prices, default=None)
            )
            project.display_price_per_sqft = (
                project.price_per_sqft
                if project.price_per_sqft is not None
                else min(configuration_price_per_sqft, default=None)
            )
            matching_projects.append(project)

            project_type = project.project_type or "OTHER"
            project_type_counts[project_type] = (
                project_type_counts.get(project_type, 0) + 1
            )
            total_configurations += len(matching_configurations)

        if matching_projects:
            developer.matching_projects = matching_projects
            filtered_developers.append(developer)
            total_projects += len(matching_projects)

    active_filter_chips = _build_filter_chips(request, search_form, catalog)
    return render(
        request,
        "property_catalog/catalog_detail.html",
        {
            "catalog": catalog,
            "developers": filtered_developers,
            "search_form": search_form,
            "total_developers": len(filtered_developers),
            "total_projects": total_projects,
            "total_configurations": total_configurations,
            "project_type_counts": project_type_counts,
            "total_project_types": len(project_type_counts),
            "active_filter_chips": active_filter_chips,
            "active_filter_count": len(active_filter_chips),
            "has_active_filters": bool(active_filter_chips),
            "clear_filters_url": reverse(
                "property_catalog:catalog_detail",
                kwargs={"pk": catalog.pk},
            ),
            "reset_filters_url": _reset_filters_url(request, catalog),
        },
    )


def _matches_project_filters(project, developer, filters):
    if filters.get("developer") and str(developer.pk) != filters["developer"]:
        return False
    if filters.get("project") and str(project.pk) != filters["project"]:
        return False
    if filters.get("project_type") and project.project_type != filters["project_type"]:
        return False
    if filters.get("status") and project.status != filters["status"]:
        return False

    location = getattr(project, "location", None)
    for field_name in ("locality", "city", "district", "state", "pincode"):
        value = filters.get(field_name, "").strip()
        if value and (
            not location
            or value.casefold() not in getattr(location, field_name, "").casefold()
        ):
            return False

    location_query = filters.get("location", "").strip().casefold()
    if location_query:
        location_values = (
            getattr(location, field, "")
            for field in ("locality", "city", "district", "state", "pincode")
        ) if location else ()
        if not any(location_query in value.casefold() for value in location_values if value):
            return False
    return True


def _matches_keyword(project, developer, keyword):
    if not keyword:
        return True

    searchable_values = [
        developer.name,
        project.name,
        project.project_type,
        project.status,
        project.channel_partner_notes,
        project.total_land_area,
    ]
    location = getattr(project, "location", None)
    if location:
        searchable_values.extend(
            getattr(location, field, "")
            for field in ("locality", "city", "district", "state", "pincode")
        )
    searchable_values.extend(item.text for item in project.highlights.all())
    searchable_values.extend(item.name for item in project.amenities.all())
    return any(keyword.casefold() in str(value).casefold() for value in searchable_values if value)


def _matches_configuration_filters(
    configuration,
    project,
    filters,
    include_keyword=False,
    include_notes=False,
):
    property_type = filters.get("property_type")
    if property_type and configuration.property_type != property_type:
        return False

    facing = filters.get("facing")
    if facing and configuration.facing != facing:
        return False

    availability = filters.get("availability")
    if availability and configuration.availability != availability:
        return False

    possession = filters.get("possession", "").strip()
    if possession and possession.casefold() not in configuration.possession.casefold():
        return False

    bhk = filters.get("bhk")
    if bhk and not _matches_bhk(configuration, bhk):
        return False

    min_budget = filters.get("min_budget")
    max_budget = filters.get("max_budget")
    if min_budget is not None or max_budget is not None:
        price = configuration.basic_price
        if price is None:
            price = project.starting_price
        if price is None or (min_budget is not None and price < min_budget):
            return False
        if max_budget is not None and price > max_budget:
            return False

    min_area = filters.get("min_area")
    max_area = filters.get("max_area")
    if min_area is not None or max_area is not None:
        areas = _configuration_areas(configuration)
        if not any(
            (min_area is None or area >= min_area)
            and (max_area is None or area <= max_area)
            for area in areas
        ):
            return False

    min_price_per_sqft = filters.get("min_price_per_sqft")
    max_price_per_sqft = filters.get("max_price_per_sqft")
    if min_price_per_sqft is not None or max_price_per_sqft is not None:
        price_per_sqft = configuration.price_per_sqft
        if price_per_sqft is None:
            price_per_sqft = project.price_per_sqft
        if price_per_sqft is None:
            return False
        if min_price_per_sqft is not None and price_per_sqft < min_price_per_sqft:
            return False
        if max_price_per_sqft is not None and price_per_sqft > max_price_per_sqft:
            return False

    amenities = filters.get("amenity", [])
    if any(
        not _matches_amenity(configuration, project, amenity)
        for amenity in amenities
    ):
        return False

    features = filters.get("feature", [])
    if any(
        not _matches_feature(configuration, project, feature)
        for feature in features
    ):
        return False

    if include_keyword and not _matches_configuration_keyword(configuration, filters.get("keyword", "")):
        return False
    if include_notes and not _matches_configuration_notes(
        configuration,
        filters.get("notes", ""),
    ):
        return False
    return True


def _matches_bhk(configuration, selection):
    if selection.startswith("bedrooms:"):
        bedrooms = int(selection.partition(":")[2])
        if configuration.bedrooms == bedrooms:
            return True
        return re.fullmatch(
            rf"\s*{bedrooms}\s*(?:BHK)?\s*",
            configuration.bhk,
            re.IGNORECASE,
        ) is not None
    return configuration.bhk.casefold() == selection.partition(":")[2].casefold()


def _configuration_areas(configuration):
    areas = [
        configuration.built_up_area_sq_ft,
        configuration.super_built_up_area_sq_ft,
        configuration.carpet_area_sq_ft,
        configuration.plot_area_sq_ft,
        configuration.office_area_sq_ft,
        configuration.retail_area_sq_ft,
    ]
    if configuration.plot_area_sq_yd is not None:
        areas.append(configuration.plot_area_sq_yd * Decimal("9"))
    return [area for area in areas if area is not None]


def _matches_amenity(configuration, project, amenity):
    target = amenity.casefold()
    values = list(CatalogSearchForm._strings(configuration.amenities))
    values.extend(item.name for item in project.amenities.all())
    return any(value.casefold() == target for value in values)


def _matches_feature(configuration, project, feature):
    target = feature.casefold()
    values = list(CatalogSearchForm._strings(configuration.features))
    values.extend(item.text for item in project.highlights.all())
    return any(value.casefold() == target for value in values)


def _matches_project_notes(project, notes):
    return bool(
        notes
        and notes.casefold() in project.channel_partner_notes.casefold()
    )


def _matches_configuration_notes(configuration, notes):
    return any(
        notes.casefold() in value.casefold()
        for value in (configuration.notes, configuration.description)
        if value
    )


def _matches_configuration_keyword(configuration, keyword):
    searchable_values = [
        configuration.type_name,
        configuration.property_type,
        configuration.description,
        configuration.bhk,
        configuration.facing,
        configuration.parking,
        configuration.suitable_for,
        configuration.availability,
        configuration.possession,
        configuration.notes,
        *CatalogSearchForm._strings(configuration.amenities),
        *CatalogSearchForm._strings(configuration.features),
    ]
    return any(keyword.casefold() in str(value).casefold() for value in searchable_values if value)


def _decorate_configuration(configuration):
    bhk_text = configuration.bhk.strip()
    if not bhk_text and configuration.bedrooms is not None:
        bhk_text = str(configuration.bedrooms)
    if re.fullmatch(r"\d+", bhk_text):
        bhk_text = f"{bhk_text} BHK"
    bedroom_count = configuration.bedrooms
    if bedroom_count is None:
        match = re.match(r"\s*(\d+)", configuration.bhk)
        bedroom_count = int(match.group(1)) if match else None
    name_has_bhk = bedroom_count is not None and re.search(
        rf"(?<!\d){bedroom_count}\s*[- ]?\s*BHK\b",
        configuration.type_name,
        re.IGNORECASE,
    )
    configuration.display_bhk = "" if name_has_bhk else bhk_text
    configuration.display_features = list(
        CatalogSearchForm._strings(configuration.amenities)
    ) + list(CatalogSearchForm._strings(configuration.features))


def _has_configuration_filters(filters):
    for name in (
        "property_type",
        "min_budget",
        "max_budget",
        "bhk",
        "facing",
        "availability",
        "possession",
        "min_area",
        "max_area",
        "amenity",
        "min_price_per_sqft",
        "max_price_per_sqft",
        "feature",
    ):
        value = filters.get(name)
        if value not in (None, "", []):
            return True
    return False


def _build_filter_chips(request, form, catalog):
    labels = {
        "min_budget": "Minimum budget",
        "max_budget": "Maximum budget",
        "min_area": "Minimum area",
        "max_area": "Maximum area",
        "min_price_per_sqft": "Minimum price / sq. ft.",
        "max_price_per_sqft": "Maximum price / sq. ft.",
        "keyword": "Search",
        "location": "Location",
    }
    chips = []
    clear_url = reverse("property_catalog:catalog_detail", kwargs={"pk": catalog.pk})
    for field_name, field in form.fields.items():
        selected_values = [
            value for value in request.GET.getlist(field_name) if value
        ]
        for selected in selected_values:
            query = request.GET.copy()
            remaining = query.getlist(field_name)
            remaining.remove(selected)
            if remaining:
                query.setlist(field_name, remaining)
            else:
                query.pop(field_name, None)
            try:
                display_value = dict(field.choices).get(selected, selected)
            except (AttributeError, TypeError):
                display_value = selected
            label = labels.get(field_name, field.label)
            if field_name in {
                "min_budget",
                "max_budget",
                "min_price_per_sqft",
            }:
                display_value = f"₹{display_value}"
            elif field_name in {"min_area", "max_area"}:
                display_value = f"{display_value} sq. ft."
            chips.append(
                {
                    "label": f"{label}: {display_value}",
                    "url": f"{clear_url}?{query.urlencode()}" if query else clear_url,
                }
            )
    return chips


def _reset_filters_url(request, catalog):
    keyword = request.GET.get("keyword", "").strip()
    clear_url = reverse("property_catalog:catalog_detail", kwargs={"pk": catalog.pk})
    if not keyword:
        return clear_url
    query = request.GET.copy()
    query.clear()
    query["keyword"] = keyword
    return f"{clear_url}?{query.urlencode()}"