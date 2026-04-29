# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Colocated context for ``www/passenger-signup.html``.

Frappe resolves the module name by replacing hyphens with underscores in the page
basename, so this file must be ``passenger_signup.py``, not ``passenger-signup.py``.
"""

import frappe

from airplane_mode.airplane_mode.doctype.flight_passenger.flight_passenger import (
	get_passenger_for_user,
)


def get_context(context):
	context.no_cache = 1
	context.is_guest = frappe.session.user == "Guest"
	if not context.is_guest:
		context.has_passenger_profile = bool(get_passenger_for_user())
