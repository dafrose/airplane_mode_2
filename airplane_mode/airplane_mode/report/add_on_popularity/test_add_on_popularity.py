# Copyright (c) 2026, ALYF and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from airplane_mode.tests.helpers import create_test_flight, create_test_ticket

REPORT_NAME = "Add-on Popularity"


class TestAddOnPopularityReport(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		flight = create_test_flight()

		cls._t1 = create_test_ticket(
			flight=flight.name,
			flight_price=100,
			add_ons=[
				{"item": "_Test Baggage", "amount": 30},
				{"item": "_Test Meal", "amount": 20},
			],
		)
		cls._t2 = create_test_ticket(
			flight=flight.name,
			flight_price=100,
			add_ons=[{"item": "_Test Baggage", "amount": 30}],
		)

	def _run(self):
		report = frappe.get_doc("Report", REPORT_NAME)
		columns, data = report.execute_query_report({})
		rows = {row[0]: row[1] for row in data}
		return columns, rows

	def test_report_runs_and_returns_columns_and_data(self):
		columns, rows = self._run()
		self.assertEqual(len(columns), 2)
		self.assertGreaterEqual(len(rows), 2)

	def test_sold_count_reflects_ticket_inclusions(self):
		_, rows = self._run()
		self.assertEqual(rows.get("_Test Baggage"), 2)
		self.assertEqual(rows.get("_Test Meal"), 1)

	def test_results_sorted_by_sold_count_desc(self):
		_, data = frappe.get_doc("Report", REPORT_NAME).execute_query_report({})
		counts = [row[1] for row in data]
		self.assertEqual(counts, sorted(counts, reverse=True))
