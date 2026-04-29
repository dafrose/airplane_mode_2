# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from airplane_mode.airport_shops.tasks import sync_occupied_shop_status_from_leases
from airplane_mode.tests.helpers import get_shop_type_for_tests
from airplane_mode.tests.test_rent_scheduler import _make_lease_bundle

test_dependencies = [
	"Airport",
	"Shop",
	"Shop Type",
	"Shop Tenant",
	"Shop Lease Contract",
]


class TestShopStatusScheduler(FrappeTestCase):
	def test_sync_sets_available_when_all_leases_expired(self):
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		bundle = _make_lease_bundle(suffix=sfx)
		try:
			self.assertEqual(frappe.db.get_value("Shop", bundle["shop"], "status"), "Occupied")
			with patch("airplane_mode.airport_shops.tasks.today", return_value="2029-12-31"):
				sync_occupied_shop_status_from_leases()
			self.assertEqual(frappe.db.get_value("Shop", bundle["shop"], "status"), "Available")
		finally:
			if frappe.db.exists("Shop Lease Contract", bundle["lease"]):
				frappe.delete_doc(
					"Shop Lease Contract",
					bundle["lease"],
					force=True,
					ignore_permissions=True,
				)
			for dt, key in (
				("Shop", "shop"),
				("Shop Tenant", "tenant"),
				("Airport", "airport"),
			):
				if frappe.db.exists(dt, bundle[key]):
					frappe.delete_doc(dt, bundle[key], force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_sync_keeps_occupied_when_open_ended_lease(self):
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		code = f"O{sfx}"[:8]
		ap = frappe.get_doc(
			{
				"doctype": "Airport",
				"name": f"_OpenEnd-{sfx}",
				"code": code,
				"city": "C",
				"country": "D",
			}
		).insert(ignore_permissions=True)
		shop = frappe.get_doc(
			{
				"doctype": "Shop",
				"airport": ap.name,
				"area": 10.0,
				"shop_type": get_shop_type_for_tests(),
				"status": "Occupied",
			}
		).insert(ignore_permissions=True)
		tenant = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"first_name": "O",
				"last_name": f"End{sfx}",
				"email": f"open_end_{sfx}@example.com",
			}
		).insert(ignore_permissions=True)
		lease = None
		try:
			lease = frappe.get_doc(
				{
					"doctype": "Shop Lease Contract",
					"shop": shop.name,
					"tenant": tenant.name,
					"rent": 50.0,
					"lease_start_date": "2020-01-01",
				}
			).insert(ignore_permissions=True)
			self.assertEqual(frappe.db.get_value("Shop", shop.name, "status"), "Occupied")
			with patch("airplane_mode.airport_shops.tasks.today", return_value="2099-06-01"):
				sync_occupied_shop_status_from_leases()
			self.assertEqual(frappe.db.get_value("Shop", shop.name, "status"), "Occupied")
		finally:
			if lease and frappe.db.exists("Shop Lease Contract", lease.name):
				frappe.delete_doc(
					"Shop Lease Contract",
					lease.name,
					force=True,
					ignore_permissions=True,
				)
			for dt, nm in (
				("Shop", shop.name),
				("Shop Tenant", tenant.name),
				("Airport", ap.name),
			):
				if frappe.db.exists(dt, nm):
					frappe.delete_doc(dt, nm, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_sync_sets_available_for_occupied_shop_with_no_leases(self):
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		code = f"N{sfx}"[:8]
		ap = frappe.get_doc(
			{
				"doctype": "Airport",
				"name": f"_NoLease-{sfx}",
				"code": code,
				"city": "C",
				"country": "D",
			}
		).insert(ignore_permissions=True)
		shop = frappe.get_doc(
			{
				"doctype": "Shop",
				"airport": ap.name,
				"area": 10.0,
				"shop_type": get_shop_type_for_tests(),
				"status": "Occupied",
			}
		).insert(ignore_permissions=True)
		try:
			sync_occupied_shop_status_from_leases()
			self.assertEqual(frappe.db.get_value("Shop", shop.name, "status"), "Available")
		finally:
			if frappe.db.exists("Shop", shop.name):
				frappe.delete_doc("Shop", shop.name, force=True, ignore_permissions=True)
			if frappe.db.exists("Airport", ap.name):
				frappe.delete_doc("Airport", ap.name, force=True, ignore_permissions=True)
			frappe.db.commit()
