# Copyright (c) 2026, ALYF and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

TENANT_A = "shop_tenant_a@airplane.test"
TENANT_B = "shop_tenant_b@airplane.test"


def _new_tenant(**kwargs):
	data = {
		"doctype": "Shop Tenant",
		"first_name": kwargs.get("first_name", "Sync"),
		"last_name": kwargs.get("last_name", "Test"),
		"email": kwargs.get("email", f"sync_{frappe.generate_hash(length=8)}@airplane.test"),
	}
	data.update(kwargs)
	return frappe.get_doc(data)


class TestShopTenantUserSync(FrappeTestCase):
	def tearDown(self):
		for name in frappe.get_all("Shop Tenant", filters={"last_name": "SyncTest"}, pluck="name"):
			frappe.delete_doc("Shop Tenant", name, force=True, ignore_permissions=True)

	def test_linking_user_grants_user_permission_and_role(self):
		frappe.set_user("Administrator")
		doc = _new_tenant(last_name="SyncTest", user=TENANT_A).insert()
		self.assertTrue(
			frappe.db.exists(
				"User Permission",
				{"user": TENANT_A, "allow": "Shop Tenant", "for_value": doc.name},
			)
		)
		self.assertIn("Shop Tenant", frappe.get_roles(TENANT_A))

	def test_clearing_user_revokes_user_permission_and_role(self):
		frappe.set_user("Administrator")
		doc = _new_tenant(last_name="SyncTest", user=TENANT_A).insert()
		doc.user = None
		doc.save()
		self.assertFalse(
			frappe.db.exists(
				"User Permission",
				{"user": TENANT_A, "allow": "Shop Tenant", "for_value": doc.name},
			)
		)
		self.assertNotIn("Shop Tenant", frappe.get_roles(TENANT_A))

	def test_changing_user_moves_user_permission_and_role(self):
		frappe.set_user("Administrator")
		doc = _new_tenant(last_name="SyncTest", user=TENANT_A).insert()
		doc.user = TENANT_B
		doc.save()
		self.assertFalse(
			frappe.db.exists(
				"User Permission",
				{"user": TENANT_A, "allow": "Shop Tenant", "for_value": doc.name},
			)
		)
		self.assertTrue(
			frappe.db.exists(
				"User Permission",
				{"user": TENANT_B, "allow": "Shop Tenant", "for_value": doc.name},
			)
		)
		self.assertNotIn("Shop Tenant", frappe.get_roles(TENANT_A))
		self.assertIn("Shop Tenant", frappe.get_roles(TENANT_B))

	def test_trash_revokes_for_linked_user(self):
		frappe.set_user("Administrator")
		doc = _new_tenant(last_name="SyncTest", user=TENANT_A).insert()
		name = doc.name
		doc.delete()
		self.assertFalse(
			frappe.db.exists(
				"User Permission",
				{"user": TENANT_A, "allow": "Shop Tenant", "for_value": name},
			)
		)
		self.assertNotIn("Shop Tenant", frappe.get_roles(TENANT_A))
