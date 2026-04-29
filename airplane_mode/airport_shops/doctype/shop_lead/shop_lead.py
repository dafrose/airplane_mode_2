# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ShopLead(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		email: DF.Data | None
		first_name: DF.Data
		last_name: DF.Data
		phone: DF.Phone | None
		projected_start_date: DF.Date | None
		shop: DF.Link
		status: DF.Literal["New", "Contacted", "Scheduled", "Signed", "Withdrawn"]
	# end: auto-generated types
	pass
