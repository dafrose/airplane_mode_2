# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class ShopRentPayment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		address: DF.SmallText | None
		airport_code: DF.Data | None
		amended_from: DF.Link | None
		amount_due: DF.Currency
		date_paid: DF.Date | None
		date_posted: DF.Date | None
		lease_contract: DF.Link
		period_end: DF.Date
		period_start: DF.Date
		status: DF.Literal["Due", "Paid"]
		tenant: DF.Link | None
		tenant_email: DF.Data | None
	# end: auto-generated types

	def after_insert(self):
		if self.lease_contract and self.period_end:
			following = getdate(self.period_end) + timedelta(days=1)
			frappe.db.set_value(
				"Shop Lease Contract",
				self.lease_contract,
				"next_due_date",
				following,
			)

	def before_submit(self):
		self.status = "Paid"
		if not self.date_paid:
			self.date_paid = nowdate()

	def before_cancel(self):
		self.status = "Due"
		self.date_paid = None
