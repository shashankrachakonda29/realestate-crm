from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Project
from .models import Inventory
from decimal import Decimal, InvalidOperation


def inventory_list(request):

    search = request.GET.get("search", "").strip()
    project_id = request.GET.get("project", "").strip()
    location_id = request.GET.get("location", "").strip()
    property_type = request.GET.get("property_type", "").strip()
    status = request.GET.get("status", "").strip()
    bhk = request.GET.get("bhk", "").strip()

    inventory = (
        Inventory.objects
        .select_related(
            "project",
            "project__developer",
            "project__location",
        )
        .order_by(
            "project__name",
            "unit_number",
        )
    )

    if search:
        inventory = inventory.filter(
            unit_number__icontains=search
        )

    if project_id:
        inventory = inventory.filter(
            project_id=project_id
        )

    if location_id:
        inventory = inventory.filter(
            project__location_id=location_id
        )

    if property_type:
        inventory = inventory.filter(
            property_type=property_type
        )

    if status:
        inventory = inventory.filter(
            status=status
        )

    if bhk:
        inventory = inventory.filter(
            bhk=bhk
        )

    projects = Project.objects.filter(
        is_active=True
    ).order_by("name")

    locations = (
        Project.objects
        .filter(is_active=True)
        .select_related("location")
        .values(
            "location_id",
            "location__name",
        )
        .distinct()
        .order_by("location__name")
    )

    return render(
        request,
        "inventory/list.html",
        {
            "inventory": inventory,
            "search": search,
            "projects": projects,
            "locations": locations,
            "property_types": Inventory.PropertyType.choices,
            "statuses": Inventory.Status.choices,
            "selected_project": project_id,
            "selected_location": location_id,
            "selected_property_type": property_type,
            "selected_status": status,
            "selected_bhk": bhk,
        },
    )


def inventory_create(request):

    projects = Project.objects.filter(
        is_active=True
    ).select_related(
        "developer",
        "location",
    ).order_by("name")

    if request.method == "POST":

        def decimal_value(field_name):
            value = request.POST.get(field_name)

            if not value:
                return Decimal("0")

            try:
                return Decimal(value)
            except (InvalidOperation, TypeError, ValueError):
                return Decimal("0")

        # -------------------------------------------------
        # PRICING VALUES
        # -------------------------------------------------

        basic_sale_price = decimal_value(
            "basic_sale_price"
        )

        gst_amount = decimal_value(
            "gst_amount"
        )

        amenities_charges = decimal_value(
            "amenities_charges"
        )

        facing_charges = decimal_value(
            "facing_charges"
        )

        discount = decimal_value(
            "discount"
        )

        unit_size_sq_ft = decimal_value(
            "unit_size_sq_ft"
        )

        # -------------------------------------------------
        # SERVER-SIDE CALCULATION
        # -------------------------------------------------

        total_unit_cost = (
            basic_sale_price
            + gst_amount
            + amenities_charges
            + facing_charges
            - discount
        )

        if unit_size_sq_ft > 0:

            price_per_sq_ft_incl_gst = (
                total_unit_cost
                / unit_size_sq_ft
            )

        else:

            price_per_sq_ft_incl_gst = Decimal("0")

        # -------------------------------------------------
        # CREATE INVENTORY
        # -------------------------------------------------

        Inventory.objects.create(

            project_id=request.POST.get(
                "project"
            ),

            unit_number=request.POST.get(
                "unit_number",
                "",
            ).strip(),

            property_type=request.POST.get(
                "property_type"
            ),

            bhk=(
                request.POST.get("bhk")
                or None
            ),

            plot_size_sq_yards=(
                request.POST.get(
                    "plot_size_sq_yards"
                ) or None
            ),

            plot_size_sq_ft=(
                request.POST.get(
                    "plot_size_sq_ft"
                ) or None
            ),

            saleable_area_sq_ft=(
                request.POST.get(
                    "saleable_area_sq_ft"
                ) or None
            ),

            built_up_area_sq_ft=(
                request.POST.get(
                    "built_up_area_sq_ft"
                ) or None
            ),

            extra_built_up_area_sq_ft=(
                request.POST.get(
                    "extra_built_up_area_sq_ft"
                ) or None
            ),

            facing=request.POST.get(
                "facing",
                "",
            ).strip(),

            floors=request.POST.get(
                "floors",
                "",
            ).strip(),

            current_price=(
                request.POST.get(
                    "current_price"
                ) or None
            ),

            gst_amount=gst_amount,

            # SERVER CALCULATED
            total_unit_cost=total_unit_cost,

            discount=(
                request.POST.get(
                    "discount"
                ) or None
            ),

            booking_amount=(
                request.POST.get(
                    "booking_amount"
                ) or None
            ),

            basic_sale_price_per_sq_ft=(
                request.POST.get(
                    "basic_sale_price_per_sq_ft"
                ) or None
            ),

            basic_sale_price=basic_sale_price,

            amenities_charges=(
                request.POST.get(
                    "amenities_charges"
                ) or None
            ),

            facing_charges=(
                request.POST.get(
                    "facing_charges"
                ) or None
            ),

            # SERVER CALCULATED
            price_per_sq_ft_incl_gst=(
                price_per_sq_ft_incl_gst
            ),

            unit_size_sq_ft=(
                request.POST.get(
                    "unit_size_sq_ft"
                ) or None
            ),

            unit_facing=request.POST.get(
                "unit_facing",
                "",
            ).strip(),

            unit_price=(
                request.POST.get(
                    "unit_price"
                ) or None
            ),

            available_units=(
                request.POST.get(
                    "available_units"
                ) or None
            ),

            cp_commission_percent=(
                request.POST.get(
                    "cp_commission_percent"
                ) or None
            ),

            commission_terms=request.POST.get(
                "commission_terms",
                "",
            ).strip(),

            offer_valid_till=(
                request.POST.get(
                    "offer_valid_till"
                ) or None
            ),

            source=request.POST.get(
                "source",
                "",
            ).strip(),

            date_received=(
                request.POST.get(
                    "date_received"
                ) or None
            ),

            payment_plan=request.POST.get(
                "payment_plan",
                "",
            ).strip(),

            possession_date=(
                request.POST.get(
                    "possession_date"
                ) or None
            ),

            rera_number=request.POST.get(
                "rera_number",
                "",
            ).strip(),

            amenities=request.POST.get(
                "amenities",
                "",
            ).strip(),

            status=request.POST.get(
                "status"
            ),

            notes=request.POST.get(
                "notes",
                "",
            ).strip(),

            brochure_url=request.POST.get(
                "brochure_url",
                "",
            ).strip(),

            price_sheet_url=request.POST.get(
                "price_sheet_url",
                "",
            ).strip(),

            inventory_sheet_url=request.POST.get(
                "inventory_sheet_url",
                "",
            ).strip(),

            website_url=request.POST.get(
                "website_url",
                "",
            ).strip(),

            google_maps_url=request.POST.get(
                "google_maps_url",
                "",
            ).strip(),
        )

        return redirect(
            "inventory_list"
        )

    return render(
        request,
        "inventory/form.html",
        {
            "title": "Add Inventory",
            "inventory_item": None,
            "projects": projects,
            "property_types": Inventory.PropertyType.choices,
            "statuses": Inventory.Status.choices,
        },
    )

