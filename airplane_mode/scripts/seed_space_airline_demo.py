# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Insert demo airlines, airports, airplanes, flights, passengers, and tickets.

Run once per site, e.g.:
	bench --site <site> execute airplane_mode.seed_space_airline_demo.seed
"""

from __future__ import annotations

from datetime import date, time

import frappe
from frappe import _

AIRLINES = [
	{
		"name": "Aurora Spaceways",
		"headquarters": "Enceladus Ice Harbor",
		"founding_year": 2040,
		"customer_care_number": "000-ASW-1",
	},
	{
		"name": "Kuiper Kargo",
		"headquarters": "Orcus Transfer Node",
		"founding_year": 2042,
		"customer_care_number": "000-KKP-2",
	},
]

AIRPORTS = [
	{"name": "Venus Spaceport", "code": "VNS", "city": "Venus Cloud City", "country": "Venus"},
	{"name": "Callisto Landing Pad", "code": "CLP", "city": "Callisto Dome", "country": "Jupiter Orbit"},
	{"name": "Phobos Space Terminal", "code": "PHB", "city": "Phobos Tether", "country": "Mars Orbit"},
]

PASSENGERS = [
	("Lyra", "Andromeda", "1991-03-15"),
	("Orion", "Cassini", "1988-07-22"),
	("Vega", "Rigel", "1995-11-30"),
	("Nova", "Pulsar", "1990-01-08"),
	("Sol", "Corona", "1987-09-19"),
	("Elara", "Titania", "1993-04-04"),
	("Atlas", "Prometheus", "1989-12-12"),
	("Helios", "Chromosphere", "1994-06-06"),
	("Ceres", "Dawn", "1992-02-28"),
	("Io", "Europa", "1996-08-18"),
]

FLIGHT_DEPARTURE = date(2099, 6, 15)
FLIGHT_TIME = time(9, 30)
# Frappe Duration field: seconds
FLIGHT_DURATION_SECONDS = 2 * 60 * 60
AIRPLANE_CAPACITY = 50


def _cleanup_partial_demo_if_needed() -> None:
	"""If a previous run failed after creating airlines/airplanes but before flights, remove it."""
	demo_airline_names = [a["name"] for a in AIRLINES]
	if not frappe.db.exists("Airline", demo_airline_names[0]):
		return
	planes = frappe.get_all("Airplane", filters={"airline": ("in", demo_airline_names)}, pluck="name")
	if not planes:
		return
	if frappe.db.count("Airplane Flight", {"airplane": ("in", planes)}):
		return
	for ap in planes:
		frappe.delete_doc("Airplane", ap, force=True, ignore_permissions=True)
	for name in demo_airline_names:
		frappe.delete_doc("Airline", name, force=True, ignore_permissions=True)
	for row in AIRPORTS:
		if frappe.db.exists("Airport", row["name"]):
			frappe.delete_doc("Airport", row["name"], force=True, ignore_permissions=True)
	frappe.db.commit()


def seed():
	_cleanup_partial_demo_if_needed()

	if frappe.db.exists("Airline", AIRLINES[0]["name"]):
		frappe.msgprint(
			_("Demo data already present (airline {0} exists).").format(AIRLINES[0]["name"]),
			indicator="orange",
		)
		return

	airline_names = []
	for row in AIRLINES:
		doc = frappe.get_doc({"doctype": "Airline", **row})
		doc.insert(ignore_permissions=True)
		airline_names.append(doc.name)

	airport_names = []
	for row in AIRPORTS:
		doc = frappe.get_doc({"doctype": "Airport", **row})
		doc.insert(ignore_permissions=True)
		airport_names.append(doc.name)

	airplanes: list[str] = []
	for airline in airline_names:
		for model in ("Nebula-200", "Comet-XL"):
			ap = frappe.get_doc(
				{
					"doctype": "Airplane",
					"airline": airline,
					"model": f"{model} {airline[:4]}",
					"capacity": AIRPLANE_CAPACITY,
				}
			)
			ap.insert(ignore_permissions=True)
			airplanes.append(ap.name)

	routes = [
		(airport_names[0], airport_names[1]),
		(airport_names[1], airport_names[2]),
		(airport_names[2], airport_names[0]),
		(airport_names[0], airport_names[2]),
	]

	flight_names: list[str] = []
	for airplane, (src, dst) in zip(airplanes, routes, strict=True):
		fl = frappe.get_doc(
			{
				"doctype": "Airplane Flight",
				"airplane": airplane,
				"source_airport": src,
				"destination_airport": dst,
				"date_of_departure": FLIGHT_DEPARTURE,
				"time_of_departure": FLIGHT_TIME,
				"duration": FLIGHT_DURATION_SECONDS,
			}
		)
		fl.insert(ignore_permissions=True)
		flight_names.append(fl.name)

	passenger_names: list[str] = []
	for first, last, dob in PASSENGERS:
		p = frappe.get_doc(
			{
				"doctype": "Flight Passenger",
				"first_name": first,
				"last_name": last,
				"date_of_birth": dob,
			}
		)
		p.insert(ignore_permissions=True)
		passenger_names.append(p.name)

	for flight_idx, flight in enumerate(flight_names):
		price = 100 + flight_idx * 25
		for passenger in passenger_names:
			t = frappe.get_doc(
				{
					"doctype": "Airplane Ticket",
					"passenger": passenger,
					"flight": flight,
					"flight_price": price,
					"status": "Booked",
				}
			)
			t.insert(ignore_permissions=True)

	submit_airline = airline_names[0]
	airplanes_submit = frappe.get_all(
		"Airplane",
		filters={"airline": submit_airline},
		pluck="name",
		order_by="creation asc",
	)
	flights_submit = frappe.get_all(
		"Airplane Flight",
		filters={"airplane": ("in", airplanes_submit)},
		pluck="name",
		order_by="creation asc",
	)
	tickets_submit = frappe.get_all(
		"Airplane Ticket",
		filters={"flight": ("in", flights_submit), "docstatus": 0},
		pluck="name",
	)

	for name in tickets_submit:
		ticket = frappe.get_doc("Airplane Ticket", name)
		ticket.status = "Boarded"
		ticket.save(ignore_permissions=True)

	for name in tickets_submit:
		ticket = frappe.get_doc("Airplane Ticket", name)
		ticket.submit()

	for name in flights_submit:
		frappe.get_doc("Airplane Flight", name).submit()

	frappe.db.commit()
	frappe.msgprint(
		_(
			"Created {0} airlines, {1} airports, {2} airplanes, {3} flights, {4} passengers, {5} tickets. "
			"Submitted flights and tickets for {6}; {7} remains draft."
		).format(
			len(AIRLINES),
			len(AIRPORTS),
			len(airplanes),
			len(flight_names),
			len(passenger_names),
			len(flight_names) * len(passenger_names),
			submit_airline,
			airline_names[1],
		),
		indicator="green",
	)
