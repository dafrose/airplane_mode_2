# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Colocated helpers for **Rent Payment Reminder Email**.

The alert uses **Send Alert On** = **Custom**; Frappe does not auto-trigger it. Sending is done from
**Shop Rent Payment** `after_insert` when **Airport Shop Settings** *Enable Rent Reminders* is on
(see `shop_rent_payment._send_rent_payment_reminder_if_enabled`).
"""


def get_context(context):
	# do your magic here
	pass
