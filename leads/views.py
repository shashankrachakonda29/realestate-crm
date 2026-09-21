from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LeadForm, LeadActivityForm
from .models import Lead, LeadActivity

from accounts.permissions import require_roles


User = get_user_model()


# =====================================================
# LEAD ACCESS HELPER
# =====================================================

def get_sales_lead_queryset(user):

    if user.role == User.Role.SALES:
        return Lead.objects.filter(
            assigned_to=user
        )

    return Lead.objects.all()


# =====================================================
# LEAD ASSIGNMENT HELPER
# =====================================================

def can_assign_leads(user):
    """
    Only Admin and Manager can assign/reassign leads.
    """

    return (
        user.is_authenticated
        and user.role in [
            User.Role.ADMIN,
            User.Role.MANAGER,
        ]
    )


# =====================================================
# PIPELINE
# =====================================================

def lead_pipeline(request):

    leads = get_sales_lead_queryset(
        request.user
    )

    # -----------------------------------------
    # Status counts
    # -----------------------------------------

    total_leads = leads.count()

    status_counts = {
        "new": leads.filter(
            status=Lead.Status.NEW
        ).count(),

        "contacted": leads.filter(
            status=Lead.Status.CONTACTED
        ).count(),

        "interested": leads.filter(
            status=Lead.Status.INTERESTED
        ).count(),

        "site_visit": leads.filter(
            status=Lead.Status.SITE_VISIT
        ).count(),

        "negotiation": leads.filter(
            status=Lead.Status.NEGOTIATION
        ).count(),

        "booked": leads.filter(
            status=Lead.Status.BOOKED
        ).count(),

        "lost": leads.filter(
            status=Lead.Status.LOST
        ).count(),

        "on_hold": leads.filter(
            status=Lead.Status.ON_HOLD
        ).count(),
    }

    # -----------------------------------------
    # Today's follow-ups
    # -----------------------------------------

    today = timezone.localdate()

    today_followups = leads.filter(
        next_follow_up__date=today
    ).select_related(
        "assigned_to",
        "interested_project",
    ).order_by(
        "next_follow_up"
    )

    # -----------------------------------------
    # Overdue follow-ups
    # -----------------------------------------

    overdue_followups = leads.filter(
        next_follow_up__lt=timezone.now()
    ).exclude(
        status__in=[
            Lead.Status.BOOKED,
            Lead.Status.LOST,
        ]
    ).select_related(
        "assigned_to",
        "interested_project",
    ).order_by(
        "next_follow_up"
    )

    # -----------------------------------------
    # Upcoming follow-ups
    # -----------------------------------------

    upcoming_followups = leads.filter(
        next_follow_up__gt=timezone.now()
    ).select_related(
        "assigned_to",
        "interested_project",
    ).order_by(
        "next_follow_up"
    )[:10]

    context = {
        "total_leads": total_leads,
        "status_counts": status_counts,

        "today_followups": today_followups,
        "overdue_followups": overdue_followups,
        "upcoming_followups": upcoming_followups,
    }

    return render(
        request,
        "leads/pipeline.html",
        context
    )


