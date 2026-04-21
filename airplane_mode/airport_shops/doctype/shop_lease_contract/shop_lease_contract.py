# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ShopLeaseContract(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		airport_code: DF.Data | None
		lease_expiry_date: DF.Date | None
		lease_start_date: DF.Date | None
		rent: DF.Currency
		shop: DF.Link
		tenant: DF.Link
	# end: auto-generated types
	pass
