# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Shop(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		airport: DF.Link
		airport_code: DF.Data | None
		area: DF.Float
		is_published: DF.Check
		shop_number: DF.Int
		shop_type: DF.Data | None
		status: DF.Literal["Available", "Occupied"]
	# end: auto-generated types
	pass
