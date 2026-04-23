# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Background and scheduled tasks for **Airport Shops**."""

from __future__ import annotations

from datetime import date, timedelta

import frappe
from dateutil.relativedelta import relativedelta
from frappe.utils import getdate, today


def create_due_shop_rent_payments() -> None:
	"""Create **Shop Rent Payment** rows when due (see issue #8).

	Uses **Shop Lease Contract** *Next Due Date* (always set after install patch + `before_insert`
	on new leases). Each period is one month; the next period starts the day after *Period End*.
	*Next Due Date* is advanced on each payment `insert` (**Shop Rent Payment.after_insert**); when
	the `while` loop finishes without `break`, this task runs one more `set_value` as a safeguard.
	While **Airport Shop Settings**
	*Enable Rent Reminders* is off, this function returns immediately.
	"""
	if not frappe.db.get_single_value("Airport Shop Settings", "enable_rent_reminders"):
		return

	today_d = getdate(today())
	leases = frappe.get_all(
		"Shop Lease Contract",
		fields=[
			"name",
			"rent",
			"lease_start_date",
			"lease_expiry_date",
			"next_due_date",
		],
	)

	for lease_row in leases:
		# Assume next_due_date always exists. If not, do not fail silently.

		lease_start = getdate(lease_row.lease_start_date)
		if today_d < lease_start:
			continue

		expiry = getdate(lease_row.lease_expiry_date) if lease_row.lease_expiry_date else None
		next_period_start = getdate(lease_row.next_due_date)

		while next_period_start <= today_d:
			if expiry and next_period_start > expiry:
				break

			period_end = next_period_start + relativedelta(months=1) - timedelta(days=1)
			following_period_start = period_end + timedelta(days=1)

			if _shop_rent_payment_exists(lease_row.name, next_period_start):
				frappe.db.set_value(
					"Shop Lease Contract",
					lease_row.name,
					"next_due_date",
					following_period_start,
				)
				next_period_start = following_period_start
				continue

			frappe.get_doc(
				{
					"doctype": "Shop Rent Payment",
					"lease_contract": lease_row.name,
					"amount_due": lease_row.rent,
					"period_start": next_period_start,
					"period_end": period_end,
				}
			).insert()
			next_period_start = following_period_start

		else:
			# Python `while`/`else`: this block runs once when the loop stops because
			# `next_period_start > today_d` — not each iteration, and not after `break`
			# (expiry). It realigns *Next Due Date* with the in-memory cursor as a safeguard
			# if payment `insert` / `after_insert` ever got out of sync.
			frappe.db.set_value(
				"Shop Lease Contract",
				lease_row.name,
				"next_due_date",
				next_period_start,
			)


def _shop_rent_payment_exists(lease_contract: str, period_start: date) -> bool:
	"""True if a non-cancelled **Shop Rent Payment** already covers this lease period."""
	rows = frappe.get_all(
		"Shop Rent Payment",
		filters={
			"lease_contract": lease_contract,
			"period_start": period_start,
			"docstatus": ["!=", 2],
		},
		pluck="name",
		limit=1,
	)
	return bool(rows)
