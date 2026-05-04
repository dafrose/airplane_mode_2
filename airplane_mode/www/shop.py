# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import get_url

from airplane_mode.airport_shops.shops_portal_context import (
	is_shop_portal_visible,
	picnic_stylesheet_url,
)

SHOP_LEAD_ROUTE = "shop-lead"


def build_shop_detail_context(context, shop_name: str | None = None) -> None:
	context.no_cache = 1
	context.picnic_css = picnic_stylesheet_url()
	name = shop_name or frappe.form_dict.get("name") or frappe.form_dict.get("shop")
	if not name:
		frappe.throw(_("Shop not found."), frappe.PageDoesNotExistError)
	if not frappe.db.exists("Shop", name):
		frappe.throw(_("Shop not found."), frappe.PageDoesNotExistError)
	if not is_shop_portal_visible(name):
		frappe.throw(_("Shop not found."), frappe.PageDoesNotExistError)

	row = frappe.db.get_value(
		"Shop",
		name,
		["airport", "airport_code", "area", "floors", "shop_type", "status"],
		as_dict=True,
	)
	row["name"] = name
	code = row.get("airport_code") or ""
	airport_doc = row.get("airport") or ""
	row["airport_display"] = f"{code} - {airport_doc}"
	context.shop = row
	context.page_title = f"{name} — {code}" if code else name
	context.shop_lead_url = get_url(f"/{SHOP_LEAD_ROUTE}?shop={quote(name, safe='')}")


def get_context(context):
	build_shop_detail_context(context)
