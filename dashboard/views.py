from django.shortcuts import render

from developers.models import Developer
from projects.models import Project
from inventory.models import Inventory
from leads.models import Lead


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
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )