# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class ShopLeaseContract(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		airport_code: DF.Data | None
		lease_expiry_date: DF.Date | None
		lease_start_date: DF.Date
		next_due_date: DF.Date | None
		rent: DF.Currency
		shop: DF.Link
		tenant: DF.Link
	# end: auto-generated types

	def before_insert(self):
		# First row only: *Lease Start Date* is mandatory; *Next Due Date* seeds the rolling schedule.
		self.next_due_date = self.lease_start_date

	def validate(self):
		# Set shop status to Occupied when contract is created
		# Shop is mandatory, do not check for existence
		status = self._shop_status_from_lease()
		frappe.db.set_value("Shop", self.shop, "status", status, update_modified=False)

	def on_trash(self):
		# Set shop status to Available when contract is deleted
		# Shop is mandatory, do not check for existence
		frappe.db.set_value("Shop", self.shop, "status", "Available", update_modified=False)

	def _shop_status_from_lease(self) -> str:
		lease_expired = self.lease_expiry_date and getdate(self.lease_expiry_date) <= getdate(today())
		return "Available" if lease_expired else "Occupied"
