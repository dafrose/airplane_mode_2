# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Website API helpers (guest-safe passenger signup, etc.)."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.auth import CookieManager, LoginManager
from frappe.utils import cint, escape_html, getdate, validate_email_address

from airplane_mode.airplane_mode.doctype.airplane_flight.airplane_flight import (
	BOOK_FLIGHT_WEB_FORM_ROUTE,
)
from airplane_mode.passenger_portal_urls import PASSENGER_HOME_ROUTE

BOOK_TICKET_ROUTE = BOOK_FLIGHT_WEB_FORM_ROUTE


# Dedicated passenger signup; validates email/DOB, rate-limit at proxy if needed.
# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True, methods=["POST"])
def passenger_signup(
	email: str,
	password: str,
	first_name: str,
	last_name: str | None = None,
	date_of_birth: str | None = None,
):
	"""Create a **Website User** with the **Passenger** role, a **Flight Passenger** row, and a session.

	Intended for ``/passenger-signup`` when **Website Settings** sign up is off.
	The passenger profile Web Form is optional; sign up collects profile fields here.

	**Flight Passenger** is inserted **after** ``login_as`` so **Owner** is the new user (not
	**Guest**), which keeps Web Form Link/Autocomplete labels in sync with ``full_name``.
	"""
	email = (email or "").strip().lower()
	first_name = (first_name or "").strip()
	last_name = (last_name or "").strip() or None
	date_of_birth = (date_of_birth or "").strip()

	if not email or not password or not first_name or not date_of_birth:
		frappe.throw(
			_("Email, password, first name, and date of birth are required."),
			title=_("Missing information"),
		)

	validate_email_address(email, throw=True)

	if frappe.db.exists("User", email):
		frappe.throw(_("This email is already registered."), title=_("Sign up"))

	max_signups_allowed_per_hour = cint(frappe.get_system_settings("max_signups_allowed_per_hour") or 300)
	users_created_past_hour = frappe.db.get_creation_count("User", 60)
	if users_created_past_hour >= max_signups_allowed_per_hour:
		frappe.throw(
			_("Too many users signed up recently. Please try again later."),
			title=_("Temporarily disabled"),
		)

	dob = getdate(date_of_birth)

	user_doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": escape_html(first_name),
			"last_name": escape_html(last_name) if last_name else "",
			"enabled": 1,
			"send_welcome_email": 0,
			"user_type": "Website User",
			"new_password": password,
		}
	)
	user_doc.append("roles", {"role": "Passenger"})
	user_doc.flags.ignore_permissions = True

	try:
		user_doc.insert()
		if getattr(frappe.local, "cookie_manager", None) is None:
			frappe.local.cookie_manager = CookieManager()
		if getattr(frappe.local, "login_manager", None) is None:
			frappe.local.login_manager = LoginManager()
		frappe.local.login_manager.login_as(user_doc.name)
		frappe.get_doc(
			{
				"doctype": "Flight Passenger",
				"user": user_doc.name,
				"first_name": escape_html(first_name),
				"last_name": escape_html(last_name) if last_name else None,
				"date_of_birth": dob,
			}
		).insert(ignore_permissions=True)
	except Exception:
		name = getattr(user_doc, "name", None)
		if name:
			for pname in frappe.get_all("Flight Passenger", {"user": name}, pluck="name"):
				frappe.delete_doc("Flight Passenger", pname, force=True, ignore_permissions=True)
			if frappe.db.exists("User", name):
				frappe.delete_doc("User", name, ignore_permissions=True, force=True)
		raise

	return {
		"redirect_to": f"/{PASSENGER_HOME_ROUTE}",
	}


@frappe.whitelist()
def passenger_link_titles(passenger_ids):
	"""Map **Flight Passenger** id → display name for portal list cells.

	Only ids that appear on at least one **Airplane Ticket** the current user may read
	are returned.
	"""
	if isinstance(passenger_ids, str):
		passenger_ids = json.loads(passenger_ids)

	if not isinstance(passenger_ids, list):
		frappe.throw(_("Invalid request"))

	normalized = []
	for x in passenger_ids[:200]:
		if x is None or str(x).strip() == "":
			continue
		s = str(x).strip()
		if s not in normalized:
			normalized.append(s)

	if not normalized:
		return {}

	allowed = {
		str(x)
		for x in (
			frappe.get_all(
				"Airplane Ticket",
				filters={"passenger": ["in", normalized]},
				pluck="passenger",
			)
			or []
		)
		if x is not None
	}
	to_fetch = [p for p in normalized if p in allowed]
	if not to_fetch:
		return {}

	out = {}
	for row in frappe.get_all(
		"Flight Passenger",
		filters={"name": ["in", to_fetch]},
		fields=["name", "full_name", "first_name"],
		ignore_permissions=True,
	):
		out[str(row.name)] = (row.get("full_name") or row.get("first_name") or "").strip()

	return out
