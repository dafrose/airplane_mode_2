# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Context for ``www/passenger-home.html`` (passenger dashboard)."""

import frappe
from frappe.utils import format_date, format_time

from airplane_mode.airplane_mode.doctype.airplane_flight.airplane_flight import (
	get_airplane_ticket_portal_url,
)
from airplane_mode.airplane_mode.doctype.flight_passenger.flight_passenger import (
	get_passenger_for_user,
)
from airplane_mode.passenger_portal_urls import PASSENGER_HOME_ROUTE


def get_context(context):
	context.no_cache = 1
	if frappe.session.user == "Guest":
		frappe.redirect(f"/login?redirect-to=/{PASSENGER_HOME_ROUTE}")

	if not get_passenger_for_user():
		context.missing_profile = True
		context.tickets = []
		return context

	context.missing_profile = False
	rows = frappe.get_all(
		"Airplane Ticket",
		filters={"docstatus": 0},
		fields=["name", "flight", "status", "gate_number"],
		order_by="modified desc",
		limit=50,
	)
	flight_ids = list({x.flight for x in rows if x.flight})
	flights = {}
	if flight_ids:
		flights = {
			r.name: r
			for r in frappe.get_all(
				"Airplane Flight",
				filters={"name": ["in", flight_ids]},
				fields=[
					"name",
					"source_airport_code",
					"destination_airport_code",
					"date_of_departure",
					"time_of_departure",
				],
			)
		}
	for row in rows:
		row.ticket_url = get_airplane_ticket_portal_url(row.name)
		f = flights.get(row.flight)
		if f:
			src = f.source_airport_code or ""
			dst = f.destination_airport_code or ""
			row.flight_label = f"{src} → {dst}"
			parts = []
			if f.date_of_departure:
				parts.append(format_date(f.date_of_departure))
			if f.time_of_departure:
				parts.append(format_time(f.time_of_departure))
			row.departure = " ".join(parts)
		else:
			row.flight_label = row.flight or ""
			row.departure = ""
	context.tickets = rows
	return context
