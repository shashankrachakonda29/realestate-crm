import json
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from property_catalog.models import (
    CatalogConfiguration,
    CatalogDeveloper,
    CatalogLocation,
    CatalogProject,
    PropertyCatalog,
)
from property_catalog.services import import_catalog


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


class CatalogRequirementSearchTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="catalog-search-user",
            email="search@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.catalog = PropertyCatalog.objects.create(name="Search Catalog")
        self.developer = CatalogDeveloper.objects.create(
            catalog=self.catalog,
            name="Apex Developers",
        )
        self.project = self.create_project(
            "Green Villa",
            project_type="VILLAS",
            status="Under Construction",
            starting_price="6000000",
            price_per_sqft="4000",
        )
        CatalogLocation.objects.create(
            project=self.project,
            locality="Whitefield",
            city="Bengaluru",
            district="Bengaluru Urban",
            state="Karnataka",
            pincode="560066",
        )
        self.two_bhk = self.create_configuration(
            self.project,
            "2 BHK Villa",
            bhk="2",
            bedrooms=2,
            facing="EAST",
            basic_price="6000000",
            built_up_area_sq_ft="1500",
            price_per_sqft="4000",
            availability="Under Construction",
            possession="Dec 2027",
            amenities=["Clubhouse", "Swimming Pool"],
            features=["Garden"],
            notes="Corner home",
        )
        self.three_bhk = self.create_configuration(
            self.project,
            "3 BHK Villa",
            bhk="3",
            bedrooms=3,
            facing="WEST",
            basic_price="8500000",
            built_up_area_sq_ft="2100",
            price_per_sqft="4048",
            availability="Ready to Move",
            possession="Ready",
            amenities=["Parking"],
        )
        self.apartment_project = self.create_project(
            "Lake Apartments",
            project_type="APARTMENTS",
            status="Ready",
            starting_price="4500000",
        )
        CatalogLocation.objects.create(
            project=self.apartment_project,
            locality="Sarjapur",
            city="Bengaluru",
            state="Karnataka",
            pincode="560035",
        )
        self.apartment_configuration = self.create_configuration(
            self.apartment_project,
            "2 BHK Apartment",
            property_type="APARTMENT",
            bhk="2 BHK",
            bedrooms=2,
            facing="NORTH",
            basic_price="4500000",
            carpet_area_sq_ft="1000",
            availability="Ready to Move",
            possession="Immediate",
            amenities=["Garden"],
        )

    def create_project(
        self,
        name,
        *,
        project_type="VILLAS",
        status="",
        starting_price=None,
        price_per_sqft=None,
    ):
        return CatalogProject.objects.create(
            developer=self.developer,
            name=name,
            project_type=project_type,
            status=status,
            starting_price=starting_price,
            price_per_sqft=price_per_sqft,
        )

    @staticmethod
    def create_configuration(
        project,
        type_name,
        *,
        property_type="VILLA",
        bhk="",
        bedrooms=None,
        facing="",
        basic_price=None,
        built_up_area_sq_ft=None,
        carpet_area_sq_ft=None,
        price_per_sqft=None,
        availability="",
        possession="",
        amenities=None,
        features=None,
        notes="",
    ):
        return CatalogConfiguration.objects.create(
            project=project,
            property_type=property_type,
            type_name=type_name,
            bhk=bhk,
            bedrooms=bedrooms,
            facing=facing,
            basic_price=basic_price,
            built_up_area_sq_ft=built_up_area_sq_ft,
            carpet_area_sq_ft=carpet_area_sq_ft,
            price_per_sqft=price_per_sqft,
            availability=availability,
            possession=possession,
            amenities=amenities or [],
            features=features or [],
            notes=notes,
        )

    def search(self, **params):
        return self.client.get(
            f"/property-catalog/{self.catalog.pk}/",
            params,
        )

    def matching_projects(self, response):
        return {
            project.pk
            for developer in response.context["developers"]
            for project in developer.matching_projects
        }

    def test_unfiltered_page_shows_catalog_and_all_matching_counts(self):
        response = self.search()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Filters")
        self.assertEqual(response.context["total_projects"], 2)
        self.assertEqual(response.context["total_configurations"], 3)

    def test_developer_project_type_property_type_and_project_search(self):
        response = self.search(
            developer=str(self.developer.pk),
            project=str(self.project.pk),
            project_type="VILLAS",
            property_type="VILLA",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.matching_projects(response), {self.project.pk})
        shown = response.context["developers"][0].matching_projects[0]
        self.assertEqual(len(shown.matching_configurations), 2)

        response = self.search(project=str(self.apartment_project.pk))
        self.assertEqual(self.matching_projects(response), {self.apartment_project.pk})

    def test_budget_boundaries_are_decimal_safe(self):
        response = self.search(min_budget="6000000.01")
        self.assertEqual(self.matching_projects(response), {self.project.pk})
        matching = response.context["developers"][0].matching_projects[0]
        self.assertEqual(
            [item.pk for item in matching.matching_configurations],
            [self.three_bhk.pk],
        )

        response = self.search(max_budget="6000000")
        self.assertEqual(self.matching_projects(response), {self.project.pk, self.apartment_project.pk})

    def test_bhk_is_matched_exactly_and_facing_is_filtered(self):
        response = self.search(bhk="bedrooms:2")
        selected_configurations = {
            item.pk
            for developer in response.context["developers"]
            for project in developer.matching_projects
            for item in project.matching_configurations
        }
        self.assertEqual(
            selected_configurations,
            {self.two_bhk.pk, self.apartment_configuration.pk},
        )

        response = self.search(bhk="bedrooms:2", facing="EAST")
        self.assertEqual(self.matching_projects(response), {self.project.pk})
        configs = response.context["developers"][0].matching_projects[0].matching_configurations
        self.assertEqual([item.pk for item in configs], [self.two_bhk.pk])

    def test_location_matches_locality_city_district_state_and_pincode(self):
        expected = {
            "Whitefield": {self.project.pk},
            "Bengaluru Urban": {self.project.pk},
            "Karnataka": {self.project.pk, self.apartment_project.pk},
            "560066": {self.project.pk},
        }
        for value, expected_projects in expected.items():
            with self.subTest(value=value):
                response = self.search(location=value)
                self.assertEqual(self.matching_projects(response), expected_projects)

    def test_area_filters_include_carpet_area_and_price_per_square_foot(self):
        response = self.search(min_area="900", max_area="1100")
        self.assertEqual(self.matching_projects(response), {self.apartment_project.pk})

        response = self.search(min_price_per_sqft="4000", max_price_per_sqft="4000")
        self.assertEqual(self.matching_projects(response), {self.project.pk})
        self.assertEqual(
            response.context["developers"][0].matching_projects[0].matching_configuration_count,
            1,
        )

    def test_availability_possession_amenities_and_keyword_search(self):
        response = self.search(
            availability="Under Construction",
            possession="2027",
            amenity="Clubhouse",
        )
        self.assertEqual(self.matching_projects(response), {self.project.pk})
        self.assertEqual(
            [item.pk for item in response.context["developers"][0].matching_projects[0].matching_configurations],
            [self.two_bhk.pk],
        )

        response = self.search(feature=["Garden"])
        self.assertEqual(
            [item.pk for item in response.context["developers"][0].matching_projects[0].matching_configurations],
            [self.two_bhk.pk],
        )

        response = self.search(amenity=["Clubhouse", "Swimming Pool"])
        self.assertEqual(self.matching_projects(response), {self.project.pk})
        self.assertEqual(
            [item.pk for item in response.context["developers"][0].matching_projects[0].matching_configurations],
            [self.two_bhk.pk],
        )

        response = self.search(keyword="Corner home")
        self.assertEqual(self.matching_projects(response), {self.project.pk})
        self.assertEqual(
            [item.pk for item in response.context["developers"][0].matching_projects[0].matching_configurations],
            [self.two_bhk.pk],
        )

    def test_combined_filters_apply_with_and_logic(self):
        response = self.search(
            project_type="VILLAS",
            status="Under Construction",
            property_type="VILLA",
            min_budget="5000000",
            max_budget="7000000",
            bhk="bedrooms:2",
            facing="EAST",
            location="560066",
            availability="Under Construction",
            amenity="Clubhouse",
            feature="Garden",
        )
        self.assertEqual(self.matching_projects(response), {self.project.pk})
        self.assertEqual(
            [item.pk for item in response.context["developers"][0].matching_projects[0].matching_configurations],
            [self.two_bhk.pk],
        )

    def test_invalid_numeric_input_is_reported_and_values_are_preserved(self):
        response = self.search(min_budget="not-a-number")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a number")
        self.assertContains(response, 'value="not-a-number"')

        response = self.search(min_area="2000", max_area="1000")
        self.assertContains(response, "Maximum area must be greater than or equal to minimum area.")

    def test_location_subfields_notes_and_individual_filter_chips(self):
        self.project.channel_partner_notes = "Channel partner approved"
        self.project.save(update_fields=["channel_partner_notes"])

        response = self.search(city="Bengaluru", state="Karnataka", notes="Corner")
        self.assertEqual(self.matching_projects(response), {self.project.pk})
        self.assertEqual(
            [item.pk for item in response.context["developers"][0].matching_projects[0].matching_configurations],
            [self.two_bhk.pk],
        )

        response = self.search(notes="Channel partner")
        self.assertEqual(self.matching_projects(response), {self.project.pk})
        self.assertEqual(
            response.context["developers"][0].matching_projects[0].matching_configuration_count,
            2,
        )

        response = self.search(bhk="bedrooms:2", facing="EAST")
        facing_chip = next(
            chip
            for chip in response.context["active_filter_chips"]
            if chip["label"] == "Facing: East"
        )
        parsed_query = parse_qs(urlsplit(facing_chip["url"]).query)
        self.assertEqual(parsed_query, {"bhk": ["bedrooms:2"]})

        response = self.search(keyword="Green", bhk="bedrooms:2", facing="EAST")
        reset_query = parse_qs(urlsplit(response.context["reset_filters_url"]).query)
        self.assertEqual(reset_query, {"keyword": ["Green"]})

    def test_each_filter_category_can_be_applied_independently(self):
        all_projects = {self.project.pk, self.apartment_project.pk}
        cases = (
            ({"developer": str(self.developer.pk)}, all_projects),
            ({"project_type": "VILLAS"}, {self.project.pk}),
            ({"property_type": "APARTMENT"}, {self.apartment_project.pk}),
            ({"status": "Ready"}, {self.apartment_project.pk}),
            ({"availability": "Under Construction"}, {self.project.pk}),
            ({"possession": "Immediate"}, {self.apartment_project.pk}),
            ({"bhk": "bedrooms:3"}, {self.project.pk}),
            ({"facing": "NORTH"}, {self.apartment_project.pk}),
            ({"locality": "Whitefield"}, {self.project.pk}),
            ({"city": "Bengaluru"}, all_projects),
            ({"district": "Bengaluru Urban"}, {self.project.pk}),
            ({"state": "Karnataka"}, all_projects),
            ({"pincode": "560035"}, {self.apartment_project.pk}),
            ({"min_area": "1400"}, {self.project.pk}),
            ({"max_area": "1100"}, {self.apartment_project.pk}),
            ({"min_price_per_sqft": "4040"}, {self.project.pk}),
            ({"max_price_per_sqft": "4000"}, {self.project.pk}),
            ({"amenity": "Parking"}, {self.project.pk}),
            ({"feature": "Garden"}, {self.project.pk}),
            ({"notes": "Corner"}, {self.project.pk}),
            ({"keyword": "Apex"}, all_projects),
        )
        for params, expected_projects in cases:
            with self.subTest(params=params):
                response = self.search(**params)
                self.assertEqual(self.matching_projects(response), expected_projects)

    def test_empty_results_and_unmatched_configurations_are_hidden(self):
        response = self.search(keyword="No matching property")
        self.assertEqual(response.context["total_projects"], 0)
        self.assertEqual(response.context["total_configurations"], 0)

        response = self.search(facing="EAST", availability="Ready to Move")
        self.assertEqual(self.matching_projects(response), set())

    def test_catalog_isolation_and_clear_filters(self):
        other_catalog = PropertyCatalog.objects.create(name="Other Catalog")
        other_developer = CatalogDeveloper.objects.create(
            catalog=other_catalog,
            name="Other Developer",
        )
        CatalogProject.objects.create(
            developer=other_developer,
            name="Hidden Project",
            project_type="VILLAS",
        )

        response = self.search(keyword="Hidden Project")
        self.assertEqual(response.context["total_projects"], 0)
        self.assertContains(response, "Clear all")
        self.assertContains(
            response,
            f'href="/property-catalog/{self.catalog.pk}/"',
        )

        cleared_response = self.client.get(f"/property-catalog/{self.catalog.pk}/")
        self.assertEqual(cleared_response.context["total_projects"], 2)

    def test_filter_panel_is_closed_by_default_and_contains_grouped_filters(self):
        response = self.search()
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, 'id="catalogFilterDrawer"')
        self.assertContains(response, "Project")
        self.assertContains(response, "Amenities and features")
        self.assertContains(response, 'placeholder="Search projects, developers, locations..."')


class CatalogDuplicateHandlingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="catalog-entry-user",
            email="entry@example.com",
            password="test-password-123",
        )
        self.client.force_login(self.user)

    @staticmethod
    def payload(
        developer_name="Apex Developers",
        project_name="Cedar Villas",
        configuration_name="3 BHK Premium",
    ):
        return {
            "catalog_name": "Duplicate Check Catalog",
            "version": "1.0",
            "developers": [
                {
                    "name": developer_name,
                    "email": "sales@example.com",
                    "projects": [
                        {
                            "name": project_name,
                            "project_type": "VILLAS",
                            "project_details": {
                                "status": "Under Construction",
                                "starting_price": "8500000.00",
                            },
                            "configurations": [
                                {
                                    "property_type": "VILLA",
                                    "type_name": configuration_name,
                                    "bhk": "3",
                                    "bedrooms": 3,
                                    "built_up_area_sq_ft": "2100.00",
                                    "basic_price": "8500000.00",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

    def test_reimport_reuses_developer_project_and_configuration(self):
        catalog, first_summary, _ = import_catalog(self.payload())
        second_catalog, second_summary, records = import_catalog(
            self.payload(),
            catalog,
        )

        self.assertEqual(second_catalog.pk, catalog.pk)
        self.assertEqual(first_summary["created"], 3)
        self.assertEqual(second_summary["created"], 0)
        self.assertEqual(second_summary["reused"], 3, records)
        self.assertEqual(
            [record["action"] for record in records],
            ["reused", "reused", "reused"],
        )
        self.assertEqual(catalog.developers.count(), 1)
        self.assertEqual(CatalogProject.objects.filter(developer__catalog=catalog).count(), 1)
        self.assertEqual(CatalogConfiguration.objects.filter(project__developer__catalog=catalog).count(), 1)

    def test_names_match_case_insensitively_and_trim_outer_whitespace(self):
        catalog, _, _ = import_catalog(self.payload())
        repeated = self.payload(
            developer_name="  apex developers ",
            project_name=" CEDAR VILLAS ",
            configuration_name=" 3 bhk premium ",
        )

        _, summary, _ = import_catalog(repeated, catalog)

        self.assertEqual(summary["reused"], 3)
        self.assertEqual(summary["created"], 0)

    def test_conflicting_details_are_reported_and_existing_values_are_preserved(self):
        catalog, _, _ = import_catalog(self.payload())
        repeated = self.payload()
        repeated["developers"][0]["email"] = "different@example.com"
        repeated["developers"][0]["projects"][0]["project_details"]["status"] = "Ready"
        repeated["developers"][0]["projects"][0]["configurations"][0]["basic_price"] = "9000000"

        _, summary, records = import_catalog(repeated, catalog)

        self.assertEqual(summary["conflicting"], 3)
        self.assertEqual(summary["skipped"], 3)
        self.assertEqual([record["action"] for record in records], ["conflicting"] * 3)
        developer = catalog.developers.get()
        project = developer.projects.get()
        configuration = project.configurations.get()
        self.assertEqual(developer.email, "sales@example.com")
        self.assertEqual(project.status, "Under Construction")
        self.assertEqual(str(configuration.basic_price), "8500000.00")
        self.assertTrue(all(record["differences"] for record in records))

    def test_same_project_name_under_a_different_developer_is_not_merged(self):
        catalog, _, _ = import_catalog(self.payload())
        other_payload = self.payload(developer_name="Different Builder")

        _, summary, _ = import_catalog(other_payload, catalog)

        self.assertEqual(summary["created"], 3)
        self.assertEqual(catalog.developers.count(), 2)
        self.assertEqual(
            CatalogProject.objects.filter(
                developer__catalog=catalog,
                name="Cedar Villas",
            ).count(),
            2,
        )

    def test_same_bhk_with_distinct_configuration_identity_is_kept(self):
        payload = self.payload()
        project = payload["developers"][0]["projects"][0]
        project["configurations"].append(
            {
                "property_type": "VILLA",
                "type_name": "3 BHK Garden",
                "bhk": "3",
                "bedrooms": 3,
                "built_up_area_sq_ft": "2400",
                "basic_price": "9500000",
            }
        )

        catalog, summary, _ = import_catalog(payload)

        self.assertEqual(summary["created"], 4)
        self.assertEqual(
            CatalogConfiguration.objects.filter(
                project__developer__catalog=catalog
            ).count(),
            2,
        )

    def test_import_adds_a_new_project_to_the_existing_catalog_developer(self):
        catalog, _, _ = import_catalog(self.payload())
        developer = catalog.developers.get()
        new_project_payload = self.payload(project_name="Oak Residences")

        _, summary, _ = import_catalog(new_project_payload, catalog)

        self.assertEqual(summary["reused"], 1)
        self.assertEqual(summary["created"], 2)
        self.assertEqual(developer.projects.count(), 2)

    def test_manual_project_and_configuration_creation_and_duplicate_review(self):
        catalog, _, _ = import_catalog(self.payload())
        developer = catalog.developers.get()
        add_project_url = reverse(
            "property_catalog:catalog_project_create",
            kwargs={"catalog_pk": catalog.pk, "developer_pk": developer.pk},
        )
        response = self.client.post(
            add_project_url,
            {"name": "Oak Residences", "project_type": "VILLAS"},
        )
        self.assertEqual(response.status_code, 302)
        project = developer.projects.get(name="Oak Residences")

        response = self.client.post(
            reverse(
                "property_catalog:catalog_project_create",
                kwargs={"catalog_pk": catalog.pk, "developer_pk": developer.pk},
            ),
            {"name": " oak residences ", "project_type": "APARTMENTS"},
            follow=True,
        )
        self.assertEqual(developer.projects.filter(name__iexact="Oak Residences").count(), 1)
        self.assertContains(response, "Existing data was kept")

        add_configuration_url = reverse(
            "property_catalog:catalog_configuration_create",
            kwargs={"catalog_pk": catalog.pk, "project_pk": project.pk},
        )
        new_configuration = {
            "property_type": "VILLA",
            "type_name": "3 BHK Courtyard",
            "bhk": "3",
            "bedrooms": "3",
            "built_up_area_sq_ft": "2400",
            "amenities": "Garden\nParking",
            "features": "Corner unit",
        }
        response = self.client.post(add_configuration_url, new_configuration)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(project.configurations.count(), 1)

        response = self.client.post(
            add_configuration_url,
            {**new_configuration, "type_name": " 3 bhk courtyard "},
            follow=True,
        )
        self.assertEqual(project.configurations.count(), 1)
        self.assertContains(response, "An equivalent configuration already exists")

    def test_manual_developer_addition_is_catalog_scoped(self):
        catalog = PropertyCatalog.objects.create(name="Manual Catalog")
        create_url = reverse(
            "property_catalog:catalog_developer_create",
            kwargs={"catalog_pk": catalog.pk},
        )
        response = self.client.post(
            create_url,
            {"name": "Northstar Realty", "email": "hello@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(catalog.developers.filter(name="Northstar Realty").exists())

        response = self.client.post(
            create_url,
            {"name": " northstar realty ", "email": "other@example.com"},
            follow=True,
        )
        self.assertEqual(catalog.developers.count(), 1)
        self.assertContains(response, "Details differ in: email")

    def test_catalog_isolation_and_import_rollback(self):
        first_catalog, _, _ = import_catalog(self.payload())
        second_catalog = PropertyCatalog.objects.create(name="Other Catalog")
        _, summary, _ = import_catalog(self.payload(), second_catalog)
        self.assertEqual(summary["created"], 3)
        self.assertEqual(second_catalog.developers.count(), 1)
        self.assertEqual(first_catalog.developers.count(), 1)

        failing_payload = self.payload(developer_name="Rollback Developer")
        with self.assertRaises(RuntimeError):
            from unittest.mock import patch

            with patch(
                "property_catalog.services.CatalogConfiguration.objects.create",
                side_effect=RuntimeError("simulated configuration write failure"),
            ):
                import_catalog(failing_payload)
        self.assertFalse(
            PropertyCatalog.objects.filter(name="Duplicate Check Catalog").exclude(
                pk__in=[first_catalog.pk]
            ).exists()
        )

    def test_existing_catalog_is_selectable_and_preview_reports_reuse(self):
        catalog, _, _ = import_catalog(self.payload())
        uploaded = SimpleUploadedFile(
            "catalog.json",
            json.dumps(self.payload()).encode("utf-8"),
            content_type="application/json",
        )
        response = self.client.post(
            reverse("property_catalog:import_json"),
            {"json_file": uploaded, "target_catalog": str(catalog.pk)},
        )
        self.assertRedirects(response, reverse("property_catalog:preview"))

        preview = self.client.get(reverse("property_catalog:preview"))
        self.assertEqual(preview.context["preview_summary"]["reused"], 3)
        self.assertContains(preview, "Reused")

        confirmation = self.client.post(
            reverse("property_catalog:preview"),
            {"action": "confirm"},
        )
        self.assertRedirects(
            confirmation,
            reverse("property_catalog:catalog_detail", kwargs={"pk": catalog.pk}),
        )
        self.assertEqual(catalog.developers.count(), 1)

    def test_import_page_preselects_catalog_when_launched_from_catalog_details(self):
        catalog = PropertyCatalog.objects.create(name="Selected Catalog")

        response = self.client.get(
            reverse("property_catalog:import_json"),
            {"catalog": catalog.pk},
        )

        self.assertEqual(
            response.context["form"]["target_catalog"].value(),
            catalog.pk,
        )
