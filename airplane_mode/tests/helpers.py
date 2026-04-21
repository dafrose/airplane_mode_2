# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Test helpers for the Airplane Mode app.

`test_records.json` files seed the DocTypes whose names are predictable
(Airport, Airline, Airplane, Add-on Type). These helpers create the
scenario-specific records (flights, passengers, tickets) that vary per test.
"""

from __future__ import annotations

from datetime import date, time

import frappe

TEST_AIRLINE = "_Test Airways"
TEST_SOURCE_AIRPORT = "_TST"
TEST_DESTINATION_AIRPORT = "_TXY"


def get_test_airplane() -> str:
	"""Return the name of the seeded test airplane (capacity = 2)."""
	return frappe.db.get_value("Airplane", {"airline": TEST_AIRLINE}, "name")


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
	data: dict = {
		"doctype": "Airplane Flight",
		"airplane": airplane or get_test_airplane(),
		"source_airport": source,
		"destination_airport": destination,
		"date_of_departure": departure_date or date(2099, 6, 15),
		"time_of_departure": departure_time or time(9, 30),
		"duration": duration_seconds,
	}
	if gate_number is not None:
		data["gate_number"] = gate_number
	doc = frappe.get_doc(data).insert(ignore_permissions=True)
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
