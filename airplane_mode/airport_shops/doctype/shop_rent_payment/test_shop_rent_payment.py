# Copyright (c) 2026, ALYF and Contributors
# See license.txt

from io import BytesIO
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, today

from airplane_mode.airport_shops.doctype.shop_rent_payment.shop_rent_payment import (
	PAYMENT_RECEIPT_PRINT_FORMAT,
)
from airplane_mode.tests.test_rent_scheduler import (
	_automated_message_for_payment,
	_make_lease_bundle,
)

test_dependencies = [
	"Airport",
	"Shop",
	"Shop Type",
	"Shop Tenant",
	"Shop Lease Contract",
	"Shop Rent Payment",
	"Notification",
]


def _submit_receipt_notification_row():
	"""First **Email** **Notification** on **Submit** for **Shop Rent Payment** with print attach."""
	rows = frappe.get_all(
		"Notification",
		filters={
			"document_type": "Shop Rent Payment",
			"event": "Submit",
			"channel": "Email",
		},
		fields=["name", "attach_print", "print_format", "enabled"],
	)
	for row in rows:
		if row.attach_print and row.print_format:
			return row
	return None


def _sendmail_patch():
	"""Desk **Notification** may fire on submit; absorb outbound mail in tests."""
	return patch("frappe.sendmail")


def _minimal_pdf_bytes() -> bytes:
	"""Tiny valid PDF for tests (passes **File** PDF checks without **wkhtmltopdf**)."""
	from pypdf import PdfWriter

	buf = BytesIO()
	w = PdfWriter()
	w.add_blank_page(width=72, height=72)
	w.write(buf)
	return buf.getvalue()


def _get_pdf_patch():
	# `get_print` imports **get_pdf** inside the function; patch the definition module.
	return patch("frappe.utils.pdf.get_pdf", return_value=_minimal_pdf_bytes())


def _cancel_payment_in_test(pay):
	"""Cancel a submitted payment; if the row stays submitted, retry with `save` + `commit`."""
	with _sendmail_patch():
		pay.cancel()
	pay.reload()
	if pay.docstatus != 2:
		with _sendmail_patch():
			pay.save()
		frappe.db.commit()
		pay.reload()


def _cleanup_shop_rent_scenario(bundle: dict) -> None:
	payment_names = frappe.get_all(
		"Shop Rent Payment",
		filters={"lease_contract": bundle["lease"]},
		pluck="name",
	)
	for pname in payment_names:
		doc = frappe.get_doc("Shop Rent Payment", pname)
		if doc.docstatus == 1:
			_cancel_payment_in_test(doc)
	for f in frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Shop Rent Payment"},
		fields=["name", "attached_to_name"],
	):
		if f.attached_to_name in payment_names:
			frappe.delete_doc("File", f.name, force=True, ignore_permissions=True)
	for name in payment_names:
		for comm in _automated_message_for_payment(name):
			frappe.delete_doc("Communication", comm, force=True, ignore_permissions=True)
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


def _insert_due_payment(bundle: dict):
	return frappe.get_doc(
		{
			"doctype": "Shop Rent Payment",
			"lease_contract": bundle["lease"],
			"amount_due": 100.0,
			"period_start": "2026-04-01",
			"period_end": "2026-04-30",
		}
	).insert(ignore_permissions=True)


