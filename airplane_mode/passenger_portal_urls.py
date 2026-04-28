# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Shared routes and helpers for the passenger website shell."""

from __future__ import annotations

import frappe

from airplane_mode.airplane_mode.doctype.airplane_flight.airplane_flight import (
	BOOK_FLIGHT_WEB_FORM_ROUTE,
	FLIGHTS_WEB_ROUTE,
)

PASSENGER_HOME_ROUTE = "passenger-home"
COMPLETE_PASSENGER_PROFILE_ROUTE = "complete-passenger-profile"
PASSENGER_SIGNUP_ROUTE = "passenger-signup"


def passenger_portal_links():
	"""Return passenger links (relative paths, leading ``/``). Callable from Jinja."""

	return {
		"home": f"/{PASSENGER_HOME_ROUTE}",
		"flights": f"/{FLIGHTS_WEB_ROUTE}",
		"book_new": f"/{BOOK_FLIGHT_WEB_FORM_ROUTE}/new",
		"book_list": f"/{BOOK_FLIGHT_WEB_FORM_ROUTE}/list",
		"profile": f"/{COMPLETE_PASSENGER_PROFILE_ROUTE}",
		"signup": f"/{PASSENGER_SIGNUP_ROUTE}",
		"login": "/login",
		"logout": "/login?cmd=logout",
	}


def apply_passenger_web_form_template(context) -> None:
	"""Use the portal shell for flight-related **Web Form** pages (any logged-in user).
	Sets ``context.template`` to the appropriate template.
	"""
	if frappe.session.user == "Guest":
		return
	# Web Form list view vs single-document view — different base templates.
	if getattr(context, "is_list", False):
		context.template = "passenger_shell_web_list.html"
	else:
		context.template = "passenger_shell_web_form.html"