def inventory_detail(request, pk):

    inventory_item = get_object_or_404(
        Inventory.objects.select_related(
            "project",
            "project__developer",
            "project__location",
        ),
        pk=pk,
    )

    return render(
        request,
        "inventory/detail.html",
        {
            "inventory_item": inventory_item,
        },
    )


def inventory_edit(request, pk):

    inventory_item = get_object_or_404(
        Inventory,
        pk=pk,
    )

    projects = Project.objects.filter(
        is_active=True
    ).select_related(
        "developer",
        "location",
    ).order_by("name")

    if request.method == "POST":

        # -------------------------------------------------
        # DECIMAL HELPER
        # -------------------------------------------------

        def decimal_value(field_name):
            value = request.POST.get(field_name)

            if not value:
                return Decimal("0")

            try:
                return Decimal(value)
            except (InvalidOperation, TypeError, ValueError):
                return Decimal("0")

        # -------------------------------------------------
        # PRICING VALUES
        # -------------------------------------------------

        basic_sale_price = decimal_value(
            "basic_sale_price"
        )

        gst_amount = decimal_value(
            "gst_amount"
        )

        amenities_charges = decimal_value(
            "amenities_charges"
        )

        facing_charges = decimal_value(
            "facing_charges"
        )

        discount = decimal_value(
            "discount"
        )

        unit_size_sq_ft = decimal_value(
            "unit_size_sq_ft"
        )

        # -------------------------------------------------
        # SERVER-SIDE CALCULATION
        # -------------------------------------------------

        total_unit_cost = (
            basic_sale_price
            + gst_amount
            + amenities_charges
            + facing_charges
            - discount
        )

        if unit_size_sq_ft > 0:
            price_per_sq_ft_incl_gst = (
                total_unit_cost / unit_size_sq_ft
            )
        else:
            price_per_sq_ft_incl_gst = Decimal("0")

        # -------------------------------------------------
        # UPDATE INVENTORY
        # -------------------------------------------------

        inventory_item.project_id = request.POST.get(
            "project"
        )

        inventory_item.unit_number = request.POST.get(
            "unit_number",
            "",
        ).strip()

        inventory_item.property_type = request.POST.get(
            "property_type"
        )

        inventory_item.bhk = (
            request.POST.get("bhk")
            or None
        )

        inventory_item.plot_size_sq_yards = (
            request.POST.get(
                "plot_size_sq_yards"
            ) or None
        )

        inventory_item.plot_size_sq_ft = (
            request.POST.get(
                "plot_size_sq_ft"
            ) or None
        )

        inventory_item.saleable_area_sq_ft = (
            request.POST.get(
                "saleable_area_sq_ft"
            ) or None
        )

        inventory_item.built_up_area_sq_ft = (
            request.POST.get(
                "built_up_area_sq_ft"
            ) or None
        )

        inventory_item.extra_built_up_area_sq_ft = (
            request.POST.get(
                "extra_built_up_area_sq_ft"
            ) or None
        )

        inventory_item.facing = request.POST.get(
            "facing",
            "",
        ).strip()

        inventory_item.floors = request.POST.get(
            "floors",
            "",
        ).strip()

        inventory_item.current_price = (
            request.POST.get(
                "current_price"
            ) or None
        )

        # -------------------------------------------------
        # PRICING
        # -------------------------------------------------

        inventory_item.basic_sale_price = (
            basic_sale_price
        )

        inventory_item.gst_amount = (
            gst_amount
        )

        inventory_item.amenities_charges = (
            amenities_charges
        )

        inventory_item.facing_charges = (
            facing_charges
        )

        inventory_item.discount = (
            discount
        )

        inventory_item.unit_size_sq_ft = (
            unit_size_sq_ft
            if unit_size_sq_ft > 0
            else None
        )

        # SERVER-CALCULATED
        inventory_item.total_unit_cost = (
            total_unit_cost
        )

        # SERVER-CALCULATED
        inventory_item.price_per_sq_ft_incl_gst = (
            price_per_sq_ft_incl_gst
        )

        # -------------------------------------------------
        # OTHER FIELDS
        # -------------------------------------------------

        inventory_item.booking_amount = (
            request.POST.get(
                "booking_amount"
            ) or None
        )

        inventory_item.basic_sale_price_per_sq_ft = (
            request.POST.get(
                "basic_sale_price_per_sq_ft"
            ) or None
        )

        inventory_item.unit_facing = request.POST.get(
            "unit_facing",
            "",
        ).strip()

        inventory_item.unit_price = (
            request.POST.get(
                "unit_price"
            ) or None
        )

        inventory_item.available_units = (
            request.POST.get(
                "available_units"
            ) or None
        )

        inventory_item.cp_commission_percent = (
            request.POST.get(
                "cp_commission_percent"
            ) or None
        )

        inventory_item.commission_terms = request.POST.get(
            "commission_terms",
            "",
        ).strip()

        inventory_item.offer_valid_till = (
            request.POST.get(
                "offer_valid_till"
            ) or None
        )

        inventory_item.source = request.POST.get(
            "source",
            "",
        ).strip()

        inventory_item.date_received = (
            request.POST.get(
                "date_received"
            ) or None
        )

        inventory_item.payment_plan = request.POST.get(
            "payment_plan",
            "",
        ).strip()

        inventory_item.possession_date = (
            request.POST.get(
                "possession_date"
            ) or None
        )

        inventory_item.rera_number = request.POST.get(
            "rera_number",
            "",
        ).strip()

        inventory_item.amenities = request.POST.get(
            "amenities",
            "",
        ).strip()

        inventory_item.status = request.POST.get(
            "status"
        )

        inventory_item.notes = request.POST.get(
            "notes",
            "",
        ).strip()

        inventory_item.brochure_url = request.POST.get(
            "brochure_url",
            "",
        ).strip()

        inventory_item.price_sheet_url = request.POST.get(
            "price_sheet_url",
            "",
        ).strip()

        inventory_item.inventory_sheet_url = request.POST.get(
            "inventory_sheet_url",
            "",
        ).strip()

        inventory_item.website_url = request.POST.get(
            "website_url",
            "",
        ).strip()

        inventory_item.google_maps_url = request.POST.get(
            "google_maps_url",
            "",
        ).strip()

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        inventory_item.save()

        return redirect(
            "inventory_detail",
            pk=inventory_item.pk,
        )

    return render(
        request,
        "inventory/form.html",
        {
            "title": "Edit Inventory",
            "inventory_item": inventory_item,
            "projects": projects,
            "property_types": Inventory.PropertyType.choices,
            "statuses": Inventory.Status.choices,
        },
    )

def inventory_delete(request, pk):

    inventory_item = get_object_or_404(
        Inventory,
        pk=pk,
    )

    if request.method == "POST":

        inventory_item.delete()

        return redirect(
            "inventory_list"
        )

    return render(
        request,
        "inventory/detail.html",
        {
            "inventory_item": inventory_item,
            "confirm_delete": True,
        },
    )