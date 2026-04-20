# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Create **User** accounts for **Flight Passenger** rows without a linked `user`,
and align **Owner** with the linked **User** for portal permissions (Web Form links).

Each new account is a **Website User** with the **Passenger** role. Email addresses
are synthetic and unique: ``passenger+{passenger_name}@{email_domain}``.

Run (from bench directory), e.g.::

	bench --site <site> execute airplane_mode.backfill_passenger_users.run

Dry run (no inserts)::

	bench --site <site> execute airplane_mode.backfill_passenger_users.run \\
		--kwargs "{'dry_run': True}"

Sync **Owner** only (no new users)::

	bench --site <site> execute airplane_mode.backfill_passenger_users.sync_passenger_owners

Dry run (owner sync preview)::

	bench --site <site> execute airplane_mode.backfill_passenger_users.sync_passenger_owners \\
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


def _passengers_with_owner_mismatch() -> list[tuple[str, str]]:
	"""``(name, user)`` for rows where **Owner** is not the linked **User**."""
	return frappe.db.sql(
		"""
		select name, `user` from `tabFlight Passenger`
		where ifnull(`user`, '') != ''
		and ifnull(`owner`, '') != `user`
		""",
	)


def sync_passenger_owners(dry_run: bool = False) -> dict:
	"""Set **Owner** on **Flight Passenger** to the linked **User** when they differ.

	Use after fixing ``user`` links or to repair rows created while **Guest** was the session
	(so **Owner** was wrong for ``if_owner`` / Web Form autocomplete labels).

	Returns ``{"synced": [...], "skipped": [...]}`` where ``skipped`` entries are
	``{"passenger": name, "user": value, "reason": "..."}``.
	"""
	synced: list[str] = []
	skipped: list[dict[str, str]] = []

	for pname, user in _passengers_with_owner_mismatch():
		if not frappe.db.exists("User", user):
			skipped.append(
				{"passenger": pname, "user": user, "reason": "linked_user_missing"},
			)
			continue
		if dry_run:
			synced.append(pname)
			continue
		frappe.db.set_value("Flight Passenger", pname, "owner", user, update_modified=False)
		synced.append(pname)

	if not dry_run:
		frappe.db.commit()

	return {"ownership_synced": synced, "ownership_skipped": skipped}


def run(
	dry_run: bool = False,
	default_password: str = "PassengerBackfill1!",
	email_domain: str = "passenger.airplane-mode.local",
) -> dict:
	"""Link a new **Website User** to every **Flight Passenger** with no `user`, then sync **Owner**.

	Run as **Administrator** (e.g. ``bench execute``). Returns a small report dict.
	"""
	_ensure_passenger_role()

	names = _passengers_missing_user()
	owner_rows = _passengers_with_owner_mismatch()

	if dry_run:
		return {
			"dry_run": True,
			"missing_before": len(names),
			"would_create_for": list(names),
			"ownership_mismatch_before": len(owner_rows),
			"would_sync_owner_for": [r[0] for r in owner_rows],
		}

	created: list[str] = []
	skipped: list[str] = []

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

	owner_report = sync_passenger_owners(dry_run=False)

	return {
		"dry_run": False,
		"missing_before": len(names),
		"created": created,
		"skipped": skipped,
		**owner_report,
	}
