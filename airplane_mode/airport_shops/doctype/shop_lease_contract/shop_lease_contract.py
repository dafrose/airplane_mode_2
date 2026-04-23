# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from frappe.model.document import Document


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
