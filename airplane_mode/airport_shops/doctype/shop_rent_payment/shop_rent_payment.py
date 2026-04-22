# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ShopRentPayment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		airport_code: DF.Data | None
		amended_from: DF.Link | None
		amount_due: DF.Currency
		date_payed: DF.Date | None
		date_posted: DF.Date | None
		lease_contract: DF.Link
		period_end: DF.Date | None
		period_start: DF.Date | None
		tenant: DF.Link | None
		tenant_email: DF.Data | None
	# end: auto-generated types
	pass
