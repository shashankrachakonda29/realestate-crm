import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class GeminiTemporaryUnavailable(Exception):
    """Raised when Gemini remains unavailable after retrying."""


class GeminiModelUnavailable(Exception):
    """Raised when the configured Gemini model is not available."""


EXTRACTION_PROMPT = """
You are analyzing multiple documents belonging to the SAME real-estate project/property.
Read ALL uploaded documents before producing the result.
Information can be distributed across different documents.
Combine complementary information from all documents into ONE final structured JSON object.
Do not create separate JSON objects for each document.
Do not invent missing information.
If a field is unavailable in ALL documents, return null.
If pricing appears in one document and unit information appears in another, combine them only when the documents clearly refer to the same project/unit/configuration.
Preserve values from the documents.
Do not calculate values that are not explicitly provided.
Return ONLY one valid JSON object.

Return exactly this structure:
{
  "project_name": null,
  "developer": null,
  "location": null,
  "property_type": null,
  "rera_number": null,
  "unit_configurations": [
    {
      "unit_number": null,
      "unit_type": null,
      "bhk": null,
      "plot_size_sq_yds": null,
      "plot_size_sq_ft": null,
      "facing": null,
      "saleable_area_sq_ft": null,
      "built_up_area_sq_ft": null,
      "extra_built_up_area_sq_ft": null,
      "basic_sale_price_per_sq_ft": null,
      "additional_basic_price_per_sq_ft": null,
      "amenities_charges": null,
      "facing_charges": null,
      "corner_charges": null,
      "discount": null,
      "gst_amount": null,
      "total_base_cost": null,
      "total_cost_including_gst": null,
      "possession": null,
      "available_units": null
    }
  ],
  "amenities": []
}
"""


def extract_property_from_files(file_paths):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from .env")
    if not file_paths:
        raise ValueError("At least one property file is required.")

    client = genai.Client(api_key=api_key)
    uploaded_files = [client.files.upload(file=file_path) for file_path in file_paths]
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    response = None
    last_error = None
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[*uploaded_files, EXTRACTION_PROMPT],
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            break
        except Exception as exc:
            last_error = exc
            error_text = str(exc).lower()
            status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            if status_code == 404 or "404" in error_text or "not found" in error_text:
                raise GeminiModelUnavailable(
                    f"Gemini model '{model}' is unavailable. Check GEMINI_MODEL."
                ) from exc
            transient = (
                status_code in {429, 503}
                or "429" in error_text
                or "503" in error_text
                or "unavailable" in error_text
                or "resource exhausted" in error_text
            )
            if not transient:
                raise
            if attempt == 3:
                raise GeminiTemporaryUnavailable(
                    f"Gemini model '{model}' is temporarily unavailable. "
                    "Please try again in a few minutes."
                ) from exc
            retry_after = getattr(exc, "retry_after", None)
            if retry_after is None:
                retry_after = getattr(getattr(exc, "response", None), "headers", {}).get(
                    "Retry-After"
                )
            try:
                delay = max(float(retry_after), 2 ** (attempt + 1))
            except (TypeError, ValueError):
                delay = 2 ** (attempt + 1)
            time.sleep(delay)

    if response is None:
        raise GeminiTemporaryUnavailable(
            f"Gemini model '{model}' is temporarily unavailable. "
            "Please try again in a few minutes."
        ) from last_error

    text = (getattr(response, "text", None) or "").strip()
    if not text:
        raise ValueError("Gemini returned an empty response.")
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON. Response preview: {text[:500]}") from exc
    if not isinstance(data, dict):
        raise ValueError("Gemini returned JSON, but the top-level response was not an object.")
    configurations = data.get("unit_configurations", [])
    amenities = data.get("amenities", [])
    if not isinstance(configurations, list) or not all(isinstance(item, dict) for item in configurations):
        raise ValueError("Gemini returned an invalid unit configuration list.")
    if not isinstance(amenities, list):
        raise ValueError("Gemini returned invalid amenities.")
    data["unit_configurations"] = configurations
    data["amenities"] = amenities
    return data
