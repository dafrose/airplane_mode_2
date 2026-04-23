# Copyright (c) 2026, ALYF and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, today

from airplane_mode.tests.test_rent_scheduler import _make_lease_bundle


class TestShopRentPayment(FrappeTestCase):
	def test_submit_sets_paid_and_cancel_resets_due(self):
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		bundle = _make_lease_bundle(suffix=sfx)
		try:
			pay = frappe.get_doc(
				{
					"doctype": "Shop Rent Payment",
					"lease_contract": bundle["lease"],
					"amount_due": 100.0,
					"period_start": "2026-04-01",
					"period_end": "2026-04-30",
				}
			).insert(ignore_permissions=True)
			pay.submit()
			pay.reload()
			self.assertEqual(pay.status, "Paid")
			self.assertIsNotNone(pay.date_paid)
			self.assertEqual(getdate(pay.date_paid), getdate(today()))

			pay.cancel()
			pay.reload()
			self.assertEqual(pay.status, "Due")
			self.assertIsNone(pay.date_paid)
		finally:
			for name in frappe.get_all(
				"Shop Rent Payment",
				filters={"lease_contract": bundle["lease"]},
				pluck="name",
			):
				frappe.delete_doc("Shop Rent Payment", name, force=True, ignore_permissions=True)
			for dt, key in (
				("Shop Lease Contract", "lease"),
				("Shop", "shop"),
				("Shop Tenant", "tenant"),
				("Airport", "airport"),
			):
				if frappe.db.exists(dt, bundle[key]):
					frappe.delete_doc(dt, bundle[key], force=True, ignore_permissions=True)
			frappe.db.commit()
