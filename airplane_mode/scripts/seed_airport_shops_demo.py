# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

"""Insert demo **Airport Shops** data tied to the space airline demo airports.

Expects **Airport** rows *VNS*, *CLP*, and *PHB* (created by ``seed_space_airline_demo``).

Run once per site, e.g.:

	bench --site <site> execute airplane_mode.scripts.seed_airport_shops_demo.seed
"""

from __future__ import annotations

from datetime import date, timedelta

import frappe
from dateutil.relativedelta import relativedelta
from frappe import _
from frappe.utils import getdate

from airplane_mode.airport_shops.doctype.shop_lease_contract.shop_lease_contract import (
	recalculate_shop_status_from_leases,
)

# **Airport** `.name` values from ``seed_space_airline_demo`` (IATA-style codes).
DEMO_AIRPORT_CODES = ("VNS", "CLP", "PHB")

# Fixture **Shop Type** names (see ``fixtures/shop_type.json``); index maps into ``_SHOP_SPECS``.
DEFAULT_SHOP_TYPES: tuple[str, ...] = ("Normal", "Stall", "Walk-through")

# First demo **Shop Tenant** email — used only to detect an existing seed run.
_DEMO_SEED_MARKER_EMAIL = "selene.karman@example.com"

# Per airport: three shops (area m², floors, index into DEFAULT_SHOP_TYPES).
_SHOP_SPECS = (28.0, 1, 0), (52.5, 2, 1), (120.0, 1, 2)

# Lease bundle: (shop_index, tenant_index, rent, lease_start, lease_expiry_or_none, public_shop_name_or_none)
# shop_index follows flattened order: all VNS, then CLP, then PHB.
_LEASES: tuple[tuple[int, int, float, date, date | None, str | None], ...] = (
	(0, 0, 4500.0, date(2026, 1, 1), date(2099, 12, 31), "Aurora Duty-Free Annex"),
	(1, 1, 6200.0, date(2026, 1, 1), date(2099, 12, 31), "Kuiper Noodle Bar"),
	(3, 2, 2800.0, date(2024, 1, 1), date(2025, 12, 1), "Legacy Orbital Outfitters"),
	(6, 3, 5100.0, date(2026, 1, 1), date(2099, 12, 31), "Phobos Pressed Juice"),
	(7, 4, 3900.0, date(2026, 1, 1), None, "Tether News & Gifts"),
)

_LEADS: tuple[tuple[int, str, str, str, date | None, str], ...] = (
	(2, "Mira", "Zenith", "mira.zenith@example.com", date(2026, 6, 1), "New"),
	(4, "Juno", "Lagrange", "juno.lagrange@example.com", date(2026, 7, 15), "Contacted"),
	(8, "Rhea", "Arc", "rhea.arc@example.com", None, "Scheduled"),
)


def _period_end(period_start: date) -> date:
	return period_start + relativedelta(months=1) - timedelta(days=1)


