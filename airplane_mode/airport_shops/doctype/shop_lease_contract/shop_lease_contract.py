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
		public_shop_name: DF.Data | None
		rent: DF.Currency
		shop: DF.Link
		tenant: DF.Link
	# end: auto-generated types

	def before_save(self):
		if self.has_value_changed("lease_start_date"):
			self.next_due_date = self.lease_start_date

	def after_insert(self):
		self._sync_shop_status_for_lease_dates()

	def on_update(self):
		if self.has_value_changed("lease_start_date") or self.has_value_changed("lease_expiry_date"):
			self._sync_shop_status_for_lease_dates()

	def on_trash(self):
		recalculate_shop_status_from_leases(self.shop, ignore_contract=self.name)

	def _sync_shop_status_for_lease_dates(self) -> None:
		if _lease_row_covers_today(self):
			frappe.db.set_value("Shop", self.shop, "status", "Occupied", update_modified=False)
		else:
			_enqueue_recalculate_shop_status(self.shop)


def _lease_row_covers_today(doc: Document) -> bool:
	today_date = getdate(today())
	if doc.lease_expiry_date:
		return getdate(doc.lease_start_date) <= today_date < getdate(doc.lease_expiry_date)
	else:
		return getdate(doc.lease_start_date) <= today_date


def _enqueue_recalculate_shop_status(shop: str) -> None:
	method = "airplane_mode.airport_shops.doctype.shop_lease_contract.shop_lease_contract.recalculate_shop_status_from_leases"
	if frappe.flags.in_test:
		recalculate_shop_status_from_leases(shop)
		return
	frappe.enqueue(
		method,
		queue="default",
		job_name=f"recalculate_shop_status|{shop}",
		shop=shop,
	)


def recalculate_shop_status_from_leases(shop: str, ignore_contract: str | None = None) -> None:
	has_active_lease = False
	for row in frappe.get_all(
		"Shop Lease Contract",
		filters={"shop": shop},
		pluck="name",
	):
		if ignore_contract and row == ignore_contract:
			continue

		lease = frappe.get_doc("Shop Lease Contract", row)
		if _lease_row_covers_today(lease):
			has_active_lease = True
			break
	frappe.db.set_value(
		"Shop",
		shop,
		"status",
		"Occupied" if has_active_lease else "Available",
		update_modified=False,
	)
