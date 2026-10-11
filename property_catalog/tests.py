import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from property_catalog.models import PropertyCatalog


class PropertyCatalogFlowTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="catalog-admin",
            email="admin@example.com",
            password="secret123",
        )
        self.client.force_login(self.user)

    def test_dashboard_lists_imported_catalogs(self):
        PropertyCatalog.objects.create(name="Alpha Catalog", version="2.0")

        response = self.client.get("/property-catalog/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Catalog")

    def test_import_page_renders_upload_form(self):
        response = self.client.get("/property-catalog/import/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Validate")
        self.assertContains(response, 'name="json_file"')

    def test_valid_import_creates_catalog_after_preview_confirmation(self):
        payload = {
            "catalog_name": "Demo Catalog",
            "version": "1.0",
            "developers": [
                {
                    "name": "Apex Developers",
                    "projects": [
                        {
                            "name": "Sunrise Residency",
                            "project_type": "APARTMENT",
                            "project_details": {
                                "status": "Ongoing",
                                "total_units": 80,
                                "starting_price": "1000000",
                            },
                            "location": {
                                "locality": "MG Road",
                                "city": "Bengaluru",
                                "state": "Karnataka",
                                "pincode": "560001",
                            },
                            "highlights": ["Clubhouse", "Green view"],
                            "amenities": ["Pool", "Gym"],
                            "configurations": [
                                {
                                    "property_type": "APARTMENT",
                                    "type_name": "2 BHK",
                                    "bhk": "2",
                                    "bedrooms": 2,
                                    "bathrooms": 2,
                                    "built_up_area_sq_ft": "1200",
                                    "basic_price": "6500000",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        uploaded = SimpleUploadedFile(
            "catalog.json",
            json.dumps(payload).encode("utf-8"),
            content_type="application/json",
        )

        response = self.client.post(
            "/property-catalog/import/",
            {"json_file": uploaded},
            follow=False,
        )
        print("Response status:", response.status_code)
        print("Response URL:", getattr(response, "url", None))
        print("Import error:", response.context.get("import_error")
            if response.context else None)
        print("Form errors:", response.context.get("form").errors
            if response.context and response.context.get("form") else None)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/property-catalog/preview/")

        preview_response = self.client.post(
            "/property-catalog/preview/",
            {"action": "confirm"},
            follow=False,
        )

        self.assertEqual(preview_response.status_code, 302)
        self.assertEqual(PropertyCatalog.objects.count(), 1)
        self.assertEqual(PropertyCatalog.objects.get().name, "Demo Catalog")
