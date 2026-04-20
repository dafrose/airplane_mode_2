# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.data import quoted
from frappe.website.website_generator import WebsiteGenerator

# Must match Web Form > Route (see book_flight_ticket_web_form.json)
BOOK_FLIGHT_WEB_FORM_ROUTE = "book-flight-ticket-web-form"
# Must match DocType **Airplane Flight** > Route (Has Web View list URL)
FLIGHTS_WEB_ROUTE = "flights"


class AirplaneFlight(WebsiteGenerator):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		airplane: DF.Link
		amended_from: DF.Link | None
		date_of_departure: DF.Date
		destination_airport: DF.Link
		destination_airport_code: DF.Data | None
		duration: DF.Duration
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
