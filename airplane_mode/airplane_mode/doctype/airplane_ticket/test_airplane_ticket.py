# Copyright (c) 2026, ALYF and Contributors
# See license.txt

import re

import frappe
from frappe.tests.utils import FrappeTestCase

from airplane_mode.airplane_mode.doctype.airplane_ticket.airplane_ticket import (
	generate_seat_assignment,
)
from airplane_mode.tests.helpers import create_test_flight, create_test_ticket

SEAT_REGEX = re.compile(r"^[1-9][0-9]?[A-E]$")


class TestSeatAssignment(FrappeTestCase):
	"""Pure-function tests for `generate_seat_assignment` (no DB hits)."""

	def test_seat_format_always_matches_regex(self):
		for _ in range(500):
			seat = generate_seat_assignment()
			self.assertRegex(seat, SEAT_REGEX, msg=f"Bad seat: {seat!r}")

	def test_seat_row_within_bounds(self):
		for _ in range(500):
			seat = generate_seat_assignment()
			row = int(seat[:-1])
			self.assertGreaterEqual(row, 1)
			self.assertLessEqual(row, 99)


class TestAirplaneTicket(FrappeTestCase):
	"""Each test gets its own flight because the seeded airplane has capacity = 2.

	Sharing a flight via `setUpClass` would make tests order-dependent and would fill
	the flight after the second `insert()`.
	"""

	def setUp(self):
		self.flight = create_test_flight()

	def test_seat_auto_generated_on_insert(self):
		ticket = create_test_ticket(flight=self.flight.name)
		self.assertRegex(ticket.seat, SEAT_REGEX)

	def test_seat_not_overwritten_when_provided(self):
		ticket = create_test_ticket(flight=self.flight.name, seat="42C")
		self.assertEqual(ticket.seat, "42C")

	def test_total_amount_equals_flight_price_plus_add_ons(self):
		ticket = create_test_ticket(
			flight=self.flight.name,
			flight_price=200,
			add_ons=[
				{"item": "_Test Baggage", "amount": 50},
				{"item": "_Test Meal", "amount": 25},
			],
		)
		self.assertEqual(ticket.total_amount, 275)

	def test_duplicate_add_ons_are_removed(self):
		ticket = create_test_ticket(
			flight=self.flight.name,
			flight_price=100,
			add_ons=[
				{"item": "_Test Baggage", "amount": 30},
				{"item": "_Test Baggage", "amount": 30},
			],
		)
		self.assertEqual(len(ticket.add_ons), 1)
		self.assertEqual(ticket.total_amount, 130)

	def test_flight_capacity_is_enforced(self):
		"""The seeded airplane has capacity = 2, so the third ticket must fail."""
		create_test_ticket(flight=self.flight.name)
		create_test_ticket(flight=self.flight.name)

		with self.assertRaisesRegex(frappe.ValidationError, "fully booked"):
			create_test_ticket(flight=self.flight.name)

	def test_cannot_submit_unless_status_boarded(self):
		ticket = create_test_ticket(flight=self.flight.name, status="Booked")
		with self.assertRaisesRegex(frappe.ValidationError, "Boarded"):
			ticket.submit()

	def test_can_submit_when_status_boarded(self):
		ticket = create_test_ticket(flight=self.flight.name, status="Booked")
		ticket.status = "Boarded"
		ticket.submit()
		self.assertEqual(ticket.docstatus, 1)
