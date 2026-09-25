import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from projects.models import Project
from leads.models import Lead

try:
    import pandas as pd
except ImportError:
    pd = None


FIELD_DEFINITIONS = [
    ("name", "Name", True),
    ("phone", "Phone", True),
    ("email", "Email", False),
    ("interested_project", "Project", False),
    ("budget_min", "Budget Min", False),
    ("budget_max", "Budget Max", False),
    ("preferred_location", "Location", False),
    ("preferred_property_type", "Property Type", False),
    ("bhk", "BHK", False),
    ("requirement", "Requirement", False),
    ("notes", "Notes", False),
    ("next_follow_up", "Next Follow Up", False),
    ("source", "Source", False),
    ("status", "Status", False),
    ("assigned_to", "Assigned To", False),
]

ALIASES = {
    "name": ["name", "full name", "customer name", "lead name", "client name"],
    "phone": ["phone", "mobile", "mobile number", "phone number", "contact number"],
    "email": ["email", "email id", "email address"],
    "interested_project": ["project", "project name", "interested project", "interested project name"],
    "budget_min": ["budget min", "minimum budget", "min budget", "budget from"],
    "budget_max": ["budget max", "maximum budget", "max budget", "budget to"],
    "preferred_location": ["location", "preferred location", "area", "preferred area"],
    "preferred_property_type": ["property type", "preferred property type", "property", "type"],
    "bhk": ["bhk", "bedrooms", "bedroom", "no of bedrooms"],
    "requirement": ["requirement", "requirements", "customer requirement"],
    "notes": ["notes", "remarks", "comments"],
    "next_follow_up": ["next follow up", "follow up", "follow up date", "next follow up date"],
    "source": ["source", "lead source"],
    "status": ["status", "lead status"],
    "assigned_to": ["assigned to", "assigned user", "sales person", "sales executive", "agent"],
}

SOURCE_VALUES = {
    "meta ads": "META_ADS", "facebook ads": "META_ADS", "google ads": "GOOGLE_ADS",
    "google": "GOOGLE_ADS", "website": "WEBSITE", "instagram": "INSTAGRAM",
    "facebook": "FACEBOOK", "whatsapp": "WHATSAPP", "referral": "REFERRAL",
    "walk in": "WALK_IN", "walk-in": "WALK_IN", "call": "CALL",
}
STATUS_VALUES = {
    "new": "NEW", "contacted": "CONTACTED", "interested": "INTERESTED",
    "site visit": "SITE_VISIT", "site visit done": "SITE_VISIT",
    "negotiation": "NEGOTIATION", "booked": "BOOKED", "lost": "LOST", "on hold": "ON_HOLD",
}


