# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Install hooks for airplane_mode.

`before_tests` runs once before the test runner starts. We use it to make
sure roles + test users exist so permission tests are deterministic and
don't depend on hand-clicking through the Desk UI on every fresh site.
"""

from __future__ import annotations

import frappe

REQUIRED_ROLES = (
	"Airport Authority Personnel",
	"Fleet Manager",
	"Travel Agent",
	"Flight Crew Member",
	"Passenger",
	"Shop Tenant",
	"Airport Shop Manager",
)

TEST_USERS: dict[str, tuple[str, ...]] = {
	"travel_agent_a@airplane.test": ("Travel Agent",),
	"travel_agent_b@airplane.test": ("Travel Agent",),
	# **Shop Tenant** role is assigned only when linked from **Shop Tenant** `user` (see `ShopTenant` hooks).
	"shop_tenant_a@airplane.test": (),
	"shop_tenant_b@airplane.test": (),
}


def after_install():
	_ensure_roles()
	frappe.db.commit()


def before_tests():
	_ensure_roles()
	_ensure_test_users()
	frappe.db.commit()


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


def _ensure_test_users() -> None:
	for email, roles in TEST_USERS.items():
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": email.split("@", 1)[0],
					"send_welcome_email": 0,
					"new_password": "Password123!",
				}
			).insert(ignore_permissions=True)

		existing = {r.role for r in user.get("roles", [])}
		missing = [r for r in roles if r not in existing]
		if missing:
			for role in missing:
				user.append("roles", {"role": role})
			user.save(ignore_permissions=True)

		# **Shop Tenant** role is granted from **Shop Tenant** `user` link only — strip stale role from older test DBs.
		if email.startswith("shop_tenant_") and email.endswith("@airplane.test"):
			user.reload()
			if "Shop Tenant" in {r.role for r in user.roles}:
				user.remove_roles("Shop Tenant")
			for up in frappe.get_all(
				"User Permission",
				filters={"user": email, "allow": "Shop Tenant"},
				pluck="name",
			):
				frappe.delete_doc("User Permission", up, ignore_permissions=True, force=True)
