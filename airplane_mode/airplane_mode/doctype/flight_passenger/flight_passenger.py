# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


def get_passenger_for_user(user: str | None = None) -> str | None:
	"""Return the **Flight Passenger** name linked to the given **User**, if any."""
	user = user or frappe.session.user
	if user == "Guest":
		return None
	return frappe.db.get_value("Flight Passenger", {"user": user}, "name")


class FlightPassenger(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		date_of_birth: DF.Date
		first_name: DF.Data
		full_name: DF.Data | None
		last_logged_in: DF.Datetime | None
		last_name: DF.Data | None
		managed_by: DF.Link | None
		name: DF.Int | None
		user: DF.Link
	# end: auto-generated types

	def before_save(self):
		self.full_name = self._make_full_name()

	def _make_full_name(self):
		first = (self.first_name or "").strip()
		last = (self.last_name or "").strip()
		if last:
			return f"{first} {last}".strip()
		return first
