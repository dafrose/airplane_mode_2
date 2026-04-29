# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Portal-only **Notification Log** helpers (hide from website without deleting rows).

Updates use :func:`frappe.db.set_value` (same idea as core **mark_as_read** on this DocType),
after scoping rows with :func:`frappe.get_list` / ``db.exists`` so only the session user's
rows are touched — not ``get_doc`` + ``save()``, which is brittle here (**Notification Log**
is ``in_create`` and similar patterns in core use direct DB updates).
"""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def get_portal_notification_logs(limit: int = 30):
	"""Return **Notification Log** rows for the current user that are not portal-dismissed."""
	if frappe.session.user == "Guest":
		return {"notification_logs": [], "user_info": {}}

	limit = max(1, min(int(limit or 30), 100))
	logs = frappe.get_all(
		"Notification Log",
		filters={
			"for_user": frappe.session.user,
			"hidden_from_portal": 0,
		},
		fields=["*"],
		limit_page_length=limit,
		order_by="modified desc",
	)
	return {"notification_logs": logs, "user_info": {}}


@frappe.whitelist()
def hide_portal_notification(docname: str):
	"""Set *Hidden from portal* for one row owned by the session user."""
	if frappe.session.user == "Guest":
		frappe.throw(_("You must be logged in."), exc=frappe.PermissionError)

	if not docname or not frappe.db.exists(
		"Notification Log",
		{"name": str(docname), "for_user": frappe.session.user},
	):
		frappe.throw(_("Not found"), exc=frappe.PermissionError)

	frappe.db.set_value(
		"Notification Log",
		str(docname),
		"hidden_from_portal",
		1,
		update_modified=False,
	)


@frappe.whitelist()
def hide_all_portal_notifications():
	"""Hide every portal-visible **Notification Log** for the current user."""
	if frappe.session.user == "Guest":
		return

	names = frappe.get_list(
		"Notification Log",
		filters={
			"for_user": frappe.session.user,
			"hidden_from_portal": 0,
		},
		pluck="name",
		limit_page_length=500,
	)
	for name in names:
		frappe.db.set_value(
			"Notification Log",
			name,
			"hidden_from_portal",
			1,
			update_modified=False,
		)
