# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Shared helpers for Picnic shop portal pages (used from multiple **www** modules)."""

from __future__ import annotations

import frappe
from frappe.utils import get_url


def picnic_stylesheet_url() -> str:
	return get_url("/assets/airplane_mode/css/picnic.min.css")


def is_shop_portal_visible(shop_name: str) -> bool:
	if not shop_name or not frappe.db.exists("Shop", shop_name):
		return False
	return bool(frappe.db.get_value("Shop", shop_name, "is_published"))
