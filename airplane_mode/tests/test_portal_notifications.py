# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from airplane_mode.install import _ensure_notification_log_portal_hidden_field
from airplane_mode.portal_notifications import (
	get_portal_notification_logs,
	hide_all_portal_notifications,
	hide_portal_notification,
)


class TestPortalNotifications(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_notification_log_portal_hidden_field()
		frappe.db.delete("Notification Log", {"for_user": "Administrator"})
		frappe.db.commit()

	def _insert_log(self, **kwargs) -> str:
		doc = frappe.get_doc(
			{
				"doctype": "Notification Log",
				"for_user": "Administrator",
				"from_user": "Administrator",
				"type": "Alert",
				"subject": "Test alert",
				"read": 0,
				**kwargs,
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def test_get_portal_notification_logs_excludes_hidden(self):
		visible = self._insert_log(hidden_from_portal=0)
		self._insert_log(hidden_from_portal=1)

		frappe.set_user("Administrator")
		out = get_portal_notification_logs(limit=20)
		names = {r["name"] for r in out["notification_logs"]}
		self.assertIn(visible, names)
		self.assertEqual(len(names), 1)

	def test_hide_portal_notification_then_missing_from_list(self):
		name = self._insert_log(hidden_from_portal=0)
		frappe.set_user("Administrator")
		hide_portal_notification(name)
		out = get_portal_notification_logs()
		self.assertEqual([r["name"] for r in out["notification_logs"]], [])

	def test_hide_all_portal_notifications(self):
		a = self._insert_log(hidden_from_portal=0)
		b = self._insert_log(hidden_from_portal=0)
		frappe.set_user("Administrator")
		hide_all_portal_notifications()
		out = get_portal_notification_logs()
		self.assertEqual(len(out["notification_logs"]), 0)
		self.assertEqual(int(frappe.db.get_value("Notification Log", a, "hidden_from_portal")), 1)
		self.assertEqual(int(frappe.db.get_value("Notification Log", b, "hidden_from_portal")), 1)
