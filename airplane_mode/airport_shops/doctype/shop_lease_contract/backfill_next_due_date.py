# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Patch: seed **Next Due Date** on legacy **Shop Lease Contract** rows."""

import frappe


def execute():
	frappe.db.sql(
		"""
		update `tabShop Lease Contract`
		set next_due_date = lease_start_date
		where ifnull(next_due_date, '') = '' and lease_start_date is not null
		"""
	)