def normalize_column_name(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def detect_column_mapping(columns):
    normalized = {}
    for column in columns:
        normalized.setdefault(normalize_column_name(column), []).append(column)
    mapping = {}
    for field, aliases in ALIASES.items():
        matches = [normalized[normalize_column_name(alias)][0] for alias in aliases
                   if normalize_column_name(alias) in normalized
                   and len(normalized[normalize_column_name(alias)]) == 1]
        if len(matches) == 1:
            mapping[field] = matches[0]
    return mapping


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def normalize_phone(value):
    text = _text(value)
    if not text:
        return ""
    digits = re.sub(r"\D", "", text)
    if text.lstrip().startswith("00") and digits.startswith("00"):
        digits = digits[2:]
    return digits


def normalize_source(value):
    return SOURCE_VALUES.get(normalize_column_name(value), "OTHER")


def normalize_status(value):
    return STATUS_VALUES.get(normalize_column_name(value), "NEW")


def parse_budget(value):
    text = _text(value).lower().replace(",", "").replace("₹", "").strip()
    if not text:
        return None
    multiplier = Decimal("1")
    if re.search(r"\b(lakh|lakhs)\b", text):
        multiplier = Decimal("100000")
    elif re.search(r"\b(cr|crore|crores)\b", text):
        multiplier = Decimal("10000000")
    text = re.sub(r"[^0-9.\-]", "", text)
    if not text:
        raise ValueError("Invalid Budget")
    try:
        return Decimal(text) * multiplier
    except InvalidOperation as exc:
        raise ValueError("Invalid Budget") from exc


def parse_bhk(value):
    text = _text(value)
    if not text:
        return None
    match = re.search(r"\d+", text)
    if not match:
        raise ValueError("Invalid BHK")
    number = int(match.group())
    if number < 1 or number > 20:
        raise ValueError("Invalid BHK")
    return number


def parse_follow_up(value):
    text = _text(value)
    if not text:
        return None
    for date_format in (
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
        "%d %b %Y", "%d %B %Y", "%Y-%m-%d %H:%M:%S",
    ):
        try:
            parsed = datetime.strptime(text, date_format)
            return timezone.make_aware(parsed)
        except ValueError:
            continue
    raise ValueError("Invalid Date")


def _normalized_text(value):
    return " ".join(_text(value).casefold().split())


def match_project(value):
    normalized = _normalized_text(value)
    if not normalized:
        return None
    for project in Project.objects.all().only("id", "name"):
        if _normalized_text(project.name) == normalized:
            return project
    return None


def match_user(value):
    normalized = _normalized_text(value)
    if not normalized:
        return None
    matches = []
    for user in User.objects.filter(is_active=True).only("id", "username", "email", "first_name", "last_name"):
        full_name = _normalized_text(f"{user.first_name} {user.last_name}")
        if normalized in {_normalized_text(user.username), _normalized_text(user.email), full_name}:
            matches.append(user)
    return matches[0] if len(matches) == 1 else None


def _read_csv(uploaded_file):
    content = uploaded_file.read().decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        return [], []
    columns = [str(column).strip() for column in reader.fieldnames]
    rows = [{column: _text(row.get(column)) for column in columns} for row in reader]
    return columns, rows


def read_lead_file(uploaded_file):
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        return _read_csv(uploaded_file)
    if pd is None:
        raise ValueError("Pandas is required for XLSX/XLS files. Run: venv\\Scripts\\pip install pandas openpyxl xlrd")
    try:
        dataframe = pd.read_excel(uploaded_file)
    except ImportError as exc:
        raise ValueError("XLS support requires xlrd. Run: venv\\Scripts\\pip install xlrd") from exc
    except Exception as exc:
        raise ValueError(f"Unable to read spreadsheet: {exc}") from exc
    columns = [str(column).strip() for column in dataframe.columns]
    rows = []
    for _, row in dataframe.iterrows():
        rows.append({column: "" if pd.isna(row[column]) else _text(row[column]) for column in columns})
    return columns, rows


def _row_result(row_number, name, phone, result, reason):
    return {"row": row_number, "name": name, "phone": phone, "result": result, "reason": reason}


def import_leads(rows, mapping):
    existing_phones = {normalize_phone(phone) for phone in Lead.objects.values_list("phone", flat=True)}
    file_phones = set()
    details = []
    imported = skipped_duplicates = validation_errors = project_warnings = user_warnings = 0

    for index, raw_row in enumerate(rows, start=2):
        def value(field):
            column = mapping.get(field)
            return _text(raw_row.get(column)) if column else ""

        name = value("name")
        phone = normalize_phone(value("phone"))
        if not name:
            validation_errors += 1
            details.append(_row_result(index, name, phone, "Error - Missing Name", "Name is required."))
            continue
        if not phone:
            validation_errors += 1
            details.append(_row_result(index, name, phone, "Error - Missing Phone", "Phone is required."))
            continue
        if phone in existing_phones:
            skipped_duplicates += 1
            details.append(_row_result(index, name, phone, "Skipped - Duplicate Phone", "A Lead with this phone already exists."))
            continue
        if phone in file_phones:
            skipped_duplicates += 1
            details.append(_row_result(index, name, phone, "Skipped - Duplicate in File", "This phone appears earlier in the uploaded file."))
            continue

        data = {"name": name, "phone": phone}
        errors = []
        email = value("email")
        if email:
            try:
                validate_email(email)
                data["email"] = email
            except ValidationError:
                errors.append("Invalid Email")
        for field in ("budget_min", "budget_max"):
            try:
                data[field] = parse_budget(value(field))
            except ValueError:
                errors.append("Invalid Budget")
        try:
            data["bhk"] = parse_bhk(value("bhk"))
        except ValueError:
            errors.append("Invalid BHK")
        try:
            data["next_follow_up"] = parse_follow_up(value("next_follow_up"))
        except ValueError:
            errors.append("Invalid Date")
        if errors:
            validation_errors += 1
            details.append(_row_result(index, name, phone, f"Error - {errors[0]}", "; ".join(errors)))
            continue

        data.update({
            "preferred_location": value("preferred_location"),
            "preferred_property_type": value("preferred_property_type"),
            "requirement": value("requirement"),
            "notes": value("notes"),
            "source": normalize_source(value("source")),
            "status": normalize_status(value("status")),
        })
        project = match_project(value("interested_project"))
        assigned_user = match_user(value("assigned_to"))
        project_warning = bool(value("interested_project") and not project)
        user_warning = bool(value("assigned_to") and not assigned_user)
        data["interested_project"] = project
        data["assigned_to"] = assigned_user

        with transaction.atomic():
            Lead.objects.create(**data)
        file_phones.add(phone)
        imported += 1
        if project_warning:
            project_warnings += 1
        if user_warning:
            user_warnings += 1
        reasons = []
        if project_warning:
            reasons.append("Project Not Matched")
        if user_warning:
            reasons.append("Assigned User Not Found")
        result = "Imported" if not reasons else "Imported - " + ", ".join(reasons)
        details.append(_row_result(index, name, phone, result, "; ".join(reasons)))

    return {
        "total_rows": len(rows),
        "imported_count": imported,
        "skipped_duplicates": skipped_duplicates,
        "validation_errors": validation_errors,
        "project_warnings": project_warnings,
        "user_warnings": user_warnings,
        "details": details,
    }
