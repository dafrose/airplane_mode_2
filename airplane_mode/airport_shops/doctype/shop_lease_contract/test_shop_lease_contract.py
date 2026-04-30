# Copyright (c) 2026, ALYF and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from airplane_mode.tests.helpers import get_shop_type_for_tests


def _new_shop_dict(airport: str, **fields):
	return {
		"doctype": "Shop",
		"airport": airport,
		"area": 10.0,
		"floors": 1,
		"shop_type": get_shop_type_for_tests(),
		**fields,
	}


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
		shop = frappe.get_doc(_new_shop_dict(ap.name)).insert(ignore_permissions=True)
		tenant = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"first_name": "L",
				"last_name": f"Seed{sfx}",
				"email": f"lease_seed_{sfx}@example.com",
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

	def test_shop_status_occupied_when_lease_expiry_in_future(self):
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		code = f"F{sfx}"[:8]
		ap = frappe.get_doc(
			{
				"doctype": "Airport",
				"name": f"_LeaseFut-{sfx}",
				"code": code,
				"city": "C",
				"country": "D",
			}
		).insert(ignore_permissions=True)
		shop = frappe.get_doc(_new_shop_dict(ap.name)).insert(ignore_permissions=True)
		tenant = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"first_name": "F",
				"last_name": f"Fut{sfx}",
				"email": f"lease_fut_{sfx}@example.com",
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
					"lease_expiry_date": add_days(today(), 365),
				}
			).insert(ignore_permissions=True)
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

	def test_shop_status_available_when_lease_expired_today_or_earlier(self):
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		code = f"E{sfx}"[:8]
		ap = frappe.get_doc(
			{
				"doctype": "Airport",
				"name": f"_LeaseExp-{sfx}",
				"code": code,
				"city": "C",
				"country": "D",
			}
		).insert(ignore_permissions=True)
		shop = frappe.get_doc(_new_shop_dict(ap.name)).insert(ignore_permissions=True)
		tenant = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"first_name": "E",
				"last_name": f"Exp{sfx}",
				"email": f"lease_exp_{sfx}@example.com",
			}
		).insert(ignore_permissions=True)
		lease = None
		try:
			for expiry in (today(), add_days(today(), -10)):
				if lease and frappe.db.exists("Shop Lease Contract", lease.name):
					frappe.delete_doc(
						"Shop Lease Contract",
						lease.name,
						force=True,
						ignore_permissions=True,
					)
				lease = frappe.get_doc(
					{
						"doctype": "Shop Lease Contract",
						"shop": shop.name,
						"tenant": tenant.name,
						"rent": 50.0,
						"lease_start_date": "2020-01-01",
						"lease_expiry_date": expiry,
					}
				).insert(ignore_permissions=True)
				self.assertEqual(
					frappe.db.get_value("Shop", shop.name, "status"),
					"Available",
					msg=f"expected Available for lease_expiry_date={expiry!r}",
				)
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

	def test_on_update_sets_occupied_when_expiry_moves_from_past_to_future(self):
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		code = f"M{sfx}"[:8]
		ap = frappe.get_doc(
			{
				"doctype": "Airport",
				"name": f"_LeaseMv-{sfx}",
				"code": code,
				"city": "C",
				"country": "D",
			}
		).insert(ignore_permissions=True)
		shop = frappe.get_doc(_new_shop_dict(ap.name)).insert(ignore_permissions=True)
		tenant = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"first_name": "M",
				"last_name": f"Mov{sfx}",
				"email": f"lease_mv_{sfx}@example.com",
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
					"lease_expiry_date": add_days(today(), -1),
				}
			).insert(ignore_permissions=True)
			self.assertEqual(frappe.db.get_value("Shop", shop.name, "status"), "Available")
			lease.lease_expiry_date = add_days(today(), 30)
			lease.save(ignore_permissions=True)
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

	def test_before_save_resets_next_due_date_when_lease_start_changes(self):
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		code = f"N{sfx}"[:8]
		ap = frappe.get_doc(
			{
				"doctype": "Airport",
				"name": f"_LeaseNd-{sfx}",
				"code": code,
				"city": "C",
				"country": "D",
			}
		).insert(ignore_permissions=True)
		shop = frappe.get_doc(_new_shop_dict(ap.name)).insert(ignore_permissions=True)
		tenant = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"first_name": "N",
				"last_name": f"Nd{sfx}",
				"email": f"lease_nd_{sfx}@example.com",
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
			lease.next_due_date = "2026-04-01"
			lease.lease_start_date = "2026-03-15"
			lease.save(ignore_permissions=True)
			self.assertEqual(str(lease.next_due_date), "2026-03-15")
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

	def test_on_trash_sets_shop_available(self):
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		code = f"T{sfx}"[:8]
		ap = frappe.get_doc(
			{
				"doctype": "Airport",
				"name": f"_LeaseTr-{sfx}",
				"code": code,
				"city": "C",
				"country": "D",
			}
		).insert(ignore_permissions=True)
		shop = frappe.get_doc(_new_shop_dict(ap.name, status="Occupied")).insert(ignore_permissions=True)
		tenant = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"first_name": "T",
				"last_name": f"Tr{sfx}",
				"email": f"lease_tr_{sfx}@example.com",
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
			self.assertEqual(frappe.db.get_value("Shop", shop.name, "status"), "Occupied")
			frappe.delete_doc(
				"Shop Lease Contract",
				lease.name,
				force=True,
				ignore_permissions=True,
			)
			lease = None
			self.assertEqual(frappe.db.get_value("Shop", shop.name, "status"), "Available")
		finally:
			for dt, nm in (
				("Shop", shop.name),
				("Shop Tenant", tenant.name),
				("Airport", ap.name),
			):
				if frappe.db.exists(dt, nm):
					frappe.delete_doc(dt, nm, force=True, ignore_permissions=True)
