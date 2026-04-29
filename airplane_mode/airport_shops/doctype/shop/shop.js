// Copyright (c) 2026, ALYF and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop", {
	refresh(frm) {
		frm.set_query("shop_type", () => ({
			filters: { enabled: 1 },
		}));
	},
});
