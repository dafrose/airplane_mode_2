import random

import frappe


def get_context(context):
	# Existing saved response: keep server-loaded document
	if frappe.form_dict.get("name"):
		return None

	flight = frappe.form_dict.get("flight")
	if not flight or not frappe.db.exists("Airplane Flight", flight):
		return None

	context.no_cache = 1
	price = random.randint(100, 10000)
	return {
		"reference_doc": {
			"doctype": "Airplane Ticket",
			"flight": flight,
			"flight_price": price,
		}
	}
