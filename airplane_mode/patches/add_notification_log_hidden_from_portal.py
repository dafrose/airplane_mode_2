# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

import frappe

from airplane_mode.install import _ensure_notification_log_portal_hidden_field


def execute():
	_ensure_notification_log_portal_hidden_field()
	frappe.db.commit()
