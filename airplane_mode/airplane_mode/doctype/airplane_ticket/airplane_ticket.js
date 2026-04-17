// Copyright (c) 2026, ALYF and contributors
// For license information, please see license.txt

frappe.ui.form.on("Airplane Ticket", {
	refresh(frm) {
		if (frm.doc.docstatus !== 0) {
			return;
		}

		frm.add_custom_button(
			__("Assign Seat"),
			() => {
				frappe.prompt(
					[
						{
							fieldname: "seat",
							fieldtype: "Data",
							label: __("Seat"),
							reqd: 1,
							default: frm.doc.seat || "",
						},
					],
					(values) => {
						frappe.run_serially([
							() => frm.set_value("seat", values.seat),
							() => frm.save(),
						]);
					},
					__("Assign Seat"),
					__("Assign")
				);
			},
			__("Actions")
		);
	},
});