def seed() -> None:
	for code in DEMO_AIRPORT_CODES:
		if not frappe.db.exists("Airport", code):
			frappe.msgprint(
				_("Airport {0} is missing; run the airline demo seed first.").format(code),
				indicator="red",
			)
			return

	if frappe.db.exists("Shop Tenant", {"email": _DEMO_SEED_MARKER_EMAIL}):
		frappe.msgprint(
			_("Airport shops demo already present (tenant {0}).").format(_DEMO_SEED_MARKER_EMAIL),
			indicator="orange",
		)
		return

	for type_name in DEFAULT_SHOP_TYPES:
		if not frappe.db.exists("Shop Type", type_name):
			frappe.msgprint(
				_("Shop Type {0} is missing; run migrate or import Shop Type fixtures.").format(type_name),
				indicator="red",
			)
			return

	shop_names: list[str] = []
	for airport_code in DEMO_AIRPORT_CODES:
		for area, floors, type_idx in _SHOP_SPECS:
			shop = frappe.get_doc(
				{
					"doctype": "Shop",
					"airport": airport_code,
					"area": area,
					"floors": floors,
					"shop_type": DEFAULT_SHOP_TYPES[type_idx],
					"is_published": 1,
				}
			)
			shop.insert(ignore_permissions=True)
			shop_names.append(shop.name)

	tenant_names: list[str] = []
	tenant_rows = (
		("Selene", "Karman", "selene.karman@example.com", "Enceladus Ring 7"),
		("Ganymede", "Frost", "ganymede.frost@example.com", "Callisto Dome 12"),
		("Deimos", "Walker", "deimos.walker@example.com", "Phobos Tether Bay"),
		("Callisto", "Rime", "callisto.rime@example.com", "Jupiter Orbit Hub"),
		("Europa", "Tide", "europa.tide@example.com", "Ice Shelf Terminal"),
	)
	for first, last, email, address in tenant_rows:
		t = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"first_name": first,
				"last_name": last,
				"email": email,
				"address": address,
			}
		)
		t.insert(ignore_permissions=True)
		tenant_names.append(t.name)

	lease_names: list[str] = []
	for shop_i, tenant_i, rent, start, expiry, pub in _LEASES:
		lease = frappe.get_doc(
			{
				"doctype": "Shop Lease Contract",
				"shop": shop_names[shop_i],
				"tenant": tenant_names[tenant_i],
				"rent": rent,
				"lease_start_date": start,
				"lease_expiry_date": expiry,
				"public_shop_name": pub,
			}
		)
		lease.insert(ignore_permissions=True)
		lease_names.append(lease.name)

	for shop in shop_names:
		recalculate_shop_status_from_leases(shop)

	# **Shop Rent Payment** `after_insert` sends the rent reminder only when *Enable Rent Reminders*
	# is on. Submit fires the standard **Notification** (e.g. *Payment Receipt Notification*).
	prev_reminders = frappe.db.get_single_value("Airport Shop Settings", "enable_rent_reminders")
	frappe.db.set_single_value("Airport Shop Settings", "enable_rent_reminders", 1)
	frappe.cache.hdel("notifications", "Shop Rent Payment")

	primary_lease = lease_names[0]
	lease_doc = frappe.get_doc("Shop Lease Contract", primary_lease)
	period_a_start = getdate(lease_doc.lease_start_date)
	period_a_end = _period_end(period_a_start)
	pay_a = frappe.get_doc(
		{
			"doctype": "Shop Rent Payment",
			"lease_contract": primary_lease,
			"amount_due": lease_doc.rent,
			"period_start": period_a_start,
			"period_end": period_a_end,
			"date_posted": period_a_start,
			"status": "Due",
		}
	)
	pay_a.insert(ignore_permissions=True)

	lease_doc.reload()
	period_b_start = getdate(lease_doc.next_due_date)
	period_b_end = _period_end(period_b_start)
	pay_b = frappe.get_doc(
		{
			"doctype": "Shop Rent Payment",
			"lease_contract": primary_lease,
			"amount_due": lease_doc.rent,
			"period_start": period_b_start,
			"period_end": period_b_end,
			"date_posted": period_b_start,
			"status": "Due",
		}
	)
	pay_b.insert(ignore_permissions=True)

	if frappe.db.exists("Print Format", "Payment Receipt Format"):
		frappe.get_doc("Shop Rent Payment", pay_a.name).submit()

	frappe.db.set_single_value("Airport Shop Settings", "enable_rent_reminders", prev_reminders)
	frappe.cache.hdel("notifications", "Shop Rent Payment")

	lead_count = 0
	for shop_i, first, last, email, projected, status in _LEADS:
		frappe.get_doc(
			{
				"doctype": "Shop Lead",
				"shop": shop_names[shop_i],
				"first_name": first,
				"last_name": last,
				"email": email,
				"projected_start_date": projected,
				"status": status,
			}
		).insert(ignore_permissions=True)
		lead_count += 1

	# nosemgrep: frappe-semgrep-rules.rules.frappe-manual-commit
	frappe.db.commit()
	frappe.msgprint(
		_(
			"Created {0} shops (types Normal, Stall, Walk-through), {1} tenants, {2} leases, "
			"rent payments on the primary lease, and {3} shop leads for demo airports."
		).format(len(shop_names), len(tenant_names), len(_LEASES), lead_count),
		indicator="green",
	)
