# Copyright (c) 2026, ALYF and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import set_request

from airplane_mode.airplane_mode.doctype.airplane_flight.airplane_flight import (
	FLIGHTS_WEB_ROUTE,
)
from airplane_mode.api import passenger_signup


def _cleanup_signup_user(email: str) -> None:
	frappe.set_user("Administrator")
	pax = frappe.db.get_value("Flight Passenger", {"user": email}, "name")
	if pax:
		frappe.delete_doc("Flight Passenger", pax, force=True, ignore_permissions=True)
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)


class TestPassengerSignup(FrappeTestCase):
	def tearDown(self):
		_cleanup_signup_user("signup_test_pax@airplane.test")
		_cleanup_signup_user("signup_dup_pax@airplane.test")
		if hasattr(frappe.local, "request"):
			delattr(frappe.local, "request")
		frappe.set_user("Administrator")
		super().tearDown()

	def test_passenger_signup_creates_user_passenger_and_redirects_to_flights(self):
		set_request(method="POST", path="/api/method/airplane_mode.api.passenger_signup")
		frappe.set_user("Guest")

		email = "signup_test_pax@airplane.test"
		out = passenger_signup(
			email=email,
			password="Password123!",
			first_name="Signy",
			last_name="Tester",
			date_of_birth="1995-06-15",
		)
		self.assertEqual(out["redirect_to"], f"/{FLIGHTS_WEB_ROUTE}")
		self.assertTrue(frappe.db.exists("User", email))
		pax_name = frappe.db.get_value("Flight Passenger", {"user": email}, "name")
		self.assertTrue(pax_name)
		doc = frappe.get_doc("Flight Passenger", pax_name)
		self.assertEqual(doc.first_name, "Signy")
		self.assertEqual(doc.last_name, "Tester")
		self.assertEqual(doc.date_of_birth, frappe.utils.getdate("1995-06-15"))
		self.assertEqual(frappe.db.get_value("Flight Passenger", pax_name, "owner"), email)
		self.assertIn("Passenger", frappe.get_roles(email))
		self.assertEqual(frappe.session.user, email)

	def test_passenger_signup_rejects_duplicate_email(self):
		set_request(method="POST", path="/api/method/airplane_mode.api.passenger_signup")
		frappe.set_user("Guest")

		email = "signup_dup_pax@airplane.test"
		passenger_signup(
			email=email,
			password="Password123!",
			first_name="First",
			last_name="",
			date_of_birth="1991-01-01",
		)
		with self.assertRaises(frappe.ValidationError):
			passenger_signup(
				email=email,
				password="Password456!",
				first_name="Second",
				last_name="",
				date_of_birth="1992-02-02",
			)
