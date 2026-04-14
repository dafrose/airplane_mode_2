# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class FlightPassenger(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        date_of_birth: DF.Date
        first_name: DF.Data
        full_name: DF.Data | None
        last_name: DF.Data | None
        name: DF.Int | None
    # end: auto-generated types

    def before_save(self):
        self.full_name = self._make_full_name()

    def _make_full_name(self):
        first = (self.first_name or "").strip()
        last = (self.last_name or "").strip()
        if last:
            return f"{first} {last}".strip()
        return first
