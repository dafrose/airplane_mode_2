# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import get_url, now_datetime
from frappe.utils.data import quoted
from frappe.website.website_generator import WebsiteGenerator

# Must match Web Form > Route (see book_flight_ticket_web_form.json)
BOOK_FLIGHT_WEB_FORM_ROUTE = "book-flight-ticket-web-form"
# Must match DocType **Airplane Flight** > Route (Has Web View list URL)
FLIGHTS_WEB_ROUTE = "flights"

GATE_CHANGE_REALTIME_EVENT = "airplane_ticket_gate_change"
_GATE_BEFORE_SAVE_MISSING = object()


def sync_tickets_gate_for_flight(flight_name: str) -> None:
	"""Align **Airplane Ticket** *gate_number* with the flight; stamp *gate_number_changed_on*
	when a ticket value changes; notify the passenger *User* over realtime.
	"""
	# Do not check, if flight does not exist.
	# We do not want to fail silently.

	flight_gate = frappe.db.get_value("Airplane Flight", flight_name, "gate_number")

	def norm(g) -> str:
		return (g or "").strip()

	target = norm(flight_gate)

	tickets = frappe.get_all(
		"Airplane Ticket",
		filters=[
			["flight", "=", flight_name],
			["docstatus", "=", 0],  # only draft tickets
		],
		fields=["name", "gate_number", "passenger"],
	)

	for row in tickets:
		if norm(row.gate_number) == target:
			continue

		old_gate = row.gate_number

		frappe.db.set_value(
			"Airplane Ticket",
			row.name,
			{
				"gate_number": flight_gate,
				"gate_number_changed_on": now_datetime(),
			},
			update_modified=False,
		)

		user = frappe.db.get_value("Flight Passenger", row.passenger, "user")
		# assume user exists. We do not want to fail silently.

		view_path = f"/app/Form/{quote('Airplane Ticket')}/{quote(row.name)}"
		frappe.publish_realtime(
			event=GATE_CHANGE_REALTIME_EVENT,
			message={
				"ticket": row.name,
				"flight": flight_name,
				"old_gate": old_gate,
				"new_gate": flight_gate,
				"view_ticket_url": get_url(view_path),
			},
			user=user,
		)


class AirplaneFlight(WebsiteGenerator):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from airplane_mode.airplane_mode.doctype.flight_crew_member.flight_crew_member import (
			FlightCrewMember,
		)

		airplane: DF.Link
		amended_from: DF.Link | None
		date_of_departure: DF.Date
		destination_airport: DF.Link
		destination_airport_code: DF.Data | None
		duration: DF.Duration
		flight_crew: DF.Table[FlightCrewMember]
		gate_number: DF.Data | None
		is_published: DF.Check
		route: DF.Data | None
		source_airport: DF.Link
		source_airport_code: DF.Data | None
		status: DF.Literal["Scheduled", "Completed", "Cancelled"]
		time_of_departure: DF.Time
	# end: auto-generated types

	def get_context(self, context):
		airline = frappe.db.get_value("Airplane", self.airplane, "airline")
		context.title = f"{airline} — {self.source_airport_code} → {self.destination_airport_code}"
		context.book_flight_url = f"/{BOOK_FLIGHT_WEB_FORM_ROUTE}/new?flight={quoted(self.name)}"
		return context

	def before_save(self):
		if self.is_new():
			self._gate_number_before_save = None
		else:
			self._gate_number_before_save = frappe.db.get_value("Airplane Flight", self.name, "gate_number")

	def on_update(self):
		prev = getattr(self, "_gate_number_before_save", _GATE_BEFORE_SAVE_MISSING)
		if prev is _GATE_BEFORE_SAVE_MISSING:
			return
		before = prev or ""
		after = self.gate_number or ""
		if before == after:
			return

		frappe.enqueue(
			"airplane_mode.airplane_mode.doctype.airplane_flight.airplane_flight.sync_tickets_gate_for_flight",
			queue="default",
			job_name=f"flight_gate_sync|{self.name}",
			flight_name=self.name,
		)

	def on_submit(self):
		self.db_set("status", "Completed")


def get_list_context(context):
	meta = frappe.get_meta("Airplane Flight")
	context.title = _("Flights")
	context.order_by = "date_of_departure asc, time_of_departure asc"
	context.hide_filters = False
	tpl = meta.get_list_template() or "templates/includes/list/list.html"
	context.template = tpl
	context.list_template = tpl
	return context