class TestShopRentPayment(FrappeTestCase):
	def test_submit_and_cancel_update_status_and_date_paid(self):
		"""Submit sets *Paid* / *Date Paid*; cancel restores *Due* and clears *Date Paid*."""
		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		bundle = _make_lease_bundle(suffix=sfx)
		try:
			pay = _insert_due_payment(bundle)
			with _sendmail_patch(), _get_pdf_patch():
				pay.submit()
			pay.reload()
			self.assertEqual(pay.status, "Paid")
			self.assertIsNotNone(pay.date_paid)
			self.assertEqual(getdate(pay.date_paid), getdate(today()))

			_cancel_payment_in_test(pay)
			self.assertEqual(pay.docstatus, 2, "Cancel should set **docstatus** to cancelled (2).")
			self.assertEqual(pay.status, "Due")
			self.assertIsNone(pay.date_paid)
		finally:
			_cleanup_shop_rent_scenario(bundle)

	def test_submit_triggers_notification_email_with_print_attachment(self):
		"""Desk **Notification** (Submit, Email, attach print) → **Communication** + **sendmail** payload."""
		notif_row = _submit_receipt_notification_row()
		if not notif_row:
			self.skipTest(
				"Create a Desk **Notification** for **Shop Rent Payment** on **Submit** (Email) "
				"with **Attach Print** and a **Print Format**, then re-run this test."
			)

		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		bundle = _make_lease_bundle(suffix=sfx)
		prev_enabled = notif_row.enabled
		frappe.db.set_value("Notification", notif_row.name, "enabled", 1)
		self.assertEqual(
			notif_row.print_format,
			PAYMENT_RECEIPT_PRINT_FORMAT,
			"Keep the Submit **Notification** **Print Format** in sync with `PAYMENT_RECEIPT_PRINT_FORMAT`.",
		)
		try:
			pay = _insert_due_payment(bundle)
			with patch("frappe.sendmail") as mock_sendmail, _get_pdf_patch():
				pay.submit()

			comms = _automated_message_for_payment(pay.name)
			self.assertTrue(
				comms,
				"Submit **Notification** should create an **Automated Message** **Communication**.",
			)
			self.assertEqual(
				frappe.db.get_value("Communication", comms[0], "has_attachment"),
				1,
			)
			self.assertTrue(mock_sendmail.called)
			send_kwargs = mock_sendmail.call_args.kwargs
			self.assertEqual(send_kwargs["recipients"], [f"rent_{sfx}@example.com"])
			self.assertEqual(send_kwargs["reference_doctype"], "Shop Rent Payment")
			self.assertEqual(send_kwargs["reference_name"], pay.name)
			print_att = next(
				(
					a
					for a in (send_kwargs.get("attachments") or [])
					if isinstance(a, dict) and a.get("print_format_attachment")
				),
				None,
			)
			self.assertIsNotNone(print_att)
			self.assertEqual(print_att.get("doctype"), "Shop Rent Payment")
			self.assertEqual(print_att.get("name"), pay.name)
			self.assertEqual(print_att.get("print_format"), notif_row.print_format)
		finally:
			frappe.db.set_value("Notification", notif_row.name, "enabled", prev_enabled)
			_cleanup_shop_rent_scenario(bundle)

	def test_submit_attaches_receipt_pdf_to_document(self):
		"""Controller **on_submit** stores a **File** PDF on the **Shop Rent Payment** (timeline)."""
		if not frappe.db.exists("Print Format", PAYMENT_RECEIPT_PRINT_FORMAT):
			self.skipTest(
				f"Add standard **Print Format** `{PAYMENT_RECEIPT_PRINT_FORMAT}` (migrate / Desk), "
				"then re-run this test."
			)

		frappe.set_user("Administrator")
		sfx = frappe.generate_hash(length=8)
		bundle = _make_lease_bundle(suffix=sfx)
		try:
			pay = _insert_due_payment(bundle)
			with _sendmail_patch(), _get_pdf_patch():
				pay.submit()

			pdf_rows = [
				f
				for f in frappe.get_all(
					"File",
					filters={
						"attached_to_doctype": "Shop Rent Payment",
						"attached_to_name": pay.name,
					},
					fields=["name", "file_name"],
				)
				if f.file_name.endswith(".pdf")
			]
			self.assertTrue(pdf_rows)
			self.assertEqual(
				frappe.get_doc("File", pdf_rows[0].name).get_content()[:4],
				b"%PDF",
			)
		finally:
			_cleanup_shop_rent_scenario(bundle)
