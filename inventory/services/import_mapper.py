from datetime import date
from decimal import Decimal, InvalidOperation
import re


PROPERTY_TYPE_MAP = {
    "VILLA": "VILLA", "VILLAS": "VILLA", "APARTMENT": "APARTMENT",
    "APARTMENTS": "APARTMENT", "FLAT": "APARTMENT", "PLOT": "PLOT",
    "PLOTS": "PLOT", "COMMERCIAL": "COMMERCIAL", "FARM": "FARM_LAND",
    "FARM LAND": "FARM_LAND", "FARM_LAND": "FARM_LAND", "OTHER": "OTHER",
}

PREVIEW_FIELDS = (
    "unit_type", "property_type", "bhk", "plot_size_sq_yds",
    "plot_size_sq_ft", "facing", "saleable_area_sq_ft", "built_up_area_sq_ft",
    "extra_built_up_area_sq_ft", "basic_sale_price_per_sq_ft",
    "additional_basic_price_per_sq_ft", "amenities_charges", "facing_charges",
    "corner_charges", "discount", "gst_amount", "total_base_cost",
    "total_cost_including_gst", "possession", "available_units",
)

INVENTORY_MATCH_FIELDS = (
    "property_type", "bhk", "plot_size_sq_yards", "plot_size_sq_ft",
    "facing", "saleable_area_sq_ft", "built_up_area_sq_ft",
    "extra_built_up_area_sq_ft",
)

JSON_UNMAPPED_FIELDS = {
    "unit_number": "Inventory no longer has a unit_number field.",
    "unit_type": "No direct Inventory field; used to infer property_type.",
    "additional_basic_price_per_sq_ft": "Inventory has no matching field.",
    "corner_charges": "Inventory has no corner_charges field.",
    "project_name": "Project metadata; matched automatically by project name.",
    "developer": "Project metadata; not an Inventory field.",
    "location": "Project metadata; not an Inventory field.",
}

DECIMAL_JSON_FIELDS = {
    "plot_size_sq_yds", "plot_size_sq_ft", "saleable_area_sq_ft",
    "built_up_area_sq_ft", "extra_built_up_area_sq_ft",
    "basic_sale_price_per_sq_ft", "amenities_charges", "facing_charges",
    "discount", "gst_amount", "total_base_cost", "total_cost_including_gst",
}


def text_value(value):
    return "" if value is None else str(value).strip()


def decimal_value(value):
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    cleaned = str(value).replace(",", "").replace("₹", "")
    match = re.search(r"\(\s*(-?\d+(?:\.\d+)?)\s*\)", cleaned)
    if not match:
        match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return Decimal(match.group(1) if match.lastindex else match.group())
    except InvalidOperation:
        return None


def integer_value(value):
    number = decimal_value(value)
    return int(number) if number is not None and number == number.to_integral_value() else None


def normalize_property_type(value):
    normalized = text_value(value).upper().replace("-", " ")
    return PROPERTY_TYPE_MAP.get(normalized, "OTHER") if normalized else ""


def date_value(value):
    try:
        return date.fromisoformat(text_value(value)) if text_value(value) else None
    except ValueError:
        return None


def configuration_to_inventory(config, document_data, filename):
    amenities = document_data.get("amenities", [])
    amenities = ", ".join(text_value(item) for item in amenities) if isinstance(amenities, list) else text_value(amenities)
    return {
        "property_type": normalize_property_type(config.get("property_type") or config.get("unit_type") or document_data.get("property_type")),
        "bhk": integer_value(config.get("bhk")),
        "plot_size_sq_yards": decimal_value(config.get("plot_size_sq_yds")),
        "plot_size_sq_ft": decimal_value(config.get("plot_size_sq_ft")),
        "facing": text_value(config.get("facing")),
        "saleable_area_sq_ft": decimal_value(config.get("saleable_area_sq_ft")),
        "built_up_area_sq_ft": decimal_value(config.get("built_up_area_sq_ft")),
        "extra_built_up_area_sq_ft": decimal_value(config.get("extra_built_up_area_sq_ft")),
        "basic_sale_price_per_sq_ft": decimal_value(config.get("basic_sale_price_per_sq_ft")),
        "basic_sale_price": decimal_value(config.get("total_base_cost")),
        "amenities_charges": decimal_value(config.get("amenities_charges")),
        "facing_charges": decimal_value(config.get("facing_charges")),
        "discount": decimal_value(config.get("discount")),
        "gst_amount": decimal_value(config.get("gst_amount")),
        "total_unit_cost": decimal_value(config.get("total_cost_including_gst")),
        "possession_date": date_value(config.get("possession")),
        "available_units": integer_value(config.get("available_units")),
        "rera_number": text_value(document_data.get("rera_number")),
        "amenities": amenities,
        "source": filename,
    }


