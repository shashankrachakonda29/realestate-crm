from django.shortcuts import get_object_or_404, redirect, render

from .models import Location


def location_list(request):
    search = request.GET.get("search", "").strip()

    locations = Location.objects.all().order_by(
        "name"
    )

    if search:
        locations = locations.filter(
            name__icontains=search
        )

    return render(
        request,
        "locations/list.html",
        {
            "locations": locations,
            "search": search,
        },
    )


def location_create(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if Location.objects.filter(name__iexact=name).exists():
            return render(
                request,
                "locations/form.html",
                {
                    "title": "Add Location",
                    "location": None,
                    "error": f'Location "{name}" already exists.',
                },
            )

        Location.objects.create(
            name=name,

            city=request.POST.get(
                "city", ""
            ).strip(),

            state=request.POST.get(
                "state", ""
            ).strip(),

            pincode=request.POST.get(
                "pincode", ""
            ).strip(),

            latitude=request.POST.get(
                "latitude"
            ) or None,

            longitude=request.POST.get(
                "longitude"
            ) or None,

            google_maps_url=request.POST.get(
                "google_maps_url", ""
            ).strip(),

            description=request.POST.get(
                "description", ""
            ).strip(),

            is_active=request.POST.get(
                "is_active"
            ) == "on",
        )

        return redirect("location_list")

    return render(
        request,
        "locations/form.html",
        {
            "title": "Add Location",
            "location": None,
        },
    )
def location_detail(request, pk):

    location = get_object_or_404(
        Location,
        pk=pk,
    )

    return render(
        request,
        "locations/detail.html",
        {
            "location": location,
        },
    )


def location_edit(request, pk):

    location = get_object_or_404(
        Location,
        pk=pk,
    )

    if request.method == "POST":

        location.name = request.POST.get(
            "name", ""
        ).strip()

        location.city = request.POST.get(
            "city", ""
        ).strip()

        location.state = request.POST.get(
            "state", ""
        ).strip()

        location.pincode = request.POST.get(
            "pincode", ""
        ).strip()

        location.latitude = (
            request.POST.get("latitude") or None
        )

        location.longitude = (
            request.POST.get("longitude") or None
        )

        location.google_maps_url = request.POST.get(
            "google_maps_url", ""
        ).strip()

        location.description = request.POST.get(
            "description", ""
        ).strip()

        location.is_active = (
            request.POST.get("is_active") == "on"
        )

        location.save()

        return redirect(
            "location_detail",
            pk=location.pk,
        )

    return render(
        request,
        "locations/form.html",
        {
            "title": "Edit Location",
            "location": location,
        },
    )


def location_delete(request, pk):

    location = get_object_or_404(
        Location,
        pk=pk,
    )

    if request.method == "POST":

        location.delete()

        return redirect("location_list")

    return render(
        request,
        "locations/detail.html",
        {
            "location": location,
            "confirm_delete": True,
        },
    )