# =====================================================
# LIST
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
    "VIEWER",
)
def lead_list(request):

    # -----------------------------------------
    # Base queryset
    # -----------------------------------------

    leads = get_sales_lead_queryset(
        request.user
    ).select_related(
        "assigned_to",
        "interested_project",
    ).order_by(
        "-created_at"
    )

    # -----------------------------------------
    # Search
    # -----------------------------------------

    search = request.GET.get(
        "search",
        ""
    ).strip()

    selected_status = request.GET.get(
        "status",
        ""
    )

    selected_source = request.GET.get(
        "source",
        ""
    )

    selected_property_type = request.GET.get(
        "preferred_property_type",
        ""
    )

    selected_assigned_to = request.GET.get(
        "assigned_to",
        ""
    )

    # -----------------------------------------
    # SEARCH FILTER
    # -----------------------------------------

    if search:

        leads = leads.filter(
            Q(name__icontains=search)
            | Q(phone__icontains=search)
            | Q(email__icontains=search)
            | Q(preferred_location__icontains=search)
            | Q(preferred_property_type__icontains=search)
            | Q(requirement__icontains=search)
            | Q(notes__icontains=search)
            | Q(interested_project__name__icontains=search)
        )

    # -----------------------------------------
    # STATUS FILTER
    # -----------------------------------------

    if selected_status:

        leads = leads.filter(
            status=selected_status
        )

    # -----------------------------------------
    # SOURCE FILTER
    # -----------------------------------------

    if selected_source:

        leads = leads.filter(
            source=selected_source
        )

    # -----------------------------------------
    # PROPERTY TYPE FILTER
    # -----------------------------------------

    if selected_property_type:

        leads = leads.filter(
            preferred_property_type__iexact=selected_property_type
        )

    # -----------------------------------------
    # ASSIGNED USER FILTER
    # -----------------------------------------

    if selected_assigned_to:

        leads = leads.filter(
            assigned_to_id=selected_assigned_to
        )

    # -----------------------------------------
    # USERS
    # -----------------------------------------

    users = User.objects.filter(
        is_active=True
    ).order_by(
        "first_name",
        "username",
    )

    # -----------------------------------------
    # STATUS COUNTS
    # -----------------------------------------

    lead_status_counts = {
        "total": leads.count(),

        "new": leads.filter(
            status=Lead.Status.NEW
        ).count(),

        "contacted": leads.filter(
            status=Lead.Status.CONTACTED
        ).count(),

        "interested": leads.filter(
            status=Lead.Status.INTERESTED
        ).count(),

        "site_visit": leads.filter(
            status=Lead.Status.SITE_VISIT
        ).count(),

        "negotiation": leads.filter(
            status=Lead.Status.NEGOTIATION
        ).count(),

        "booked": leads.filter(
            status=Lead.Status.BOOKED
        ).count(),

        "on_hold": leads.filter(
            status=Lead.Status.ON_HOLD
        ).count(),

        "lost": leads.filter(
            status=Lead.Status.LOST
        ).count(),
    }

    # -----------------------------------------
    # CONTEXT
    # -----------------------------------------

    context = {

        "leads": leads,

        "search": search,

        "selected_status": selected_status,

        "selected_source": selected_source,

        "selected_property_type": selected_property_type,

        "selected_assigned_to": selected_assigned_to,

        "statuses": Lead.Status.choices,

        "sources": Lead.Source.choices,

        "users": users,

        "total_leads": leads.count(),

        "lead_status_counts": lead_status_counts,

        "property_types": [
            "Villa",
            "Apartment",
            "Plot",
            "Independent House",
            "Commercial",
            "Other",
        ],
    }

    return render(
        request,
        "leads/list.html",
        context
    )


# =====================================================
# CREATE
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
)
def lead_create(request):

    if request.method == "POST":

        form = LeadForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():

            lead = form.save(
                commit=False
            )

            # -----------------------------------------
            # Sales automatically owns new lead
            # -----------------------------------------

            if request.user.role == User.Role.SALES:

                lead.assigned_to = request.user

            lead.save()

            return redirect(
                "lead_detail",
                pk=lead.pk
            )

    else:

        form = LeadForm(
            user=request.user
        )

    return render(
        request,
        "leads/form.html",
        {
            "form": form,
            "title": "Add Lead",
        }
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
def lead_detail(request, pk):

    lead = get_object_or_404(
        get_sales_lead_queryset(
            request.user
        ).select_related(
            "assigned_to",
            "interested_project",
        ),
        pk=pk
    )

    # -----------------------------------------
    # Activities
    # -----------------------------------------

    activities = lead.activities.select_related(
        "created_by"
    ).order_by(
        "-activity_date",
        "-created_at",
    )

    # -----------------------------------------
    # Activity form
    # -----------------------------------------

    activity_form = LeadActivityForm(
        initial={
            "activity_date": timezone.localtime().strftime(
                "%Y-%m-%dT%H:%M"
            )
        }
    )

    # -----------------------------------------
    # Site visits
    # -----------------------------------------

    site_visits = lead.site_visits.select_related(
        "project",
        "assigned_to",
    ).order_by(
        "-visit_date",
        "-visit_time",
    )

    return render(
        request,
        "leads/detail.html",
        {
            "lead": lead,
            "activities": activities,
            "activity_form": activity_form,
            "site_visits": site_visits,
        }
    )


# =====================================================
# STATUS UPDATE
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
)
def lead_status_update(request, pk):

    lead = get_object_or_404(
        get_sales_lead_queryset(
            request.user
        ),
        pk=pk
    )

    if request.method == "POST":

        status = request.POST.get(
            "status"
        )

        valid_statuses = {
            value
            for value, label
            in Lead.Status.choices
        }

        if status in valid_statuses:

            lead.status = status

            lead.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

    return redirect(
        "lead_detail",
        pk=lead.pk
    )


