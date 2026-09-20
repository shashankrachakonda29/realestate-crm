from django.contrib.auth import get_user_model
from django.db.models import Q,Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LeadForm, LeadActivityForm
from .models import Lead,LeadActivity
from django.utils import timezone
from accounts.decorators import role_required

User = get_user_model()
# ==========================================
# Pipeline
# =========================================
def lead_pipeline(request):
    leads = Lead.objects.all()

    if request.user.role == User.Role.SALES:

        leads = leads.filter(
            assigned_to=request.user
        )

    # Total leads
    total_leads = Lead.objects.count()

    # Status-wise counts
    status_counts = {
        "new": Lead.objects.filter(
            status=Lead.Status.NEW
        ).count(),

        "contacted": Lead.objects.filter(
            status=Lead.Status.CONTACTED
        ).count(),

        "interested": Lead.objects.filter(
            status=Lead.Status.INTERESTED
        ).count(),

        "site_visit": Lead.objects.filter(
            status=Lead.Status.SITE_VISIT
        ).count(),

        "negotiation": Lead.objects.filter(
            status=Lead.Status.NEGOTIATION
        ).count(),

        "booked": Lead.objects.filter(
            status=Lead.Status.BOOKED
        ).count(),

        "lost": Lead.objects.filter(
            status=Lead.Status.LOST
        ).count(),

        "on_hold": Lead.objects.filter(
            status=Lead.Status.ON_HOLD
        ).count(),
    }

    # Today's follow-ups
    today = timezone.localdate()

    today_followups = Lead.objects.filter(
        next_follow_up__date=today
    ).select_related(
        "assigned_to",
        "interested_project",
    ).order_by(
        "next_follow_up"
    )

    # Overdue follow-ups
    overdue_followups = Lead.objects.filter(
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

    # Upcoming follow-ups
    upcoming_followups = Lead.objects.filter(
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



def lead_list(request):

    leads = Lead.objects.select_related(
        "assigned_to",
        "interested_project",
    ).order_by("-created_at")
    if request.user.role == User.Role.SALES:

        leads = leads.filter(
            assigned_to=request.user
        )

    search = request.GET.get("search", "").strip()
    selected_status = request.GET.get("status", "")
    selected_source = request.GET.get("source", "")
    selected_property_type = request.GET.get(
        "preferred_property_type",
        "",
    )
    selected_assigned_to = request.GET.get(
        "assigned_to",
        "",
    )

    # =========================================
    # SEARCH
    # =========================================

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

    # =========================================
    # STATUS FILTER
    # =========================================

    if selected_status:
        leads = leads.filter(
            status=selected_status
        )

    # =========================================
    # SOURCE FILTER
    # =========================================

    if selected_source:
        leads = leads.filter(
            source=selected_source
        )

    # =========================================
    # PROPERTY TYPE FILTER
    # =========================================

    if selected_property_type:
        leads = leads.filter(
            preferred_property_type__iexact=selected_property_type
        )

    # =========================================
    # ASSIGNED USER FILTER
    # =========================================

    if selected_assigned_to:
        leads = leads.filter(
            assigned_to_id=selected_assigned_to
        )

    # =========================================
    # USERS
    # =========================================

    users = User.objects.filter(
        is_active=True
    ).order_by(
        "first_name",
        "username",
    )

    # =========================================
    # CONTEXT
    # =========================================
    lead_status_counts = {
    "total": Lead.objects.count(),

    "new": Lead.objects.filter(
        status=Lead.Status.NEW
    ).count(),

    "contacted": Lead.objects.filter(
        status=Lead.Status.CONTACTED
    ).count(),

    "interested": Lead.objects.filter(
        status=Lead.Status.INTERESTED
    ).count(),

    "site_visit": Lead.objects.filter(
        status=Lead.Status.SITE_VISIT
    ).count(),

    "negotiation": Lead.objects.filter(
        status=Lead.Status.NEGOTIATION
    ).count(),

    "booked": Lead.objects.filter(
        status=Lead.Status.BOOKED
    ).count(),

    "on_hold": Lead.objects.filter(
        status=Lead.Status.ON_HOLD
    ).count(),

    "lost": Lead.objects.filter(
        status=Lead.Status.LOST
    ).count(),
}
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
        context,
    )
# =====================================================
# CREATE
# =====================================================
@role_required("ADMIN", "MANAGER", "SALES")
def lead_create(request):

    if request.method == "POST":

        form = LeadForm(request.POST)

        if form.is_valid():

            lead = form.save(commit=False)

            if not can_assign_leads(request.user):
                lead.assigned_to = None

            lead.save()

            return redirect(
                "lead_detail",
                pk=lead.pk
            )

    else:

        form = LeadForm()

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

def lead_detail(request, pk):

    lead = get_object_or_404(
        Lead.objects.select_related(
            "assigned_to",
            "interested_project",
        ),
        pk=pk
    )

    activities = lead.activities.select_related(
        "created_by"
    ).order_by(
        "-activity_date",
        "-created_at",
    )

    activity_form = LeadActivityForm(
        initial={
            "activity_date": timezone.localtime().strftime(
                "%Y-%m-%dT%H:%M"
            )
        }
    )

    return render(
        request,
        "leads/detail.html",
        {
            "lead": lead,
            "activities": activities,
            "activity_form": activity_form,
        }
    )

@role_required("ADMIN", "MANAGER", "SALES")
def lead_status_update(request, pk):

    lead = get_object_or_404(
        Lead,
        pk=pk
    )

    if request.method == "POST":

        status = request.POST.get("status")

        valid_statuses = {
            value
            for value, label in Lead.Status.choices
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
@role_required("ADMIN", "MANAGER", "SALES")
def lead_activity_create(request, pk):

    lead = get_object_or_404(
        Lead,
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
@role_required("ADMIN", "MANAGER", "SALES")
def lead_edit(request, pk):

    lead = get_object_or_404(
        Lead,
        pk=pk
    )

    if request.method == "POST":

        form = LeadForm(
            request.POST,
            instance=lead
        )

        if form.is_valid():

            updated_lead = form.save(
                commit=False
            )

            if not can_assign_leads(request.user):

                updated_lead.assigned_to = lead.assigned_to

            updated_lead.save()

            return redirect(
                "lead_detail",
                pk=lead.pk
            )

    else:

        form = LeadForm(
            instance=lead
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
@role_required("ADMIN", "MANAGER", "SALES")
def lead_activity_edit(request, pk, activity_id):

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

@role_required("ADMIN", "MANAGER")
def lead_activity_delete(request, pk, activity_id):

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
# DELETE
# =====================================================
@role_required("ADMIN", "MANAGER")
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

def can_assign_leads(user):
    return (
        user.is_authenticated
        and user.role in [
            User.Role.ADMIN,
            User.Role.MANAGER,
        ]
    )