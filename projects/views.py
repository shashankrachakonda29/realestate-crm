from django.shortcuts import get_object_or_404, redirect, render

from .models import Project
from developers.models import Developer
from locations.models import Location


def project_list(request):

    search = request.GET.get("search", "").strip()

    projects = (
        Project.objects
        .select_related("developer", "location")
        .order_by("name")
    )

    if search:
        projects = projects.filter(
            name__icontains=search
        )

    return render(
        request,
        "projects/list.html",
        {
            "projects": projects,
            "search": search,
        },
    )


def project_create(request):

    developers = Developer.objects.filter(
        is_active=True
    ).order_by("name")

    locations = Location.objects.filter(
        is_active=True
    ).order_by("name")

    if request.method == "POST":

        Project.objects.create(
            name=request.POST.get(
                "name", ""
            ).strip(),

            developer_id=request.POST.get(
                "developer"
            ),

            location_id=request.POST.get(
                "location"
            ),

            project_type=request.POST.get(
                "project_type"
            ),

            description=request.POST.get(
                "description", ""
            ).strip(),

            total_land_acres=(
                request.POST.get("total_land_acres")
                or None
            ),

            total_land_guntas=(
                request.POST.get("total_land_guntas")
                or None
            ),

            total_units=(
                request.POST.get("total_units")
                or None
            ),

            bhk=request.POST.get(
                "bhk", ""
            ).strip(),

            possession_date=(
                request.POST.get("possession_date")
                or None
            ),

            rera_number=request.POST.get(
                "rera_number", ""
            ).strip(),

            rera_status=request.POST.get(
                "rera_status", ""
            ).strip(),

            amenities=request.POST.get(
                "amenities", ""
            ).strip(),

            website=request.POST.get(
                "website", ""
            ).strip(),

            google_maps_url=request.POST.get(
                "google_maps_url", ""
            ).strip(),

            is_active=request.POST.get(
                "is_active"
            ) == "on",
        )

        return redirect("project_list")

    return render(
    request,
    "projects/form.html",
    {
        "title": "Add Project",
        "project": None,
        "developers": developers,
        "locations": locations,
        "project_types": Project.ProjectType.choices,
    },
)


def project_detail(request, pk):

    project = get_object_or_404(
        Project.objects.select_related(
            "developer",
            "location",
        ),
        pk=pk,
    )

    return render(
        request,
        "projects/detail.html",
        {
            "project": project,
        },
    )


def project_edit(request, pk):

    project = get_object_or_404(
        Project,
        pk=pk,
    )

    developers = Developer.objects.filter(
        is_active=True
    ).order_by("name")

    locations = Location.objects.filter(
        is_active=True
    ).order_by("name")

    if request.method == "POST":

        project.name = request.POST.get(
            "name", ""
        ).strip()

        project.developer_id = request.POST.get(
            "developer"
        )

        project.location_id = request.POST.get(
            "location"
        )

        project.project_type = request.POST.get(
            "project_type"
        )

        project.description = request.POST.get(
            "description", ""
        ).strip()

        project.total_land_acres = (
            request.POST.get(
                "total_land_acres"
            ) or None
        )

        project.total_land_guntas = (
            request.POST.get(
                "total_land_guntas"
            ) or None
        )

        project.total_units = (
            request.POST.get(
                "total_units"
            ) or None
        )

        project.bhk = request.POST.get(
            "bhk", ""
        ).strip()

        project.possession_date = (
            request.POST.get(
                "possession_date"
            ) or None
        )

        project.rera_number = request.POST.get(
            "rera_number", ""
        ).strip()

        project.rera_status = request.POST.get(
            "rera_status", ""
        ).strip()

        project.amenities = request.POST.get(
            "amenities", ""
        ).strip()

        project.website = request.POST.get(
            "website", ""
        ).strip()

        project.google_maps_url = request.POST.get(
            "google_maps_url", ""
        ).strip()

        project.is_active = (
            request.POST.get("is_active") == "on"
        )

        project.save()

        return redirect(
            "project_detail",
            pk=project.pk,
        )

    return render(
    request,
    "projects/form.html",
    {
        "title": "Edit Project",
        "project": project,
        "developers": developers,
        "locations": locations,
        "project_types": Project.ProjectType.choices,
    },
)


def project_delete(request, pk):

    project = get_object_or_404(
        Project,
        pk=pk,
    )

    if request.method == "POST":

        project.delete()

        return redirect("project_list")

    return render(
        request,
        "projects/detail.html",
        {
            "project": project,
            "confirm_delete": True,
        },
    )