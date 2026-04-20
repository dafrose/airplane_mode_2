# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Create **User** accounts for **Flight Passenger** rows without a linked `user`.

Each new account is a **Website User** with the **Passenger** role. Email addresses
are synthetic and unique: ``passenger+{passenger_name}@{email_domain}``.

Run (from bench directory), e.g.::

	bench --site <site> execute airplane_mode.backfill_passenger_users.run

Dry run (no inserts)::

	bench --site <site> execute airplane_mode.backfill_passenger_users.run \\
		--kwargs "{'dry_run': True}"

Custom password / domain::

	bench --site <site> execute airplane_mode.backfill_passenger_users.run \\
		--kwargs "{'default_password': 'YourTempPass!', 'email_domain': 'example.invalid'}"
"""

from __future__ import annotations

import frappe


def _ensure_passenger_role() -> None:
	if frappe.db.exists("Role", "Passenger"):
		return
	frappe.get_doc({"doctype": "Role", "role_name": "Passenger", "desk_access": 0}).insert(
		ignore_permissions=True
	)


def _passengers_missing_user() -> list[str]:
	"""Names of **Flight Passenger** rows with no linked **User** (`user` empty or null)."""
	return frappe.db.sql(
		"""
		select name from `tabFlight Passenger`
		where ifnull(`user`, '') = ''
		""",
		pluck=True,
	)


def run(
	dry_run: bool = False,
	default_password: str = "PassengerBackfill1!",
	email_domain: str = "passenger.airplane-mode.local",
) -> dict:
	"""Link a new **Website User** to every **Flight Passenger** with no `user`.

	Run as **Administrator** (e.g. ``bench execute``). Returns a small report dict.
	"""
	_ensure_passenger_role()

	names = _passengers_missing_user()
	created: list[str] = []
	skipped: list[str] = []

	if not names:
		return {"dry_run": dry_run, "missing_before": 0, "created": [], "skipped": []}

	if dry_run:
		return {
			"dry_run": True,
			"missing_before": len(names),
			"would_create_for": names,
			"created": [],
			"skipped": [],
		}

	for pname in names:
		passenger = frappe.get_doc("Flight Passenger", pname)
		if passenger.get("user"):
			skipped.append(pname)
			continue

		email = f"passenger+{pname}@{email_domain}"
		if frappe.db.exists("User", email):
			skipped.append(pname)
			frappe.log_error(
				title="backfill_passenger_users: email collision",
				message=f"Flight Passenger {pname}: User {email} already exists; skipped.",
			)
			continue

		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": passenger.first_name or "Passenger",
				"last_name": passenger.last_name or "",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
				"new_password": default_password,
			}
		)
		user.append("roles", {"role": "Passenger"})
		user.insert(ignore_permissions=True)

		passenger.db_set("user", user.name, update_modified=False)
		created.append(email)

	frappe.db.commit()
	return {
		"dry_run": False,
		"missing_before": len(names),
		"created": created,
		"skipped": skipped,
	}
