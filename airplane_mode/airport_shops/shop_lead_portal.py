# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Public Picnic portal API for **Shop Lead** (no **Web Form** UI)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cstr, getdate


@frappe.whitelist(allow_guest=True)
def submit_shop_lead(
	shop: str,
	first_name: str,
	last_name: str,
	email: str | None = None,
	phone: str | None = None,
	projected_start_date: str | None = None,
):
	"""Create a **Shop Lead** for a *published* **Shop** (portal-only validation)."""
	from airplane_mode.airport_shops.shops_portal_context import is_shop_portal_visible

	shop = cstr(shop).strip()
	first_name = cstr(first_name).strip()
	last_name = cstr(last_name).strip()
	email = cstr(email).strip() or None
	phone = cstr(phone).strip() or None

	if not shop or not is_shop_portal_visible(shop):
		frappe.throw(_("This shop is not available for enquiries."), frappe.ValidationError)

	if not first_name or not last_name:
		frappe.throw(_("First name and last name are required."), frappe.ValidationError)

	if not email and not phone:
		frappe.throw(
			_("Please provide an email address or a phone number."),
			frappe.ValidationError,
		)

	psd = None
	if projected_start_date:
		psd = getdate(projected_start_date)

	doc = frappe.get_doc(
		{
			"doctype": "Shop Lead",
			"shop": shop,
			"first_name": first_name,
			"last_name": last_name,
			"email": email,
			"phone": phone,
			"projected_start_date": psd,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert()
	doc.flags.ignore_permissions = False

	return {"name": doc.name, "doctype": doc.doctype}
