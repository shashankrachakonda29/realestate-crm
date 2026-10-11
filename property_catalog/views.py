from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import PropertyCatalogImportForm
from .models import PropertyCatalog
from .services import import_catalog, PropertyCatalogImportError


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

            try:

                uploaded_file = form.cleaned_data["json_file"]
                data = form.parse_json(uploaded_file)

                if not isinstance(data, dict):
                    raise ValueError("JSON root must be an object.")

                request.session["property_catalog_preview"] = data

                return redirect(
                    "property_catalog:preview"
                )

            except Exception as exc:

                form.add_error(
                    "json_file",
                    str(exc),
                )

    else:

        form = PropertyCatalogImportForm()

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

    if request.method == "POST":

        action = request.POST.get(
            "action"
        )

        if action == "confirm":

            try:

                catalog = import_catalog(data)

                request.session.pop(
                    "property_catalog_preview",
                    None,
                )

                return redirect(
                    "property_catalog:catalog_detail",
                    pk=catalog.pk,
                )

            except Exception as exc:

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
                        "import_error": str(exc),
                    },
                )

        if action == "cancel":

            request.session.pop(
                "property_catalog_preview",
                None,
            )

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
        },
    )


@login_required
def catalog_detail(request, pk):
    catalog = get_object_or_404(
        PropertyCatalog,
        pk=pk,
    )

    developers = list(
        catalog.developers.prefetch_related(
            "projects__location",
            "projects__highlights",
            "projects__amenities",
            "projects__configurations",
        )
    )

    total_projects = 0
    project_type_counts = {}

    for developer in developers:
        projects = list(developer.projects.all())
        total_projects += len(projects)

        for project in projects:
            project_type = project.project_type or "OTHER"

            project_type_counts[project_type] = (
                project_type_counts.get(project_type, 0) + 1
            )

    return render(
        request,
        "property_catalog/catalog_detail.html",
        {
            "catalog": catalog,
            "developers": developers,
            "total_developers": len(developers),
            "total_projects": total_projects,
            "project_type_counts": project_type_counts,
            "total_project_types": len(project_type_counts),
        },
    )