from django.test import SimpleTestCase

from .services.lead_import import (
	detect_column_mapping,
	normalize_phone,
	normalize_source,
	normalize_status,
	parse_bhk,
	parse_budget,
	parse_follow_up,
)


class LeadImportParsingTests(SimpleTestCase):

	def test_detects_common_columns_without_guessing_duplicates(self):
		mapping = detect_column_mapping(["Full Name", "Mobile Number", "Source"])
		self.assertEqual(mapping["name"], "Full Name")
		self.assertEqual(mapping["phone"], "Mobile Number")
		self.assertEqual(mapping["source"], "Source")
		self.assertNotIn("name", detect_column_mapping(["Name", "Name"]))

	def test_normalizes_phone_and_choices(self):
		self.assertEqual(normalize_phone("+91 98765 43210"), "919876543210")
		self.assertEqual(normalize_phone("00 44 20 1234 5678"), "442012345678")
		self.assertEqual(normalize_source("Facebook Ads"), "META_ADS")
		self.assertEqual(normalize_status("Site Visit Done"), "SITE_VISIT")

	def test_parses_budget_bhk_and_date(self):
		self.assertEqual(parse_budget("50 Lakh"), 5000000)
		self.assertEqual(parse_budget("1.5 Cr"), 15000000)
		self.assertEqual(parse_bhk("4bhk"), 4)
		self.assertEqual(parse_follow_up("23/09/2026").date().isoformat(), "2026-09-23")
