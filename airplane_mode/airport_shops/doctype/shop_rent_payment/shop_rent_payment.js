// Copyright (c) 2026, ALYF and contributors
// For license information, please see license.txt
// Desk: primary action label for submittable **Shop Rent Payment**.

frappe.ui.form.on("Shop Rent Payment", {
	refresh(frm) {
		frappe.after_ajax(() => {
			if (frm.is_new() || frm.doc.docstatus !== 0) {
				return;
			}
			if (frm.toolbar?.current_status !== "Submit") {
				return;
			}
			frm.page.set_primary_action(__("Mark as Paid"), () => frm.savesubmit());
		});
	},
});
