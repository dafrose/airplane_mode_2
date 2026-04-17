# Copyright (c) 2026, ALYF and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from airplane_mode.airplane_mode.report.revenue_by_airline.revenue_by_airline import execute
from airplane_mode.tests.helpers import (
	TEST_AIRLINE,
	create_test_flight,
	create_test_ticket,
)


class TestRevenueByAirlineReport(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()

		cls.zero_airline = frappe.get_doc(
			{
				"doctype": "Airline",
				"name": "_Test Zero Airways",
				"headquarters": "Nowhere",
				"customer_care_number": "000-ZERO",
			}
		).insert(ignore_if_duplicate=True)

		cls.zero_airplane = frappe.get_doc(
			{
				"doctype": "Airplane",
				"model": "_Test Zero Plane",
				"airline": cls.zero_airline.name,
				"capacity": 5,
			}
		).insert()

		flight = create_test_flight(airplane=cls.zero_airplane.name)
		cls._unsubmitted_ticket = create_test_ticket(flight=flight.name, flight_price=99999)

		paying_flight = create_test_flight()

		t1 = create_test_ticket(flight=paying_flight.name, flight_price=100, status="Booked")
		t1.status = "Boarded"
		t1.submit()

		t2 = create_test_ticket(flight=paying_flight.name, flight_price=250, status="Booked")
		t2.status = "Boarded"
		t2.submit()

	def test_execute_returns_five_tuple(self):
		result = execute({})
		self.assertEqual(len(result), 5)

	def test_columns_shape(self):
		columns, *_ = execute({})
		self.assertEqual(columns[0]["fieldname"], "airline")
		self.assertEqual(columns[0]["fieldtype"], "Link")
		self.assertEqual(columns[0]["options"], "Airline")
		self.assertEqual(columns[1]["fieldname"], "revenue")
		self.assertEqual(columns[1]["fieldtype"], "Currency")

	def test_zero_revenue_airlines_are_included(self):
		_, data, *_ = execute({})
		airlines = {row["airline"] for row in data}
		self.assertIn(self.zero_airline.name, airlines)

		zero_row = next(row for row in data if row["airline"] == self.zero_airline.name)
		self.assertEqual(zero_row["revenue"], 0)

	def test_only_submitted_tickets_count_toward_revenue(self):
		_, data, *_ = execute({})
		paying_row = next(row for row in data if row["airline"] == TEST_AIRLINE)
		self.assertEqual(paying_row["revenue"], 350)

	def test_chart_is_donut_with_per_airline_values(self):
		*_, chart, _ = execute({})
		self.assertEqual(chart["type"], "donut")
		self.assertEqual(len(chart["data"]["labels"]), len(chart["data"]["datasets"][0]["values"]))

	def test_report_summary_total_matches_sum_of_data(self):
		_, data, _, _, summary = execute({})
		total_from_summary = summary[0]["value"]
		total_from_data = sum(row["revenue"] for row in data)
		self.assertEqual(total_from_summary, total_from_data)
