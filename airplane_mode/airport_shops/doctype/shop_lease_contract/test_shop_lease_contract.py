# Copyright (c) 2026, ALYF and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestShopLeaseContract(FrappeTestCase):
	def test_before_insert_seeds_next_due_date_from_lease_start(self):
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		code = f"L{sfx}"[:8]
		ap = frappe.get_doc(
			{
				"doctype": "Airport",
				"name": f"_LeaseSeed-{sfx}",
				"code": code,
				"city": "C",
				"country": "D",
			}
		).insert(ignore_permissions=True)
		shop = frappe.get_doc({"doctype": "Shop", "airport": ap.name, "area": 10.0}).insert(
			ignore_permissions=True
		)
		tenant = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"first_name": "L",
				"last_name": f"Seed{sfx}",
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
					"lease_start_date": "2026-03-01",
				}
			).insert(ignore_permissions=True)
			self.assertEqual(str(lease.next_due_date), "2026-03-01")
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