# =====================================================
# CREATE ACTIVITY
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
)
def lead_activity_create(request, pk):

    lead = get_object_or_404(
        get_sales_lead_queryset(
            request.user
        ),
        pk=pk
    )

    if request.method == "POST":

        form = LeadActivityForm(
            request.POST
        )

        if form.is_valid():

            activity = form.save(
                commit=False
            )

            activity.lead = lead

            if request.user.is_authenticated:

                activity.created_by = request.user

            activity.save()

            return redirect(
                "lead_detail",
                pk=lead.pk
            )

    return redirect(
        "lead_detail",
        pk=lead.pk
    )


# =====================================================
# EDIT
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
)
def lead_edit(request, pk):

    lead = get_object_or_404(
        get_sales_lead_queryset(
            request.user
        ),
        pk=pk
    )

    if request.method == "POST":

        form = LeadForm(
            request.POST,
            instance=lead,
            user=request.user
        )

        if form.is_valid():

            updated_lead = form.save(
                commit=False
            )

            # -----------------------------------------
            # Sales cannot reassign lead
            # -----------------------------------------

            if request.user.role == User.Role.SALES:

                updated_lead.assigned_to = lead.assigned_to

            updated_lead.save()

            return redirect(
                "lead_detail",
                pk=lead.pk
            )

    else:

        form = LeadForm(
            instance=lead,
            user=request.user
        )

    return render(
        request,
        "leads/form.html",
        {
            "form": form,
            "title": "Edit Lead",
            "lead": lead,
        }
    )

# =====================================================
# EDIT ACTIVITY
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
    "SALES",
)
def lead_activity_edit(
    request,
    pk,
    activity_id
):

    lead = get_object_or_404(
        get_sales_lead_queryset(
            request.user
        ),
        pk=pk
    )

    activity = get_object_or_404(
        LeadActivity,
        pk=activity_id,
        lead=lead
    )

    if request.method == "POST":

        form = LeadActivityForm(
            request.POST,
            instance=activity
        )

        if form.is_valid():

            form.save()

            return redirect(
                "lead_detail",
                pk=lead.pk
            )

    else:

        form = LeadActivityForm(
            instance=activity
        )

    return render(
        request,
        "leads/activity_form.html",
        {
            "form": form,
            "lead": lead,
            "activity": activity,
            "title": "Edit Activity",
        }
    )


# =====================================================
# DELETE ACTIVITY
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
)
def lead_activity_delete(
    request,
    pk,
    activity_id
):

    lead = get_object_or_404(
        Lead,
        pk=pk
    )

    activity = get_object_or_404(
        LeadActivity,
        pk=activity_id,
        lead=lead
    )

    if request.method == "POST":

        activity.delete()

        return redirect(
            "lead_detail",
            pk=lead.pk
        )

    return render(
        request,
        "leads/activity_delete.html",
        {
            "lead": lead,
            "activity": activity,
        }
    )


# =====================================================
# DELETE LEAD
# =====================================================

@require_roles(
    "ADMIN",
    "MANAGER",
)
def lead_delete(request, pk):

    lead = get_object_or_404(
        Lead,
        pk=pk
    )

    if request.method == "POST":

        lead.delete()

        return redirect(
            "lead_list"
        )

    return render(
        request,
        "leads/delete.html",
        {
            "lead": lead,
        }
    )