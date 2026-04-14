# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class AirplaneTicket(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from airplane_mode.airplane_mode.doctype.airplane_ticket_add_on_item.airplane_ticket_add_on_item import AirplaneTicketAddonItem
        from frappe.types import DF

        add_ons: DF.Table[AirplaneTicketAddonItem]
        amended_from: DF.Link | None
        departure_date: DF.Date
        departure_time: DF.Time
        destination_airport: DF.Link
        destination_airport_code: DF.ReadOnly
        duration_of_flight: DF.Duration
        flight: DF.Link
        flight_price: DF.Currency
        passenger: DF.Link
        source_airport: DF.Link
        source_airport_code: DF.ReadOnly
        status: DF.Literal["Booked", "Checked-In", "Boarded"]
        total_price: DF.Currency
    # end: auto-generated types

    def validate(self):
        self._dedupe_add_ons()
        addon_total = sum(flt(row.amount) for row in self.add_ons)
        self.total_price = flt(self.flight_price) + addon_total

    def on_submit(self):
        if self.status != "Boarded":
            frappe.throw(
                _("Only tickets with status {0} can be submitted.")
                .format(frappe.bold("Boarded")),
                title=_("Cannot Submit"),
            )

    def _dedupe_add_ons(self):
        """Remove duplicate add-ons from the list."""
        if not self.add_ons:
            return

        seen = set()
        rows_to_remove = []
        for row in self.add_ons:
            if row.item in seen:
                rows_to_remove.append(row)
            else:
                seen.add(row.item)

        if not rows_to_remove:
            return

        for row in rows_to_remove:
            self.remove(row)

        frappe.msgprint(
            _("Removed {0} duplicate add-on row(s). Each add-on type can only appear once.").format(
                len(rows_to_remove)
            ),
            title=_("Duplicate add-ons"),
            indicator="orange",
            alert=True,
        )
