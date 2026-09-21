from django.shortcuts import render
from django.utils import timezone

from developers.models import Developer
from projects.models import Project
from inventory.models import Inventory
from leads.models import Lead
from sitevisits.models import SiteVisit
from django.contrib.auth import get_user_model

User = get_user_model()
def dashboard(request):

    total_developers = Developer.objects.filter(
        is_active=True
    ).count()

    total_projects = Project.objects.filter(
        is_active=True
    ).count()

    total_inventory = Inventory.objects.count()

    available_inventory = Inventory.objects.filter(
        status=Inventory.Status.AVAILABLE
    ).count()

    blocked_inventory = Inventory.objects.filter(
        status=Inventory.Status.BLOCKED
    ).count()

    booked_inventory = Inventory.objects.filter(
        status=Inventory.Status.BOOKED
    ).count()

    sold_inventory = Inventory.objects.filter(
        status=Inventory.Status.SOLD
    ).count()

    on_hold_inventory = Inventory.objects.filter(
        status=Inventory.Status.ON_HOLD
    ).count()


    # =====================================================
    # LEADS
    # =====================================================

    lead_stats = {
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

        "lost": Lead.objects.filter(
            status=Lead.Status.LOST
        ).count(),

        "on_hold": Lead.objects.filter(
            status=Lead.Status.ON_HOLD
        ).count(),
    }


    # =====================================================
    # SITE VISITS
    # =====================================================

    today = timezone.localdate()

    total_site_visits = SiteVisit.objects.count()

    scheduled_site_visits = SiteVisit.objects.filter(
        status=SiteVisit.Status.SCHEDULED
    ).count()

    confirmed_site_visits = SiteVisit.objects.filter(
        status=SiteVisit.Status.CONFIRMED
    ).count()

    completed_site_visits = SiteVisit.objects.filter(
        status=SiteVisit.Status.COMPLETED
    ).count()

    cancelled_site_visits = SiteVisit.objects.filter(
        status=SiteVisit.Status.CANCELLED
    ).count()

    no_show_site_visits = SiteVisit.objects.filter(
        status=SiteVisit.Status.NO_SHOW
    ).count()

    rescheduled_site_visits = SiteVisit.objects.filter(
        status=SiteVisit.Status.RESCHEDULED
    ).count()

    todays_site_visits = SiteVisit.objects.filter(
        visit_date=today
    ).select_related(
        "lead",
        "project",
        "assigned_to",
    ).order_by(
        "visit_time"
    )


    upcoming_site_visits = SiteVisit.objects.filter(
        visit_date__gte=today
    ).exclude(
        status__in=[
            SiteVisit.Status.CANCELLED,
            SiteVisit.Status.COMPLETED,
        ]
    ).select_related(
        "lead",
        "project",
        "assigned_to",
    ).order_by(
        "visit_date",
        "visit_time",
    )[:5]


    # =====================================================
    # TODAY'S FOLLOW UPS
    # =====================================================

    todays_followups = Lead.objects.filter(
        next_follow_up__date=today
    ).select_related(
        "assigned_to",
        "interested_project",
    ).order_by(
        "next_follow_up"
    )

    # =====================================================
# SALES TEAM STATISTICS
# =====================================================

    sales_users = User.objects.filter(
        is_active=True,
        role="SALES",
    ).order_by(
        "first_name",
        "username",
    )

    sales_team_stats = []

    for user in sales_users:

        assigned_leads = Lead.objects.filter(
            assigned_to=user
        )

        assigned_site_visits = SiteVisit.objects.filter(
            assigned_to=user
        )

        sales_team_stats.append({
            "user": user,

            "total_leads": assigned_leads.count(),

            "new_leads": assigned_leads.filter(
                status=Lead.Status.NEW
            ).count(),

            "interested_leads": assigned_leads.filter(
                status=Lead.Status.INTERESTED
            ).count(),

            "site_visit_leads": assigned_leads.filter(
                status=Lead.Status.SITE_VISIT
            ).count(),

            "booked_leads": assigned_leads.filter(
                status=Lead.Status.BOOKED
            ).count(),

            "total_site_visits": assigned_site_visits.count(),

            "upcoming_site_visits": assigned_site_visits.filter(
                visit_date__gte=today
            ).exclude(
                status__in=[
                    SiteVisit.Status.CANCELLED,
                    SiteVisit.Status.COMPLETED,
                ]
            ).count(),

            "followups": assigned_leads.filter(
                next_follow_up__date=today
            ).count(),
        })

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "total_developers": total_developers,
        "total_projects": total_projects,
        "total_inventory": total_inventory,

        "available_inventory": available_inventory,
        "blocked_inventory": blocked_inventory,
        "booked_inventory": booked_inventory,
        "sold_inventory": sold_inventory,
        "on_hold_inventory": on_hold_inventory,

        "lead_stats": lead_stats,

        "total_site_visits": total_site_visits,
        "scheduled_site_visits": scheduled_site_visits,
        "confirmed_site_visits": confirmed_site_visits,
        "completed_site_visits": completed_site_visits,
        "cancelled_site_visits": cancelled_site_visits,
        "no_show_site_visits": no_show_site_visits,
        "rescheduled_site_visits": rescheduled_site_visits,

        "todays_site_visits": todays_site_visits,
        "upcoming_site_visits": upcoming_site_visits,

        "todays_followups": todays_followups,

        "sales_team_stats": sales_team_stats,
    }


    return render(
        request,
        "dashboard/dashboard.html",
        context
    )