from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from accounts.permissions import require_roles

from .forms import SiteVisitForm
from .models import SiteVisit


# =====================================================
# ACCESS HELPER
# =====================================================

def get_sitevisit_queryset(user):

    visits = SiteVisit.objects.select_related(
        "lead",
        "project",
        "assigned_to",
    )

    # Sales can only see visits for their own leads
    if user.role == user.Role.SALES:

        visits = visits.filter(
            lead__assigned_to=user
        )

    return visits


# =====================================================
# LIST
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
    "VIEWER",
)
def sitevisit_list(request):

    site_visits = get_sitevisit_queryset(
        request.user
    ).order_by(
        "-visit_date",
        "-visit_time",
    )

    return render(
        request,
        "sitevisits/list.html",
        {
            "site_visits": site_visits,
        },
    )


# =====================================================
# CREATE
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
)
def sitevisit_create(request):

    if request.method == "POST":

        form = SiteVisitForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():

            site_visit = form.save(
                commit=False
            )

            # Sales automatically becomes owner
            if request.user.role == request.user.Role.SALES:

                site_visit.assigned_to = request.user

            site_visit.save()

            return redirect(
                "sitevisit_detail",
                pk=site_visit.pk,
            )

    else:
        form = SiteVisitForm(
            user=request.user,
        )

        lead_id = request.GET.get("lead")

        if lead_id:
            from leads.models import Lead

            if request.user.role == request.user.Role.SALES:

                lead = get_object_or_404(
                    Lead,
                    pk=lead_id,
                    assigned_to=request.user,
                )

                form.fields["lead"].initial = lead.pk

            else:

                form.fields["lead"].initial = lead_id
    return render(
        request,
        "sitevisits/form.html",
        {
            "form": form,
            "title": "Schedule Site Visit",
        },
    )


# =====================================================
# DETAIL
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
    "VIEWER",
)
def sitevisit_detail(request, pk):

    site_visit = get_object_or_404(
        get_sitevisit_queryset(
            request.user
        ),
        pk=pk,
    )

    return render(
        request,
        "sitevisits/detail.html",
        {
            "site_visit": site_visit,
        },
    )


# =====================================================
# EDIT
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
)
def sitevisit_edit(request, pk):

    site_visit = get_object_or_404(
        get_sitevisit_queryset(
            request.user
        ),
        pk=pk,
    )

    if request.method == "POST":

        form = SiteVisitForm(
            request.POST,
            instance=site_visit,
            user=request.user,
        )

        if form.is_valid():

            updated_visit = form.save(
                commit=False
            )

            # Sales cannot reassign
            if request.user.role == request.user.Role.SALES:

                updated_visit.assigned_to = (
                    site_visit.assigned_to
                )

                updated_visit.lead = (
                    site_visit.lead
                )

            updated_visit.save()

            return redirect(
                "sitevisit_detail",
                pk=site_visit.pk,
            )

    else:

        form = SiteVisitForm(
            instance=site_visit,
            user=request.user,
        )

    return render(
        request,
        "sitevisits/form.html",
        {
            "form": form,
            "title": "Edit Site Visit",
            "site_visit": site_visit,
        },
    )


# =====================================================
# STATUS UPDATE
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
)
def sitevisit_status_update(request, pk):

    site_visit = get_object_or_404(
        get_sitevisit_queryset(
            request.user
        ),
        pk=pk,
    )

    if request.method == "POST":

        status = request.POST.get(
            "status"
        )

        valid_statuses = {
            value
            for value, label
            in SiteVisit.Status.choices
        }

        if status in valid_statuses:

            site_visit.status = status

            site_visit.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

    return redirect(
        "sitevisit_detail",
        pk=site_visit.pk,
    )


# =====================================================
# DELETE
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
)
def sitevisit_delete(request, pk):

    site_visit = get_object_or_404(
        SiteVisit,
        pk=pk,
    )

    if request.method == "POST":

        site_visit.delete()

        return redirect(
            "sitevisit_list"
        )

    return render(
        request,
        "sitevisits/delete.html",
        {
            "site_visit": site_visit,
        },
    )