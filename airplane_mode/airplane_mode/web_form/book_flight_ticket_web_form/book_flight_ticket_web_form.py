import random

import frappe
from frappe import _
from frappe.utils import flt, get_url

from airplane_mode.airplane_mode.doctype.airplane_ticket.airplane_ticket import (
	_passenger_ticket_scope_applies,
)
from airplane_mode.airplane_mode.doctype.flight_passenger.flight_passenger import (
	get_passenger_for_user,
)


def _passenger_display_name(passenger_id: str | None) -> str:
	if not passenger_id:
		return ""
	return (
		frappe.db.get_value("Flight Passenger", passenger_id, "full_name")
		or frappe.db.get_value("Flight Passenger", passenger_id, "first_name")
		or ""
	)


def get_context(context):
	# Existing saved response: keep server-loaded document
	if frappe.form_dict.get("name"):
		if frappe.db.exists("Airplane Ticket", frappe.form_dict.name):
			passenger = frappe.db.get_value("Airplane Ticket", frappe.form_dict.name, "passenger")
			context.reference_doc["passenger_display"] = _passenger_display_name(passenger)
		return None

	flight = frappe.form_dict.get("flight")
	if not flight or not frappe.db.exists("Airplane Flight", flight):
		return None

	passenger = get_passenger_for_user()
	if _passenger_ticket_scope_applies(frappe.session.user) and not passenger:
		frappe.throw(
			_("You need a passenger profile before booking. Register at {0} or ask an administrator.").format(
				get_url("/passenger-signup")
			),
			exc=frappe.PermissionError,
			title=_("Passenger profile required"),
		)

	context.no_cache = 1
	price = flt(random.randint(100, 10000))
	reference_doc: dict = {
		"doctype": "Airplane Ticket",
		"flight": flight,
		"flight_price": price,
	}

	if passenger:
		reference_doc["passenger"] = passenger
	reference_doc["passenger_display"] = _passenger_display_name(passenger) if passenger else ""

	# Hydrates `frappe.reference_doc` in web_form.html (defaults for new forms start as {}).
	context.reference_doc = reference_doc
