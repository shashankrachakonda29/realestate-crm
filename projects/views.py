from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Count, Min, Max
from .models import Project
from developers.models import Developer
from locations.models import Location
from inventory.models import Inventory


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
            project_status=request.POST.get(
                "project_status"    
            ),

            is_active=request.POST.get("is_active") == "on",

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
            "project_status": Project.ProjectStatus.choices,
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
        project.project_status = request.POST.get(
            "project_status"    
        )

        project.status = request.POST.get(
            "status"
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
            "project_status": Project.ProjectStatus.choices,
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


def project_inventory(request, project_id):

    project = get_object_or_404(
        Project,
        pk=project_id,
    )

    inventory = Inventory.objects.filter(
        project=project,
        status=Inventory.Status.AVAILABLE,
    )

    bhk_groups = (
        inventory
        .filter(bhk__isnull=False)
        .values("bhk")
        .annotate(
            unit_count=Count("id"),
            min_sft=Min("unit_size_sq_ft"),
            max_sft=Max("unit_size_sq_ft"),
            min_price=Min("current_price"),
        )
        .order_by("bhk")
    )

    # Add facings for each BHK
    for item in bhk_groups:

        item["facings"] = list(
            inventory
            .filter(
                bhk=item["bhk"],
                facing__isnull=False,
            )
            .exclude(
                facing=""
            )
            .values_list(
                "facing",
                flat=True,
            )
            .distinct()
        )

    return render(
        request,
        "developers/dev_project_inventory.html",
        {
            "project": project,
            "bhk_groups": bhk_groups,
        },
    )

def project_inventory_bhk(request, project_id, bhk):

    project = get_object_or_404(
        Project.objects.select_related(
            "developer",
            "location",
        ),
        pk=project_id,
    )

    inventory = (
        Inventory.objects
        .filter(
            project=project,
            bhk=bhk,
            status=Inventory.Status.AVAILABLE,
        )
        .order_by("current_price")
    )

    return render(
        request,
        "developers/dev_project_inventory_bhk.html",
        {
            "project": project,
            "bhk": bhk,
            "inventory": inventory,
        },
    )