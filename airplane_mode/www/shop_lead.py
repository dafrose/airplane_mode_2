# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Picnic **www/shop-lead** page (replaces unpublished **Web Form** route ``shop-lead``)."""

from urllib.parse import quote

import frappe
from frappe import _
from frappe.sessions import get_csrf_token
from frappe.utils import get_url

from airplane_mode.airport_shops.shops_portal_context import (
	is_shop_portal_visible,
	picnic_stylesheet_url,
)


def build_shop_lead_page_context(context, shop_name: str | None = None) -> None:
	context.no_cache = 1
	context.picnic_css = picnic_stylesheet_url()
	context.shops_list_url = get_url("/shops")
	context.submit_method = "airplane_mode.airport_shops.shop_lead_portal.submit_shop_lead"
	context.csrf_token = get_csrf_token()

	name = shop_name or frappe.form_dict.get("shop") or frappe.form_dict.get("name")
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
	context.shop = row
	context.page_title = _("Request information: {0}").format(name)
	context.shop_detail_url = get_url(f"/shop?name={quote(name, safe='')}")


def get_context(context):
	build_shop_lead_page_context(context)
