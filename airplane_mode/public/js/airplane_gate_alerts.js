// Copyright (c) 2026, ALYF and contributors
// For license information, please see license.txt

(function () {
	function escapeHtml(text) {
		if (text === null || text === undefined) {
			return "";
		}
		const div = document.createElement("div");
		div.textContent = String(text);
		return div.innerHTML;
	}

	function showGateChangeAlert(data) {
		if (!data || !data.ticket) {
			return;
		}
		const oldGate =
			data.old_gate != null && data.old_gate !== "" ? data.old_gate : __("unknown");
		const newGate =
			data.new_gate != null && data.new_gate !== "" ? data.new_gate : __("unknown");
		const ticket = escapeHtml(data.ticket);
		const flight = escapeHtml(data.flight || "");
		const lines = [
			`<p>${__("Your boarding gate was updated for ticket")} <strong>${ticket}</strong>${
				flight ? ` ${__("on flight")} <strong>${flight}</strong>` : ""
			}.</p>`,
			`<p>${__("Previous gate:")} ${escapeHtml(oldGate)} → ${__("New gate:")} ${escapeHtml(
				newGate
			)}</p>`,
		];
		if (data.view_ticket_url) {
			const href = String(data.view_ticket_url).replace(/"/g, "%22");
			lines.push(
				`<p><a class="btn btn-primary btn-sm" href="${href}">${__("View ticket")}</a></p>`
			);
		}
		frappe.msgprint({
			title: __("Gate update"),
			message: lines.join(""),
			indicator: "blue",
			wide: true,
		});
	}

	function setupRealtimeListener() {
		if (!frappe.realtime || frappe.boot.disable_async) {
			return;
		}
		const port = frappe.boot.socketio_port || 9000;
		frappe.realtime.init(port, false);
		frappe.realtime.on("airplane_ticket_gate_change", showGateChangeAlert);
	}

	frappe.ready(function () {
		if (!frappe.session || frappe.session.user === "Guest") {
			return;
		}
		setupRealtimeListener();
	});
})();
