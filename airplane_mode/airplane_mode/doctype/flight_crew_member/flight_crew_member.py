# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FlightCrewMember(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		employee: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		role: DF.Literal["Captain", "First Officer", "Cabin Crew"]
	# end: auto-generated types
	pass
