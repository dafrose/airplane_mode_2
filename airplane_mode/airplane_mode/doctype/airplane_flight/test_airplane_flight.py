# Copyright (c) 2026, ALYF and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from airplane_mode.airplane_mode.doctype.airplane_flight.airplane_flight import (
	BOOK_FLIGHT_WEB_FORM_ROUTE,
	GATE_CHANGE_REALTIME_EVENT,
	sync_tickets_gate_for_flight,
)
from airplane_mode.tests.helpers import (
	create_test_flight,
	create_test_passenger,
	create_test_ticket,
)

test_dependencies = ["Airplane"]


class TestAirplaneFlight(FrappeTestCase):
	def test_on_submit_sets_status_to_completed(self):
		flight = create_test_flight()
		self.assertEqual(flight.status, "Scheduled")

		flight.submit()
		self.assertEqual(
			frappe.db.get_value("Airplane Flight", flight.name, "status"),
			"Completed",
		)

	def test_get_context_builds_book_flight_url(self):
		flight = create_test_flight()
		ctx = frappe._dict()

		flight.get_context(ctx)

		self.assertIn(flight.source_airport_code, ctx.title)
		self.assertIn(flight.destination_airport_code, ctx.title)
		self.assertTrue(ctx.book_flight_url.startswith(f"/{BOOK_FLIGHT_WEB_FORM_ROUTE}/new?flight="))

	def test_get_context_url_quotes_flight_name(self):
		"""Generated flight names contain spaces, which must be URL-encoded."""
		flight = create_test_flight()
		ctx = frappe._dict()

		flight.get_context(ctx)

		query_value = ctx.book_flight_url.split("flight=", 1)[1]
		self.assertNotIn(" ", query_value)
		if " " in flight.name:
			self.assertIn("%20", query_value)

	def test_changing_gate_number_enqueues_sync_job(self):
		flight = create_test_flight()
		enqueued = []

		def capture_enqueue(method, **kwargs):
			enqueued.append((method, kwargs))

		with patch("frappe.enqueue", side_effect=capture_enqueue):
			flight.gate_number = "A1"
			flight.save()

		self.assertEqual(len(enqueued), 1)
		self.assertIn("sync_tickets_gate_for_flight", enqueued[0][0])
		self.assertEqual(enqueued[0][1].get("flight_name"), flight.name)

	def test_flight_gate_save_propagates_to_tickets_when_worker_runs_inline(self):
		"""Mirrors production `frappe.enqueue` by invoking the worker synchronously."""

		def dequeue(method, **kwargs):
			if "sync_tickets_gate_for_flight" in method:
				frappe.get_attr(method)(flight_name=kwargs["flight_name"])
			elif "make_notification_logs" in method:
				frappe.get_attr(method)(kwargs["doc"], kwargs["users"])
			else:
				raise AssertionError(f"unexpected frappe.enqueue target: {method!r}")

		flight = create_test_flight()
		ticket = create_test_ticket(flight=flight.name)
		self.assertFalse(frappe.db.get_value("Airplane Ticket", ticket.name, "gate_number"))

		flight.gate_number = "Z9"
		with patch("frappe.enqueue", side_effect=dequeue):
			flight.save()

		self.assertEqual(frappe.db.get_value("Airplane Ticket", ticket.name, "gate_number"), "Z9")
		self.assertTrue(frappe.db.get_value("Airplane Ticket", ticket.name, "gate_number_changed_on"))

	def test_sync_job_is_no_op_when_ticket_gate_already_matches_flight(self):
		flight = create_test_flight(gate_number="P1")
		ticket = create_test_ticket(flight=flight.name)
		self.assertEqual(ticket.gate_number, "P1")

		sync_tickets_gate_for_flight(flight.name)

		self.assertIsNone(frappe.db.get_value("Airplane Ticket", ticket.name, "gate_number_changed_on"))

	def test_sync_job_updates_ticket_gate_and_stamp(self):
		flight = create_test_flight(gate_number="G1")
		pax_user = "Administrator"
		passenger = create_test_passenger(user=pax_user)
		ticket = create_test_ticket(flight=flight.name, passenger=passenger)
		self.assertEqual(ticket.gate_number, "G1")

		frappe.db.set_value("Airplane Flight", flight.name, "gate_number", "G9", update_modified=False)
		sync_tickets_gate_for_flight(flight.name)

		changed_on = frappe.db.get_value("Airplane Ticket", ticket.name, "gate_number_changed_on")
		self.assertEqual(frappe.db.get_value("Airplane Ticket", ticket.name, "gate_number"), "G9")
		self.assertTrue(changed_on)

	def test_sync_job_skips_cancelled_tickets(self):
		flight = create_test_flight(gate_number="G1")
		ticket = create_test_ticket(flight=flight.name)
		ticket.status = "Boarded"
		ticket.submit()
		ticket.cancel()

		frappe.db.set_value("Airplane Flight", flight.name, "gate_number", "G9", update_modified=False)
		sync_tickets_gate_for_flight(flight.name)

		self.assertEqual(frappe.db.get_value("Airplane Ticket", ticket.name, "gate_number"), "G1")
		self.assertIsNone(frappe.db.get_value("Airplane Ticket", ticket.name, "gate_number_changed_on"))

	def test_sync_job_publishes_realtime_per_passenger_user(self):
		flight = create_test_flight(gate_number="X1")
		passenger = create_test_passenger(user="Administrator")
		ticket = create_test_ticket(flight=flight.name, passenger=passenger)

		frappe.db.set_value("Airplane Flight", flight.name, "gate_number", "X2", update_modified=False)

		published = []

		def capture_pub(*args, **kwargs):
			if args:
				published.append(dict(event=args[0], **kwargs))
			else:
				published.append(kwargs)

		with patch("frappe.publish_realtime", side_effect=capture_pub):
			sync_tickets_gate_for_flight(flight.name)

		gate_events = [p for p in published if p.get("event") == GATE_CHANGE_REALTIME_EVENT]
		self.assertEqual(len(gate_events), 1)
		self.assertEqual(gate_events[0]["user"], "Administrator")
		msg = gate_events[0]["message"]
		self.assertEqual(msg["ticket"], ticket.name)
		self.assertEqual(msg["flight"], flight.name)
		self.assertEqual(msg["old_gate"], "X1")
		self.assertEqual(msg["new_gate"], "X2")
		self.assertIn("view_ticket_url", msg)
		self.assertIn(BOOK_FLIGHT_WEB_FORM_ROUTE, msg["view_ticket_url"])
		self.assertNotIn("/app/Form/", msg["view_ticket_url"])

	def test_sync_job_creates_notification_log_for_passenger(self):
		flight = create_test_flight(gate_number="N1")
		passenger = create_test_passenger(user="Administrator")
		ticket = create_test_ticket(flight=flight.name, passenger=passenger)

		frappe.db.set_value("Airplane Flight", flight.name, "gate_number", "N2", update_modified=False)
		sync_tickets_gate_for_flight(flight.name)

		self.assertTrue(
			frappe.db.exists(
				"Notification Log",
				{
					"for_user": "Administrator",
					"document_type": "Airplane Ticket",
					"document_name": ticket.name,
				},
			)
		)
