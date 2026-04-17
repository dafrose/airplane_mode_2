# Copyright (c) 2026, ALYF and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from airplane_mode.airplane_mode.doctype.airplane_flight.airplane_flight import (
	BOOK_FLIGHT_WEB_FORM_ROUTE,
)
from airplane_mode.tests.helpers import create_test_flight

test_dependencies = ["Airplane"]


class TestAirplaneFlight(FrappeTestCase):
	def test_on_submit_sets_status_to_completed(self):
		flight = create_test_flight()
		self.assertEqual(flight.status, "Scheduled")

		flight.submit()
		self.assertEqual(
			frappe.db.get_value("Airplane Flight", flight.name, "status"),
			"Completed",
		)

	def test_get_context_builds_book_flight_url(self):
		flight = create_test_flight()
		ctx = frappe._dict()

		flight.get_context(ctx)

		self.assertIn(flight.source_airport_code, ctx.title)
		self.assertIn(flight.destination_airport_code, ctx.title)
		self.assertTrue(ctx.book_flight_url.startswith(f"/{BOOK_FLIGHT_WEB_FORM_ROUTE}/new?flight="))

	def test_get_context_url_quotes_flight_name(self):
		"""Generated flight names contain spaces, which must be URL-encoded."""
		flight = create_test_flight()
		ctx = frappe._dict()

		flight.get_context(ctx)

		query_value = ctx.book_flight_url.split("flight=", 1)[1]
		self.assertNotIn(" ", query_value)
		if " " in flight.name:
			self.assertIn("%20", query_value)
