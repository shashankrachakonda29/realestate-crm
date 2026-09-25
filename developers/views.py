from django.db import models
from django.db.models import ProtectedError,Count,Prefetch,Min
from django.shortcuts import get_object_or_404, redirect, render

from .models import Developer

from inventory.models import Inventory


def developer_list(request):
    search = request.GET.get("search", "").strip()

    developers = (
        Developer.objects
        .annotate(
            project_count=Count("projects"),
            villa_count=Count(
                "projects",
                filter=models.Q(
                    projects__project_type="VILLAS"
                ),
            ),
            apartment_count=Count(
                "projects",
                filter=models.Q(
                    projects__project_type="APARTMENTS"
                ),
            ),
            plot_count=Count(
                "projects",
                filter=models.Q(
                    projects__project_type="PLOTS"
                ),
            ),
            commercial_count=Count(
                "projects",
                filter=models.Q(
                    projects__project_type="COMMERCIAL"
                ),
            ),
        )
        .order_by("name")
    )

    if search:
        developers = developers.filter(
            name__icontains=search
        )

    return render(
        request,
        "developers/list.html",
        {
            "developers": developers,
            "search": search,
        },
    )
def developer_create(request):

    if request.method == "POST":

        Developer.objects.create(
            name=request.POST.get("name", "").strip(),
            description=request.POST.get(
                "description", ""
            ).strip(),
            website=request.POST.get(
                "website", ""
            ).strip(),
            contact_person=request.POST.get(
                "contact_person", ""
            ).strip(),
            phone=request.POST.get(
                "phone", ""
            ).strip(),
            email=request.POST.get(
                "email", ""
            ).strip(),
            address=request.POST.get(
                "address", ""
            ).strip(),
            is_active=request.POST.get(
                "is_active"
            ) == "on",
        )

        return redirect("developer_list")

    return render(
        request,
        "developers/form.html",
        {
            "title": "Add Developer",
            "developer": None,
        },
    )


# def developer_detail(request, pk):

#     developer = get_object_or_404(
#         Developer,
#         pk=pk,
#     )

#     # Optional property type filter
#     property_type = request.GET.get("property_type")

#     projects = (
#         developer.projects
#         .select_related("location")
#         .prefetch_related(
#             Prefetch(
#                 "inventory",
#                 queryset=Inventory.objects.filter(
#                     status=Inventory.Status.AVAILABLE,
#                     current_price__isnull=False,
#                 ).order_by("current_price"),
#                 to_attr="available_inventory",
#             )
#         )
#     )

#     # Filter projects by property type
#     if property_type:
#         projects = projects.filter(
#             inventory__property_type=property_type
#         ).distinct()

#     projects = projects.order_by("name")

#     return render(
#         request,
#         "developers/detail.html",
#         {
#             "developer": developer,
#             "projects": projects,
#             "project_count": projects.count(),
#             "property_type": property_type,
#         },
#     )


# def developer_detail(request, pk):

#     developer = get_object_or_404(
#         Developer,
#         pk=pk,
#     )

#     property_type = request.GET.get("property_type")

#     # -----------------------------------------
#     # PROJECTS
#     # -----------------------------------------

#     projects = developer.projects.select_related(
#         "location"
#     )

#     # If a property type was clicked,
#     # show only projects having that type
#     if property_type:
#         projects = projects.filter(
#             inventory__property_type=property_type
#         ).distinct()

#     projects = projects.order_by("name")

#     # -----------------------------------------
#     # INVENTORY
#     # -----------------------------------------

#     inventory_queryset = Inventory.objects.filter(
#         current_price__isnull=False,
#     )

#     # Filter inventory by selected property type
#     if property_type:
#         inventory_queryset = inventory_queryset.filter(
#             property_type=property_type
#         )

#     inventory_queryset = inventory_queryset.order_by(
#         "current_price"
#     )

#     projects = projects.prefetch_related(
#         Prefetch(
#             "inventory",
#             queryset=inventory_queryset,
#             to_attr="available_inventory",
#         )
#     )
#     print("developer_detail:", developer)
#     print("property_type:", property_type)
#     print("projects:", list(projects.values("id", "name")))
#     return render(
#         request,
#         "developers/detail.html",
#         {
#             "developer": developer,
#             "projects": projects,
#             "project_count": projects.count(),
#             "property_type": property_type,
#         },
#     )

