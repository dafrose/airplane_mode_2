# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Install hooks for airplane_mode.

`before_tests` ensures app roles and custom fields so tests are deterministic.
Shared @airplane.test users and ``_TST`` / ``_TXY`` airports are *not* created
here; use `airplane_mode.tests.helpers` on demand (cleaned up at test process
exit).
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

REQUIRED_ROLES = (
	"Airport Authority Personnel",
	"Fleet Manager",
	"Travel Agent",
	"Flight Crew Member",
	"Passenger",
	"Shop Tenant",
	"Airport Shop Manager",
)


def after_install():
	_ensure_roles()
	_ensure_notification_log_portal_hidden_field()
	frappe.db.commit()


def before_tests():
	_ensure_roles()
	_ensure_notification_log_portal_hidden_field()
	frappe.db.commit()


def _ensure_notification_log_portal_hidden_field() -> None:
	"""Add *Hidden from portal* on **Notification Log** (Custom Field, not core JSON)."""
	create_custom_fields(
		{
			"Notification Log": [
				{
					"fieldname": "hidden_from_portal",
					"fieldtype": "Check",
					"label": "Hidden from portal",
					"default": "0",
					"insert_after": "read",
					"read_only": 0,
					"description": "Dismissed from the website bell; row kept for Desk.",
				}
			]
		}
	)


def _ensure_roles() -> None:
	for role_name in REQUIRED_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		desk_access = 0 if role_name == "Passenger" else 1
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": desk_access,
			}
		).insert(ignore_permissions=True)
