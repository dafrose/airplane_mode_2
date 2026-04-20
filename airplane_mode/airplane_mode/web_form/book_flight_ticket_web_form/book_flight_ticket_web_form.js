// Hide the **Passenger** Link / autocomplete (shows autoincrement id) and show *Full Name* read-only.
// `passenger_display` is set on `frappe.reference_doc` in `book_flight_ticket_web_form.py`.

frappe.init_client_script = () => {
	const PASSENGER_FULL_NAME = frappe.reference_doc?.passenger_display || "";
	const hasPassengerId = Boolean(frappe.reference_doc && frappe.reference_doc.passenger);
	if (!PASSENGER_FULL_NAME || !hasPassengerId) {
		return;
	}

	const field = frappe.web_form.fields_dict.passenger;
	if (!field || !field.$wrapper || !field.$wrapper.length) {
		return;
	}

	field.$wrapper.hide();

	const $display = $(`<div class="frappe-control form-group web-form-passenger-display">
		<label class="control-label">${__("Passenger")}</label>
		<div class="control-input-wrapper">
			<div class="control-value like-disabled-input"></div>
		</div>
	</div>`);
	$display.find(".control-value").text(PASSENGER_FULL_NAME);
	field.$wrapper.before($display);
};
