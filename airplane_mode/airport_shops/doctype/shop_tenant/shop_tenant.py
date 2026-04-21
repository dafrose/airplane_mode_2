# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ShopTenant(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		address: DF.SmallText | None
		email: DF.Data | None
		first_name: DF.Data
		full_name: DF.Data | None
		last_name: DF.Data
		phone: DF.Phone | None
	# end: auto-generated types

	def validate(self) -> None:
		self.full_name = f"{self.first_name} {self.last_name}"
