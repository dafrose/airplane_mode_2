# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document

_SHOP_TENANT_ROLE = "Shop Tenant"


def _grant_shop_tenant_access(user: str, tenant_name: str) -> None:
	frappe.permissions.add_user_permission(
		"Shop Tenant",
		tenant_name,
		user,
		ignore_permissions=True,
	)
	frappe.get_doc("User", user).add_roles(_SHOP_TENANT_ROLE)


def _revoke_shop_tenant_access(user: str, tenant_name: str) -> None:
	if not user:
		return
	user_permission = frappe.db.get_value(
		"User Permission",
		{"user": user, "allow": "Shop Tenant", "for_value": tenant_name},
		"name",
	)
	if user_permission:
		frappe.delete_doc("User Permission", user_permission, ignore_permissions=True, force=True)

	remaining = frappe.db.count("User Permission", {"user": user, "allow": "Shop Tenant"})
	if remaining == 0:
		frappe.get_doc("User", user).remove_roles(_SHOP_TENANT_ROLE)


class ShopTenant(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		address: DF.SmallText | None
		email: DF.Data
		first_name: DF.Data
		full_name: DF.Data | None
		last_name: DF.Data
		phone: DF.Phone | None
		user: DF.Link | None
	# end: auto-generated types

	def before_save(self) -> None:
		if self.is_new():
			self._shop_tenant_prev_user = None
		else:
			self._shop_tenant_prev_user = frappe.db.get_value("Shop Tenant", self.name, "user")

	def after_insert(self) -> None:
		self._sync_linked_user_access()

	def on_update(self) -> None:
		self._sync_linked_user_access()

	def on_trash(self) -> None:
		if self.user:
			_revoke_shop_tenant_access(self.user, self.name)

	def validate(self) -> None:
		self.full_name = f"{self.first_name} {self.last_name}"

	def _sync_linked_user_access(self) -> None:
		prev = getattr(self, "_shop_tenant_prev_user", None)
		new = self.get("user")
		if prev == new:
			return
		if prev:
			_revoke_shop_tenant_access(prev, self.name)
		if new:
			_grant_shop_tenant_access(new, self.name)
