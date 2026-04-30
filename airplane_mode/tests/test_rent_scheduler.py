# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

import frappe
from dateutil.relativedelta import relativedelta
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_months, getdate, today

from airplane_mode.airport_shops.tasks import create_due_shop_rent_payments
from airplane_mode.tests.helpers import get_shop_type_for_tests

test_dependencies = [
	"Airport",
	"Shop",
	"Shop Type",
	"Shop Tenant",
	"Shop Lease Contract",
	"Shop Rent Payment",
	"Airport Shop Settings",
	"Notification",
]

# Standard app **Notification** (exported JSON under `airport_shops/notification/`).
RENT_PAYMENT_REMINDER_NOTIFICATION = "Rent Payment Reminder Email"


def _lease_start_default() -> date:
	"""First day of the month, two months before *today* (stable monthly rent periods)."""
	d = getdate(today())
	return add_months(d.replace(day=1), -2)


def _lease_expiry_default(lease_start: date) -> date:
	return lease_start + relativedelta(years=2)


def _period_end(period_start: date) -> date:
	"""Inclusive end of one calendar billing month starting *period_start* (matches rent task)."""
	return period_start + relativedelta(months=1) - timedelta(days=1)


def _make_lease_bundle(*, suffix: str) -> dict:
	"""Minimal Airport → Shop → Tenant → **Shop Lease Contract** for rent tests."""
	lease_start = _lease_start_default()
	lease_expiry = _lease_expiry_default(lease_start)
	code = f"R{suffix}"[:8]
	ap = frappe.get_doc(
		{
			"doctype": "Airport",
			"name": f"_RentTest-{suffix}",
			"code": code,
			"city": "Test City",
			"country": "TC",
		}
	).insert(ignore_permissions=True)
	shop = frappe.get_doc(
		{
			"doctype": "Shop",
			"airport": ap.name,
			"area": 42.0,
			"floors": 1,
			"shop_type": get_shop_type_for_tests(),
		}
	).insert(ignore_permissions=True)
	tenant = frappe.get_doc(
		{
			"doctype": "Shop Tenant",
			"first_name": "Rent",
			"last_name": f"Sch{suffix}",
			"email": f"rent_{suffix}@example.com",
		}
	).insert(ignore_permissions=True)
	lease = frappe.get_doc(
		{
			"doctype": "Shop Lease Contract",
			"shop": shop.name,
			"tenant": tenant.name,
			"rent": 100.0,
			"lease_start_date": lease_start,
			"lease_expiry_date": lease_expiry,
		}
	).insert(ignore_permissions=True)
	return {
		"airport": ap.name,
		"shop": shop.name,
		"tenant": tenant.name,
		"lease": lease.name,
	}


def _automated_message_for_payment(payment_name: str) -> list[str]:
	return frappe.get_all(
		"Communication",
		filters={
			"reference_doctype": "Shop Rent Payment",
			"reference_name": payment_name,
			"communication_type": "Automated Message",
		},
		pluck="name",
	)


