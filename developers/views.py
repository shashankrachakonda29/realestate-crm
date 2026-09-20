from django.shortcuts import get_object_or_404, redirect, render

from .models import Developer


def developer_list(request):
    search = request.GET.get("search", "").strip()

    developers = Developer.objects.all().order_by("name")

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


def developer_detail(request, pk):

    developer = get_object_or_404(
        Developer,
        pk=pk,
    )

    return render(
        request,
        "developers/detail.html",
        {
            "developer": developer,
        },
    )


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
        developer.delete()

        return redirect("developer_list")

    return render(
        request,
        "developers/detail.html",
        {
            "developer": developer,
            "confirm_delete": True,
        },
    )