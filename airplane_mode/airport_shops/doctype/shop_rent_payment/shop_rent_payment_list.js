// Copyright (c) 2026, ALYF and contributors
// For license information, please see license.txt

frappe.listview_settings["Shop Rent Payment"] = {
	has_indicator_for_draft: true,
	onload(listview) {
		const canTriggerManually =
			frappe.user.has_role("System Manager") ||
			frappe.user.has_role("Airport Authority Personnel");

		if (!canTriggerManually) {
			return;
		}

		listview.page.add_inner_button(__("Create Due Payments Now"), () => {
			frappe.confirm(
				__("Queue rent-payment creation for all due lease contracts now?"),
				() => {
					frappe.call({
						method: "airplane_mode.airport_shops.tasks.enqueue_create_due_shop_rent_payments",
						freeze: true,
						freeze_message: __("Queuing rent-payment creation..."),
						callback: () => {
							frappe.show_alert(
								{
									message: __("Rent-payment creation has been queued."),
									indicator: "green",
								},
								5
							);
							listview.refresh();
						},
					});
				}
			);
		});
	},
};
