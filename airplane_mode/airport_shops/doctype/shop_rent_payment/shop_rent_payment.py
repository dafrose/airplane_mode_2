# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate
from frappe.utils.file_manager import save_file

# Keep aligned with the **Print Format** chosen on the Desk **Notification** (Submit, attach print).
PAYMENT_RECEIPT_PRINT_FORMAT = "Payment Receipt Format"


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

	def on_submit(self):
		"""Persist receipt PDF on the payment (**File** on this doc → timeline / attachments).

		Desk **Notification** “Attach Print” only passes PDF into outbound email; it does not
		attach to the source document.
		"""
		printed = frappe.attach_print(
			self.doctype,
			self.name,
			file_name=f"{self.name}-receipt",
			print_format=PAYMENT_RECEIPT_PRINT_FORMAT,
			doc=self,
		)
		# `printview` sets **in_print** on the `doc` passed into `get_print`; if left set, later
		# `save()` / **Cancel** no-ops at the top of `_save` (`if self.flags.in_print: return`).
		self.flags.in_print = False

		if frappe.db.exists(
			"File",
			{
				"attached_to_doctype": self.doctype,
				"attached_to_name": self.name,
				"file_name": printed["fname"],
			},
		):
			return

		save_file(
			printed["fname"],
			printed["fcontent"],
			self.doctype,
			self.name,
			is_private=1,
		)
		self.db_set(
			"modified",
			frappe.db.get_value(self.doctype, self.name, "modified"),
			update_modified=False,
		)

	def before_cancel(self):
		self.status = "Due"
		self.date_paid = None
