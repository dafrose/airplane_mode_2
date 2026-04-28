import frappe

from airplane_mode.passenger_portal_urls import apply_passenger_web_form_template


def get_context(context):
	apply_passenger_web_form_template(context)
	# Existing document: `load_form_data` already set `reference_doc`
	if frappe.form_dict.get("name"):
		return None

	if frappe.session.user == "Guest":
		return None

	context.no_cache = 1
	return {
		"reference_doc": {
			"doctype": "Flight Passenger",
			"user": frappe.session.user,
		}
	}
