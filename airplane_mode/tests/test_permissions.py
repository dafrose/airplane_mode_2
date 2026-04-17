# Copyright (c) 2026, ALYF and Contributors
# See license.txt

"""Verify the Day-3 rule that Travel Agents only see records they own.

The two test users (`travel_agent_a@airplane.test`, `travel_agent_b@airplane.test`)
are guaranteed to exist by `airplane_mode.install.before_tests`, wired in
hooks.py.
"""

import contextlib

import frappe
from frappe.tests.utils import FrappeTestCase

from airplane_mode.tests.helpers import create_test_flight, create_test_passenger

AGENT_A = "travel_agent_a@airplane.test"
AGENT_B = "travel_agent_b@airplane.test"


@contextlib.contextmanager
def as_user(user: str):
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


class TestTravelAgentOwnerOnlyPermissions(FrappeTestCase):
	"""Each test gets its own flight (capacity = 2 on the seeded airplane)."""

	def setUp(self):
		self.flight = create_test_flight()

	def _create_ticket_as(self, user: str) -> str:
		passenger = create_test_passenger()
		with as_user(user):
			ticket = frappe.get_doc(
				{
					"doctype": "Airplane Ticket",
					"flight": self.flight.name,
					"passenger": passenger,
					"flight_price": 100,
					"status": "Booked",
				}
			).insert()
			return ticket.name

	def test_agent_b_cannot_list_agent_a_ticket(self):
		ticket_name = self._create_ticket_as(AGENT_A)

		with as_user(AGENT_B):
			visible = frappe.get_list(
				"Airplane Ticket",
				filters={"name": ticket_name},
				pluck="name",
				ignore_permissions=False,
			)
		self.assertEqual(visible, [])

	def test_agent_b_cannot_read_agent_a_ticket(self):
		"""`frappe.get_doc` doesn't auto-check permissions; use `has_permission` or
		call `.check_permission()` explicitly. The Desk and REST clients use the
		latter — that's what the if-owner rule actually protects."""
		ticket_name = self._create_ticket_as(AGENT_A)

		with as_user(AGENT_B):
			doc = frappe.get_doc("Airplane Ticket", ticket_name)
			self.assertFalse(frappe.has_permission("Airplane Ticket", doc=doc, user=AGENT_B, ptype="read"))
			with self.assertRaises(frappe.PermissionError):
				doc.check_permission("read")

	def test_agent_a_can_read_own_ticket(self):
		ticket_name = self._create_ticket_as(AGENT_A)

		with as_user(AGENT_A):
			doc = frappe.get_doc("Airplane Ticket", ticket_name)
			self.assertEqual(doc.name, ticket_name)
			self.assertTrue(frappe.has_permission("Airplane Ticket", doc=doc, user=AGENT_A, ptype="read"))
