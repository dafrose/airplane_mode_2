# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import get_url

from airplane_mode.airport_shops.shops_portal_context import picnic_stylesheet_url


def build_shops_list_context(context) -> None:
	context.no_cache = 1
	context.page_title = _("Airport shops")
	context.picnic_css = picnic_stylesheet_url()
	rows = frappe.get_all(
		"Shop",
		filters={"is_published": 1},
		fields=["name", "airport_code", "area", "shop_type", "status"],
		order_by="airport_code asc, name asc",
		ignore_permissions=True,
	)
	base = get_url("/shop")
	for row in rows:
		row["detail_url"] = f"{base}?name={quote(row.name, safe='')}"
	context.shops = rows


def get_context(context):
	build_shops_list_context(context)
