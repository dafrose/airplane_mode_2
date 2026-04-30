# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Test helpers for the Airplane Mode app.

Standard **Airline** / **Airplane** / **Add-on Type** / **Airport** / **User**
rows used by tests are created on demand and removed when the test interpreter
exits (`register_test_site_data_cleanup`).
"""

from __future__ import annotations

import atexit
from datetime import date, time

import frappe

TEST_AIRLINE = "_Test Airways"
TEST_SOURCE_AIRPORT = "_TST"
TEST_DESTINATION_AIRPORT = "_TXY"

TRAVEL_AGENT_A = "travel_agent_a@airplane.test"
TRAVEL_AGENT_B = "travel_agent_b@airplane.test"
SHOP_TENANT_A = "shop_tenant_a@airplane.test"
SHOP_TENANT_B = "shop_tenant_b@airplane.test"

# **Shop Tenant** role is assigned only when linked from **Shop Tenant** `user`.
STANDARD_TEST_USERS: dict[str, tuple[str, ...]] = {
	TRAVEL_AGENT_A: ("Travel Agent",),
	TRAVEL_AGENT_B: ("Travel Agent",),
	SHOP_TENANT_A: (),
	SHOP_TENANT_B: (),
}

TEST_AIRPORT_NAMES: tuple[str, ...] = (TEST_SOURCE_AIRPORT, TEST_DESTINATION_AIRPORT)

TEST_AIRPLANE_MODEL = "_Test Plane"

TEST_ADD_ON_TYPE_NAMES: tuple[str, ...] = ("_Test Baggage", "_Test Meal")

_test_site_cleanup_registered = False


def register_test_site_data_cleanup() -> None:
	"""Register one-shot cleanup of all helper-managed test rows at process exit."""
	global _test_site_cleanup_registered
	if _test_site_cleanup_registered:
		return
	_test_site_cleanup_registered = True
	atexit.register(remove_test_site_data)


def remove_test_site_data() -> None:
	"""Remove airports (and dependents), test fleet, add-on types, then standard test users."""
	remove_test_airports()
	remove_test_airline_and_airplane()
	remove_test_add_on_types()
	remove_standard_test_users()


def ensure_standard_test_users() -> None:
	"""Insert the shared @airplane.test **User** rows used across permission tests."""
	register_test_site_data_cleanup()
	for email, roles in STANDARD_TEST_USERS.items():
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": email.split("@", 1)[0],
					"send_welcome_email": 0,
					"new_password": "Password123!",
				}
			).insert(ignore_permissions=True)

		existing = {r.role for r in user.get("roles", [])}
		missing = [r for r in roles if r not in existing]
		if missing:
			for role in missing:
				user.append("roles", {"role": role})
			user.save(ignore_permissions=True)

		if email.startswith("shop_tenant_") and email.endswith("@airplane.test"):
			user.reload()
			if "Shop Tenant" in {r.role for r in user.roles}:
				user.remove_roles("Shop Tenant")
			for up in frappe.get_all(
				"User Permission",
				filters={"user": email, "allow": "Shop Tenant"},
				pluck="name",
			):
				frappe.delete_doc("User Permission", up, ignore_permissions=True, force=True)


def remove_standard_test_users() -> None:
	if not getattr(frappe.local, "db", None):
		return
	try:
		frappe.set_user("Administrator")
		for email in STANDARD_TEST_USERS:
			if not frappe.db.exists("User", email):
				continue
			for st in frappe.get_all("Shop Tenant", filters={"user": email}, pluck="name"):
				frappe.delete_doc("Shop Tenant", st, force=True, ignore_permissions=True)
			for up in frappe.get_all("User Permission", filters={"user": email}, pluck="name"):
				frappe.delete_doc("User Permission", up, force=True, ignore_permissions=True)
			for fp in frappe.get_all("Flight Passenger", filters={"user": email}, pluck="name"):
				frappe.delete_doc("Flight Passenger", fp, force=True, ignore_permissions=True)
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		raise


def ensure_test_airports() -> None:
	"""Insert the two standard test **Airport** rows if they are missing."""
	register_test_site_data_cleanup()
	for row in (
		{
			"name": TEST_SOURCE_AIRPORT,
			"code": TEST_SOURCE_AIRPORT,
			"city": "Test City One",
			"country": "Testland",
		},
		{
			"name": TEST_DESTINATION_AIRPORT,
			"code": TEST_DESTINATION_AIRPORT,
			"city": "Test City Two",
			"country": "Testland",
		},
	):
		if frappe.db.exists("Airport", row["name"]):
			continue
		frappe.get_doc({"doctype": "Airport", **row}).insert(ignore_permissions=True)


def remove_test_airports() -> None:
	"""Delete standard test airports and dependent rows (best-effort at process exit)."""
	if not getattr(frappe.local, "db", None):
		return

	try:
		frappe.set_user("Administrator")
		ap_list = list(TEST_AIRPORT_NAMES)

		for shop in frappe.get_all("Shop", filters={"airport": ("in", ap_list)}, pluck="name"):
			frappe.delete_doc("Shop", shop, force=True, ignore_permissions=True)

		flight_names: set[str] = set()
		for ap in ap_list:
			flight_names.update(
				frappe.get_all("Airplane Flight", filters={"source_airport": ap}, pluck="name")
			)
			flight_names.update(
				frappe.get_all("Airplane Flight", filters={"destination_airport": ap}, pluck="name")
			)

		for flight_name in flight_names:
			for ticket in frappe.get_all("Airplane Ticket", filters={"flight": flight_name}, pluck="name"):
				frappe.delete_doc("Airplane Ticket", ticket, force=True, ignore_permissions=True)
			if frappe.db.exists("Airplane Flight", flight_name):
				frappe.delete_doc("Airplane Flight", flight_name, force=True, ignore_permissions=True)

		for name in ap_list:
			if frappe.db.exists("Airport", name):
				frappe.delete_doc("Airport", name, force=True, ignore_permissions=True)

		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		raise


def ensure_test_airline_and_airplane() -> None:
	"""Ensure **Airline** ``_Test Airways`` and **Airplane** ``_Test Plane`` (capacity 2) exist."""
	register_test_site_data_cleanup()
	if not frappe.db.exists("Airline", TEST_AIRLINE):
		frappe.get_doc(
			{
				"doctype": "Airline",
				"name": TEST_AIRLINE,
				"headquarters": "Test HQ",
				"customer_care_number": "000-TEST-1",
				"founding_year": 2000,
			}
		).insert(ignore_permissions=True)
	if not frappe.db.get_value("Airplane", {"airline": TEST_AIRLINE, "model": TEST_AIRPLANE_MODEL}, "name"):
		frappe.get_doc(
			{
				"doctype": "Airplane",
				"model": TEST_AIRPLANE_MODEL,
				"airline": TEST_AIRLINE,
				"capacity": 2,
			}
		).insert(ignore_permissions=True)


def remove_test_airline_and_airplane() -> None:
	if not getattr(frappe.local, "db", None):
		return
	try:
		frappe.set_user("Administrator")
		plane = frappe.db.get_value(
			"Airplane", {"airline": TEST_AIRLINE, "model": TEST_AIRPLANE_MODEL}, "name"
		)
		if plane:
			for flight in frappe.get_all("Airplane Flight", filters={"airplane": plane}, pluck="name"):
				for ticket in frappe.get_all("Airplane Ticket", filters={"flight": flight}, pluck="name"):
					frappe.delete_doc("Airplane Ticket", ticket, force=True, ignore_permissions=True)
				frappe.delete_doc("Airplane Flight", flight, force=True, ignore_permissions=True)
			frappe.delete_doc("Airplane", plane, force=True, ignore_permissions=True)
		if (
			frappe.db.exists("Airline", TEST_AIRLINE)
			and frappe.db.count("Airplane", {"airline": TEST_AIRLINE}) == 0
		):
			frappe.delete_doc("Airline", TEST_AIRLINE, force=True, ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		raise


def ensure_test_add_on_types() -> None:
	"""Ensure **Airplane Ticket Add-on Type** rows used in ticket/report tests exist."""
	register_test_site_data_cleanup()
	for name, description in (
		("_Test Baggage", "Extra checked baggage"),
		("_Test Meal", "In-flight meal"),
	):
		if frappe.db.exists("Airplane Ticket Add-on Type", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Airplane Ticket Add-on Type",
				"name": name,
				"description": description,
			}
		).insert(ignore_permissions=True)


def remove_test_add_on_types() -> None:
	if not getattr(frappe.local, "db", None):
		return
	try:
		frappe.set_user("Administrator")
		for name in TEST_ADD_ON_TYPE_NAMES:
			if frappe.db.exists("Airplane Ticket Add-on Type", name):
				frappe.delete_doc("Airplane Ticket Add-on Type", name, force=True, ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		raise


def get_test_airplane() -> str:
	"""Return the name of the standard test **Airplane** (capacity = 2)."""
	ensure_test_airline_and_airplane()
	name = frappe.db.get_value("Airplane", {"airline": TEST_AIRLINE, "model": TEST_AIRPLANE_MODEL}, "name")
	if not name:
		raise AssertionError("Failed to resolve test Airplane after ensure_test_airline_and_airplane")
	return name


def create_test_flight(
	*,
	source: str = TEST_SOURCE_AIRPORT,
	destination: str = TEST_DESTINATION_AIRPORT,
	departure_date: date | None = None,
	departure_time: time | None = None,
	duration_seconds: int = 2 * 60 * 60,
	airplane: str | None = None,
	gate_number: str | None = None,
) -> frappe.model.document.Document:
	ensure_test_airports()
	resolved_airplane = airplane or get_test_airplane()
	data: dict = {
		"doctype": "Airplane Flight",
		"airplane": resolved_airplane,
		"source_airport": source,
		"destination_airport": destination,
		"date_of_departure": departure_date or date(2099, 6, 15),
		"time_of_departure": departure_time or time(9, 30),
		"duration": duration_seconds,
	}
	if gate_number is not None:
		data["gate_number"] = gate_number
	doc = frappe.get_doc(data).insert(ignore_permissions=True)
	doc.reload()
	doc.flags.ignore_permissions = False
	return doc


def create_test_passenger(
	first_name: str = "_TestPax",
	last_name: str = "Doe",
	*,
	user: str | None = None,
) -> str:
	"""Insert a **Flight Passenger** or return the existing row for *user* (unique per user)."""
	user = user or frappe.session.user
	existing = frappe.db.get_value("Flight Passenger", {"user": user}, "name")
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Flight Passenger",
			"first_name": first_name,
			"last_name": last_name,
			"date_of_birth": "1990-01-01",
			"user": user,
		}
	).insert(ignore_permissions=True)
	doc.flags.ignore_permissions = False
	return doc.name


def create_test_ticket(
	*,
	flight: str,
	passenger: str | None = None,
	flight_price: float = 100.0,
	add_ons: list[dict] | None = None,
	seat: str | None = None,
	status: str = "Booked",
) -> frappe.model.document.Document:
	if add_ons:
		ensure_test_add_on_types()
	if passenger is None:
		passenger = create_test_passenger()

	doc = frappe.get_doc(
		{
			"doctype": "Airplane Ticket",
			"flight": flight,
			"passenger": passenger,
			"flight_price": flight_price,
			"status": status,
		}
	)
	if seat is not None:
		doc.seat = seat
	for row in add_ons or []:
		doc.append("add_ons", row)
	doc.insert(ignore_permissions=True)
	doc.flags.ignore_permissions = False
	return doc


def get_shop_type_for_tests() -> str:
	"""Return a **Shop Type** name for inserting **Shop** rows (mandatory on many sites)."""
	name = frappe.db.get_value("Shop Type", {"enabled": 1}, "name", order_by="name asc")
	if not name:
		name = frappe.db.get_value("Shop Type", {}, "name", order_by="name asc")
	if not name:
		raise AssertionError("No Shop Type rows; migrate Shop Type fixtures or create one.")
	return name