def inventory_configuration_signature(values):
    """Return normalized identity values for an inventory configuration."""
    signature = []
    for field in INVENTORY_MATCH_FIELDS:
        value = values.get(field) if isinstance(values, dict) else getattr(values, field)
        if isinstance(value, str):
            value = value.strip().upper()
        elif isinstance(value, Decimal):
            value = value.normalize()
        signature.append(value)
    return tuple(signature)


def inventory_configuration_matches(existing, incoming):
    """Match only identity fields supplied by the incoming configuration."""
    compared = False
    compared_identity_fields = 0
    for field in INVENTORY_MATCH_FIELDS:
        incoming_value = incoming.get(field) if isinstance(incoming, dict) else getattr(incoming, field)
        if incoming_value in (None, ""):
            continue
        existing_value = getattr(existing, field) if not isinstance(existing, dict) else existing.get(field)
        if isinstance(incoming_value, str):
            incoming_value = incoming_value.strip().upper()
        if isinstance(existing_value, str):
            existing_value = existing_value.strip().upper()
        elif isinstance(existing_value, Decimal):
            existing_value = existing_value.normalize()
        if isinstance(incoming_value, Decimal):
            incoming_value = incoming_value.normalize()
        compared = True
        compared_identity_fields += 1
        if existing_value != incoming_value:
            return False
    return compared and compared_identity_fields >= 2


def non_empty_inventory_values(values):
    """Keep only incoming model values that should be written during an update."""
    return {
        field: value
        for field, value in values.items()
        if value not in (None, "")
    }


def mapping_warnings(configurations):
    warnings = []
    if any(text_value(item.get("corner_charges")) for item in configurations):
        warnings.append("Corner Charges: Extracted but not stored. Reason: Inventory model has no corner_charges field.")
    if any(text_value(item.get("additional_basic_price_per_sq_ft")) for item in configurations):
        warnings.append("Additional basic price per sq ft was extracted, but Inventory has no matching field; it will not be saved.")
    return warnings


def json_field_report(data):
    configurations = data.get("unit_configurations", [])
    mapped = {
        field
        for configuration in configurations
        for field in configuration
        if field in PREVIEW_FIELDS
    }
    missing = [field for field in PREVIEW_FIELDS if not any(text_value(item.get(field)) for item in configurations)]
    unmapped = dict(JSON_UNMAPPED_FIELDS)
    invalid = []
    for index, configuration in enumerate(configurations, start=1):
        if configuration.get("bhk") not in (None, "") and integer_value(configuration.get("bhk")) is None:
            invalid.append(f"Configuration {index}: bhk must be a whole number.")
        for field in DECIMAL_JSON_FIELDS:
            if configuration.get(field) not in (None, "") and decimal_value(configuration.get(field)) is None:
                invalid.append(f"Configuration {index}: {field} is not a valid number.")
        if configuration.get("possession") not in (None, "") and date_value(configuration.get("possession")) is None:
            invalid.append(f"Configuration {index}: possession must use YYYY-MM-DD.")
    return {"mapped_fields": sorted(mapped), "missing_fields": missing, "unmapped_fields": unmapped, "invalid_fields": invalid}


def validate_preview_configurations(configurations, document_data=None):
    errors = []
    document_data = document_data or {}
    for index, configuration in enumerate(configurations, start=1):
        if not normalize_property_type(
            configuration.get("property_type")
            or configuration.get("unit_type")
            or document_data.get("property_type")
        ):
            errors.append(f"Configuration {index}: property type is required.")
    return errors
