# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

import frappe

from .airplane_ticket import generate_seat_assignment


def execute():
	for name in frappe.get_all(
		"Airplane Ticket",
		or_filters=[
			["seat", "is", "not set"],
			["seat", "=", ""],
		],
		pluck="name",
	):
		frappe.db.set_value(
			"Airplane Ticket",
			name,
			"seat",
			generate_seat_assignment(),
			update_modified=False,
		)
