# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

import random

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


def generate_seat_assignment() -> str:
	return f"{random.randint(1, 99)}{random.choice('ABCDE')}"


def _passenger_ticket_scope_applies(user: str) -> bool:
	"""True when *user* is **Passenger**-scoped for tickets (not **System Manager**)."""
	if not user or user == "Guest":
		return False
	if "System Manager" in frappe.get_roles(user):
		return False
	return "Passenger" in frappe.get_roles(user)


def get_permission_query_conditions(user: str | None = None) -> str:
	"""Restrict **Airplane Ticket** list/API rows for portal passengers (hooks)."""
	user = user or frappe.session.user
	if not _passenger_ticket_scope_applies(user):
		return ""
	user_sql = frappe.db.escape(user, percent=False)
	return f"""EXISTS (
		SELECT 1 FROM `tabFlight Passenger` `fp`
		WHERE `fp`.`name` = `tabAirplane Ticket`.`passenger`
		AND `fp`.`user` = {user_sql}
	)"""


def has_airplane_ticket_doc_permission(doc, ptype="read", user=None, debug=False):
	"""Hook: deny **Passenger**-role users access to tickets that are not theirs."""
	user = user or frappe.session.user
	if not _passenger_ticket_scope_applies(user):
		return None
	linked_user = frappe.db.get_value("Flight Passenger", doc.get("passenger"), "user")
	if linked_user != user:
		return False
	return None


class AirplaneTicket(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from airplane_mode.airplane_mode.doctype.airplane_ticket_add_on_item.airplane_ticket_add_on_item import (
			AirplaneTicketAddonItem,
		)

		add_ons: DF.Table[AirplaneTicketAddonItem]
		amended_from: DF.Link | None
		departure_date: DF.Date
		departure_time: DF.Time
		destination_airport_code: DF.ReadOnly
		duration_of_flight: DF.Duration
		flight: DF.Link
		flight_price: DF.Currency
		gate_number: DF.ReadOnly | None
		gate_number_changed_on: DF.Datetime | None
		passenger: DF.Link
		seat: DF.Data | None
		source_airport_code: DF.ReadOnly
		status: DF.Literal["Booked", "Checked-In", "Boarded"]
		total_amount: DF.Currency
	# end: auto-generated types

	def before_insert(self):
		if not self.seat:
			self.seat = generate_seat_assignment()

	def validate(self):
		if self.flight:
			flight_gate = frappe.db.get_value("Airplane Flight", self.flight, "gate_number")
			if flight_gate and not self.get("gate_number"):
				self.gate_number = flight_gate
			if flt(self.flight_price) <= 0:
				self.flight_price = flt(random.randint(100, 10000))
		self._dedupe_add_ons()
		self._validate_passenger_matches_portal_user()
		self._validate_flight_capacity()
		addon_total = sum(flt(row.amount) for row in self.add_ons)
		self.total_amount = flt(self.flight_price) + addon_total

	def on_submit(self):
		if self.status != "Boarded":
			frappe.throw(
				_("Only tickets with status {0} can be submitted.").format(frappe.bold("Boarded")),
				title=_("Cannot Submit"),
			)

	def _validate_passenger_matches_portal_user(self):
		if not self.passenger or not _passenger_ticket_scope_applies(frappe.session.user):
			return
		linked_user = frappe.db.get_value("Flight Passenger", self.passenger, "user")
		if linked_user != frappe.session.user:
			frappe.throw(
				_("You can only book tickets for your own passenger profile."),
				title=_("Invalid passenger"),
			)

	def _validate_flight_capacity(self):
		airplane = frappe.db.get_value("Airplane Flight", self.flight, "airplane")
		capacity = cint(frappe.db.get_value("Airplane", airplane, "capacity"))

		filters = {"flight": self.flight, "docstatus": ("!=", 2)}
		if not self.is_new():
			filters["name"] = ("!=", self.name)

		existing = frappe.db.count("Airplane Ticket", filters)
		if existing >= capacity:
			frappe.throw(
				_(
					"This flight is fully booked. The airplane has {0} seat(s), and there are already {1} ticket(s) booked for this flight."
				).format(capacity, existing),
				title=_("Flight full"),
			)

	def _dedupe_add_ons(self):
		"""Remove duplicate add-ons from the list."""
		if not self.add_ons:
			return

		seen = set()
		rows_to_remove = []
		for row in self.add_ons:
			if row.item in seen:
				rows_to_remove.append(row)
			else:
				seen.add(row.item)

		if not rows_to_remove:
			return

		for row in rows_to_remove:
			self.remove(row)

		frappe.msgprint(
			_("Removed {0} duplicate add-on row(s). Each add-on type can only appear once.").format(
				len(rows_to_remove)
			),
			title=_("Duplicate add-ons"),
			indicator="orange",
			alert=True,
		)
