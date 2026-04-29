# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_url

from airplane_mode.airport_shops.shops_portal_context import (
	is_shop_portal_visible,
	picnic_stylesheet_url,
)

PICNIC_SHOP_WEB_FORM_TEMPLATE = "templates/airport_shops_picnic_web_form.html"


def _shop_lead_success_title() -> str:
	return _("Thank you")


def _shop_lead_success_message() -> str:
	return _(
		"We received your request. You will be redirected to the published shops list in a few seconds, or use the link below if that does not happen."
	)


def resolve_shop_lead_prefill(
	*,
	response_name: str | None,
	shop: str | None,
) -> dict | None:
	"""Build **Shop Lead** ``reference_doc`` fragment for a *new* response only."""
	if response_name:
		return None
	if not shop or not is_shop_portal_visible(shop):
		return None
	return {"doctype": "Shop Lead", "shop": shop}


def merge_shop_lead_reference_doc(context, prefill: dict) -> None:
	context.no_cache = 1
	existing = context.get("reference_doc")
	base: dict = dict(existing) if isinstance(existing, dict) else {}
	base.update(prefill)
	context.reference_doc = base


def _apply_shop_lead_success_context(context) -> None:
	"""Align Desk JSON, **context**, and **web_form_doc** (used by **web_form.bundle.js** for redirect)."""
	url = get_url("/shops")
	title = _shop_lead_success_title()
	message = _shop_lead_success_message()
	context.success_title = title
	context.success_message = message
	context.success_url = url
	wd = getattr(context, "web_form_doc", None)
	if isinstance(wd, dict):
		wd["success_title"] = title
		wd["success_message"] = message
		wd["success_url"] = url


def get_context(context):
	"""Picnic shell (**base.html**), not **web.html**; optional **shop** query prefill."""
	context.template = PICNIC_SHOP_WEB_FORM_TEMPLATE
	context.picnic_css = picnic_stylesheet_url()
	context.shops_portal_url = get_url("/shops")
	_apply_shop_lead_success_context(context)

	prefill = resolve_shop_lead_prefill(
		response_name=frappe.form_dict.get("name"),
		shop=frappe.form_dict.get("shop"),
	)
	if prefill:
		merge_shop_lead_reference_doc(context, prefill)
