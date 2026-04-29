# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase

from airplane_mode.airport_shops.shop_lead_portal import submit_shop_lead
from airplane_mode.airport_shops.shops_portal_context import is_shop_portal_visible
from airplane_mode.airport_shops.web_form.shop_lead import shop_lead as shop_lead_module
from airplane_mode.airport_shops.web_form.shop_lead.shop_lead import (
	PICNIC_SHOP_WEB_FORM_TEMPLATE,
	merge_shop_lead_reference_doc,
	resolve_shop_lead_prefill,
)
from airplane_mode.airport_shops.web_form.shop_lead.shop_lead import (
	get_context as shop_lead_web_form_get_context,
)
from airplane_mode.tests.helpers import get_shop_type_for_tests
from airplane_mode.www.shop import SHOP_LEAD_ROUTE, build_shop_detail_context
from airplane_mode.www.shop_lead import build_shop_lead_page_context
from airplane_mode.www.shops import build_shops_list_context

test_dependencies = ["Airport", "Shop", "Shop Lead", "Shop Type"]


def _make_airport_and_shop(*, suffix: str, is_published: int) -> tuple[str, str]:
	code = f"P{suffix}"[:8]
	ap = frappe.get_doc(
		{
			"doctype": "Airport",
			"name": f"_PortalAir-{suffix}",
			"code": code,
			"city": "Portal City",
			"country": "PC",
		}
	).insert(ignore_permissions=True)
	shop = frappe.get_doc(
		{
			"doctype": "Shop",
			"airport": ap.name,
			"area": 25.5,
			"shop_type": get_shop_type_for_tests(),
			"is_published": is_published,
		}
	).insert(ignore_permissions=True)
	return ap.name, shop.name


class TestShopsPortalContext(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_list_shows_only_published_shops(self):
		sfx = frappe.generate_hash(length=6)
		_, hidden = _make_airport_and_shop(suffix=f"h{sfx}", is_published=0)
		_, visible = _make_airport_and_shop(suffix=f"v{sfx}", is_published=1)
		ctx = frappe._dict()
		build_shops_list_context(ctx)
		names = [r["name"] for r in ctx.shops]
		self.assertIn(visible, names)
		self.assertNotIn(hidden, names)
		for row in ctx.shops:
			if row["name"] == visible:
				self.assertIn("/shop?name=", row["detail_url"])

	def test_detail_requires_published_shop(self):
		sfx = frappe.generate_hash(length=6)
		_, name = _make_airport_and_shop(suffix=f"u{sfx}", is_published=0)
		ctx = frappe._dict()
		with self.assertRaises(ValidationError):
			build_shop_detail_context(ctx, shop_name=name)

	def test_detail_loads_published_shop(self):
		sfx = frappe.generate_hash(length=6)
		_, name = _make_airport_and_shop(suffix=f"p{sfx}", is_published=1)
		ctx = frappe._dict()
		build_shop_detail_context(ctx, shop_name=name)
		self.assertEqual(ctx.shop.name, name)
		self.assertEqual(ctx.shop.area, 25.5)
		self.assertIn(f"/{SHOP_LEAD_ROUTE}?shop=", ctx.shop_lead_url)

	def test_is_shop_portal_visible(self):
		sfx = frappe.generate_hash(length=6)
		_, pub = _make_airport_and_shop(suffix=f"a{sfx}", is_published=1)
		_, un = _make_airport_and_shop(suffix=f"b{sfx}", is_published=0)
		self.assertTrue(is_shop_portal_visible(pub))
		self.assertFalse(is_shop_portal_visible(un))
		self.assertFalse(is_shop_portal_visible(""))

	def test_shop_lead_prefill_resolution(self):
		sfx = frappe.generate_hash(length=6)
		_, pub = _make_airport_and_shop(suffix=f"o{sfx}", is_published=1)
		_, un = _make_airport_and_shop(suffix=f"n{sfx}", is_published=0)
		self.assertIsNone(resolve_shop_lead_prefill(response_name=None, shop=None))
		self.assertIsNone(resolve_shop_lead_prefill(response_name="SHOPLEAD-00001", shop=pub))
		ref = resolve_shop_lead_prefill(response_name=None, shop=pub)
		self.assertEqual(ref, {"doctype": "Shop Lead", "shop": pub})
		self.assertIsNone(resolve_shop_lead_prefill(response_name=None, shop=un))

	def test_merge_shop_lead_reference_doc(self):
		ctx = frappe._dict(reference_doc={"doctype": "Shop Lead", "first_name": "A"})
		merge_shop_lead_reference_doc(ctx, {"doctype": "Shop Lead", "shop": "X.-SHOP-.001"})
		self.assertEqual(ctx.reference_doc["first_name"], "A")
		self.assertEqual(ctx.reference_doc["shop"], "X.-SHOP-.001")

	def test_shop_lead_web_form_uses_picnic_template(self):
		ctx = frappe._dict(web_form_doc={"name": "shop-lead", "route": "shop-lead"})
		shop_lead_web_form_get_context(ctx)
		self.assertEqual(ctx.template, PICNIC_SHOP_WEB_FORM_TEMPLATE)
		self.assertTrue(ctx.picnic_css)
		self.assertTrue(ctx.shops_portal_url.endswith("/shops"))
		self.assertTrue(ctx.success_url.endswith("/shops"))
		self.assertEqual(ctx.success_title, shop_lead_module._shop_lead_success_title())
		self.assertEqual(ctx.web_form_doc["success_url"], ctx.success_url)

	def test_shop_lead_success_context_updates_web_form_doc(self):
		ctx = frappe._dict(web_form_doc={"route": "shop-lead"})
		shop_lead_module._apply_shop_lead_success_context(ctx)
		self.assertTrue(ctx.success_url.endswith("/shops"))
		self.assertEqual(
			ctx.web_form_doc["success_message"],
			shop_lead_module._shop_lead_success_message(),
		)

	def test_shop_lead_page_context(self):
		sfx = frappe.generate_hash(length=6)
		_, name = _make_airport_and_shop(suffix=f"e{sfx}", is_published=1)
		ctx = frappe._dict()
		build_shop_lead_page_context(ctx, shop_name=name)
		self.assertEqual(ctx.shop.name, name)
		self.assertTrue(ctx.csrf_token)
		self.assertIn("/shop?name=", ctx.shop_detail_url)
		self.assertTrue(ctx.submit_method.endswith("submit_shop_lead"))

	def test_submit_shop_lead_inserts_row(self):
		sfx = frappe.generate_hash(length=6)
		_, name = _make_airport_and_shop(suffix=f"s{sfx}", is_published=1)
		out = submit_shop_lead(
			shop=name,
			first_name="Portal",
			last_name="Lead",
			email="portal_lead_test@example.com",
		)
		self.assertTrue(out.get("name"))
		self.assertEqual(frappe.db.get_value("Shop Lead", out["name"], "shop"), name)

	def test_submit_shop_lead_rejects_unpublished_shop(self):
		sfx = frappe.generate_hash(length=6)
		_, name = _make_airport_and_shop(suffix=f"x{sfx}", is_published=0)
		with self.assertRaises(ValidationError):
			submit_shop_lead(
				shop=name,
				first_name="A",
				last_name="B",
				email="x@example.com",
			)
