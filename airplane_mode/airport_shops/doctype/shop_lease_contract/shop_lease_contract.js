// Copyright (c) 2026, ALYF and contributors
// For license information, please see license.txt

// Desk **new** rows are built client-side; prefill *Rent* from the **Single** (server `before_insert` still applies).
frappe.ui.form.on("Shop Lease Contract", {
	refresh(frm) {
		if (!frm.is_new() || flt(frm.doc.rent) > 0 || frm._default_rent_prefill_pending) {
			return;
		}
		frm._default_rent_prefill_pending = 1;
		frappe.db
			.get_single_value("Airport Shop Settings", "default_rent_amount")
			.then((value) => {
				// Form may have been closed, submitted, or *Rent* filled while the request was in flight.
				if (!frm.doc || !frm.is_new() || flt(frm.doc.rent) > 0) {
					return;
				}
				frm.set_value("rent", flt(value));
			})
			.finally(() => {
				frm._default_rent_prefill_pending = 0;
			});
	},
});