def developer_detail(request, pk):

    developer = get_object_or_404(
        Developer,
        pk=pk,
    )

    # -----------------------------------------
    # PROJECTS
    # -----------------------------------------

    projects = (
        developer.projects
        .select_related("location")
        .annotate(
            inventory_count=Count(
                "inventory",
                distinct=True,
            )
        )
        .order_by("name")
    )

    # -----------------------------------------
    # INVENTORY
    # -----------------------------------------

    inventory_queryset = (
        Inventory.objects
        .filter(
            current_price__isnull=False,
        )
        .order_by("current_price")
    )

    projects = projects.prefetch_related(
        Prefetch(
            "inventory",
            queryset=inventory_queryset,
            to_attr="available_inventory",
        )
    )

    # -----------------------------------------
    # RESPONSE
    # -----------------------------------------

    return render(
        request,
        "developers/detail.html",
        {
            "developer": developer,
            "projects": projects,
            "project_count": projects.count(),
        },
    )
# Developer under Projects View
def developer_projects(request, pk):

    developer = get_object_or_404(
        Developer,
        pk=pk,
    )

    property_type = request.GET.get("property_type")

    projects = (
        developer.projects
        .select_related("location")
    )

    # -----------------------------------------
    # FILTER BY PROPERTY TYPE
    # -----------------------------------------

    project_type_map = {
        "APARTMENT": "APARTMENTS",
        "APARTMENTS": "APARTMENTS",

        "VILLA": "VILLAS",
        "VILLAS": "VILLAS",

        "PLOT": "PLOTS",
        "PLOTS": "PLOTS",

        "COMMERCIAL": "COMMERCIAL",

        "FARM_LAND": "FARM_LANDS",
        "FARM_LANDS": "FARM_LANDS",

        "OTHER": "OTHER",
    }

    # ALL = show every project
    if property_type and property_type != "ALL":

        selected_project_type = project_type_map.get(
            property_type
        )

        if selected_project_type:
            projects = projects.filter(
                project_type=selected_project_type
            )

    projects = (
        projects
        .prefetch_related(
            Prefetch(
                "inventory",
                queryset=Inventory.objects.filter(
                    status=Inventory.Status.AVAILABLE,
                    current_price__isnull=False,
                ).order_by("current_price"),
                to_attr="available_inventory",
            )
        )
        .order_by("name")
    )

    return render(
        request,
        "developers/dev_project.html",
        {
            "developer": developer,
            "projects": projects,
            "project_count": projects.count(),
            "property_type": property_type,
        },
    )

# Developer Edit View

def developer_edit(request, pk):

    developer = get_object_or_404(
        Developer,
        pk=pk,
    )

    if request.method == "POST":

        developer.name = request.POST.get(
            "name", ""
        ).strip()

        developer.description = request.POST.get(
            "description", ""
        ).strip()

        developer.website = request.POST.get(
            "website", ""
        ).strip()

        developer.contact_person = request.POST.get(
            "contact_person", ""
        ).strip()

        developer.phone = request.POST.get(
            "phone", ""
        ).strip()

        developer.email = request.POST.get(
            "email", ""
        ).strip()

        developer.address = request.POST.get(
            "address", ""
        ).strip()

        developer.is_active = (
            request.POST.get("is_active") == "on"
        )

        developer.save()

        return redirect(
            "developer_detail",
            pk=developer.pk,
        )

    return render(
        request,
        "developers/form.html",
        {
            "title": "Edit Developer",
            "developer": developer,
        },
    )


def developer_delete(request, pk):

    developer = get_object_or_404(
        Developer,
        pk=pk,
    )

    if request.method == "POST":
        try:
            developer.delete()
        except ProtectedError:
            return render(
                request,
                "developers/detail.html",
                {
                    "developer": developer,
                    "delete_blocked": True,
                    "related_projects": developer.projects.all().order_by(
                        "name"
                    ),
                    "projects": developer.projects.select_related(
                        "location",
                    ).order_by("name"),
                    "project_count": developer.projects.count(),
                },
            )

        return redirect("developer_list")

    return render(
        request,
        "developers/detail.html",
        {
            "developer": developer,
            "confirm_delete": True,
            "projects": developer.projects.select_related(
                "location",
            ).order_by("name"),
            "project_count": developer.projects.count(),
        },
    )