class TestRentScheduler(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._prev_reminders = frappe.db.get_single_value("Airport Shop Settings", "enable_rent_reminders")
		self._bundle: dict | None = None

	def tearDown(self):
		frappe.db.set_single_value(
			"Airport Shop Settings",
			"enable_rent_reminders",
			self._prev_reminders,
		)
		b = self._bundle
		if b:
			for name in frappe.get_all(
				"Shop Rent Payment",
				filters={"lease_contract": b["lease"]},
				pluck="name",
			):
				for comm in _automated_message_for_payment(name):
					frappe.delete_doc("Communication", comm, force=True, ignore_permissions=True)
				frappe.delete_doc("Shop Rent Payment", name, force=True, ignore_permissions=True)
			for dt, key in (
				("Shop Lease Contract", "lease"),
				("Shop", "shop"),
				("Shop Tenant", "tenant"),
				("Airport", "airport"),
			):
				if frappe.db.exists(dt, b[key]):
					frappe.delete_doc(dt, b[key], force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_scheduler_creates_due_payment_and_advances_cursor(self):
		sfx = frappe.generate_hash(length=8)
		self._bundle = _make_lease_bundle(suffix=sfx)
		lease_start = getdate(
			frappe.db.get_value("Shop Lease Contract", self._bundle["lease"], "lease_start_date")
		)
		first_period_end = _period_end(lease_start)
		next_due = first_period_end + timedelta(days=1)

		with patch("airplane_mode.airport_shops.tasks.today", return_value=str(first_period_end)):
			create_due_shop_rent_payments()

		payments = frappe.get_all(
			"Shop Rent Payment",
			filters={"lease_contract": self._bundle["lease"]},
			fields=["name", "period_start", "period_end"],
		)
		self.assertEqual(len(payments), 1)
		self.assertEqual(getdate(payments[0].period_start), lease_start)
		self.assertEqual(getdate(payments[0].period_end), first_period_end)

		next_due_db = frappe.db.get_value("Shop Lease Contract", self._bundle["lease"], "next_due_date")
		self.assertEqual(getdate(next_due_db), next_due)

	def test_scheduler_skips_existing_period(self):
		sfx = frappe.generate_hash(length=8)
		self._bundle = _make_lease_bundle(suffix=sfx)
		lease_start = getdate(
			frappe.db.get_value("Shop Lease Contract", self._bundle["lease"], "lease_start_date")
		)
		first_period_end = _period_end(lease_start)
		next_due = first_period_end + timedelta(days=1)

		frappe.get_doc(
			{
				"doctype": "Shop Rent Payment",
				"lease_contract": self._bundle["lease"],
				"amount_due": 100.0,
				"period_start": lease_start,
				"period_end": first_period_end,
			}
		).insert(ignore_permissions=True)

		with patch("airplane_mode.airport_shops.tasks.today", return_value=str(first_period_end)):
			create_due_shop_rent_payments()

		count = frappe.db.count("Shop Rent Payment", {"lease_contract": self._bundle["lease"]})
		self.assertEqual(count, 1)
		next_due_db = frappe.db.get_value("Shop Lease Contract", self._bundle["lease"], "next_due_date")
		self.assertEqual(getdate(next_due_db), next_due)

	def test_rent_reminder_notification_on_new_payment(self):
		if not frappe.db.exists("Notification", RENT_PAYMENT_REMINDER_NOTIFICATION):
			self.skipTest(
				f"Install/sync **Notification** `{RENT_PAYMENT_REMINDER_NOTIFICATION}` "
				"(app export) to run this test."
			)

		prev_enabled = frappe.db.get_value("Notification", RENT_PAYMENT_REMINDER_NOTIFICATION, "enabled")
		frappe.db.set_value("Notification", RENT_PAYMENT_REMINDER_NOTIFICATION, "enabled", 1)
		frappe.db.set_single_value("Airport Shop Settings", "enable_rent_reminders", 1)

		sfx = frappe.generate_hash(length=8)
		self._bundle = _make_lease_bundle(suffix=sfx)
		try:
			lease_start = getdate(
				frappe.db.get_value("Shop Lease Contract", self._bundle["lease"], "lease_start_date")
			)
			# Later month inside the lease — avoids overlapping the scheduler's first period.
			period_start = lease_start + relativedelta(months=6)
			period_end = _period_end(period_start)

			pay = frappe.get_doc(
				{
					"doctype": "Shop Rent Payment",
					"lease_contract": self._bundle["lease"],
					"amount_due": 100.0,
					"period_start": period_start,
					"period_end": period_end,
				}
			).insert(ignore_permissions=True)

			comms = _automated_message_for_payment(pay.name)
			self.assertTrue(
				comms,
				"Desk **Notification** (New → email) should create an **Automated Message** "
				"**Communication** linked to the **Shop Rent Payment** (see `Notification.send_an_email`).",
			)
		finally:
			frappe.db.set_value(
				"Notification",
				RENT_PAYMENT_REMINDER_NOTIFICATION,
				"enabled",
				prev_enabled,
			)
