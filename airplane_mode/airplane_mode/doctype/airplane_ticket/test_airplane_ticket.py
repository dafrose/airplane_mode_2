# Copyright (c) 2026, ALYF and Contributors
# See license.txt

import re

import frappe
from frappe.tests.utils import FrappeTestCase

from airplane_mode.airplane_mode.doctype.airplane_ticket.airplane_ticket import (
	generate_seat_assignment,
)
from airplane_mode.tests.helpers import (
	create_test_flight,
	create_test_passenger,
	create_test_ticket,
)

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
		super().setUp()
		frappe.set_user("Administrator")
		self.flight = create_test_flight()

	def test_validate_sets_gate_number_from_flight_when_present(self):
		flight = create_test_flight(gate_number="D4")
		ticket = create_test_ticket(flight=flight.name)
		self.assertEqual(ticket.gate_number, "D4")

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


class TestAirplaneTicketPassengerPermissions(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.flight = create_test_flight()
		self.email = "passenger_perm_scope@airplane.test"
		self._ensure_passenger_website_user(self.email)
		self.user_name = frappe.db.get_value("User", {"email": self.email}, "name")
		self.own_passenger = create_test_passenger(first_name="_OwnPax", user=self.user_name)
		self.other_passenger = create_test_passenger(first_name="_OtherPax")
		self.ticket_own = create_test_ticket(flight=self.flight.name, passenger=self.own_passenger)
		self.ticket_other = create_test_ticket(flight=self.flight.name, passenger=self.other_passenger)
		# **Travel Agent** read perm uses *if_owner*; assign owner so list tests see both rows.
		for row in (self.ticket_own, self.ticket_other):
			frappe.db.set_value(
				"Airplane Ticket",
				row.name,
				"owner",
				"travel_agent_a@airplane.test",
				update_modified=False,
			)

	def tearDown(self):
		frappe.set_user("Administrator")

	def _ensure_passenger_website_user(self, email: str) -> None:
		if frappe.db.exists("User", {"email": email}):
			return
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Pax",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
				"new_password": "testpass123",
			}
		)
		user.append("roles", {"role": "Passenger"})
		user.insert(ignore_permissions=True)

	def test_get_list_only_shows_linked_tickets(self):
		frappe.set_user(self.user_name)
		names = frappe.get_list("Airplane Ticket", pluck="name")
		self.assertIn(self.ticket_own.name, names)
		self.assertNotIn(self.ticket_other.name, names)

	def test_has_permission_denies_other_passenger_ticket(self):
		frappe.set_user(self.user_name)
		self.assertTrue(frappe.has_permission("Airplane Ticket", "read", doc=self.ticket_own))
		self.assertFalse(frappe.has_permission("Airplane Ticket", "read", doc=self.ticket_other))

	def test_portal_user_cannot_book_ticket_for_other_passenger(self):
		frappe.set_user(self.user_name)
		with self.assertRaisesRegex(frappe.ValidationError, "own passenger profile"):
			create_test_ticket(flight=self.flight.name, passenger=self.other_passenger)

	def test_travel_agent_sees_all_tickets(self):
		frappe.set_user("travel_agent_a@airplane.test")
		names = frappe.get_list("Airplane Ticket", pluck="name")
		self.assertIn(self.ticket_own.name, names)
		self.assertIn(self.ticket_other.name, names)
