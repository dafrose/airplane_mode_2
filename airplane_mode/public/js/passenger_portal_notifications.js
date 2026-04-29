// Copyright (c) 2026, ALYF and contributors
// For license information, please see license.txt

(function () {
	const PORTAL_LOGS = "airplane_mode.portal_notifications.get_portal_notification_logs";
	const PORTAL_HIDE_ONE = "airplane_mode.portal_notifications.hide_portal_notification";
	const PORTAL_HIDE_ALL = "airplane_mode.portal_notifications.hide_all_portal_notifications";

	function portalNotifyError(r) {
		var msg = __("Could not update notifications.");
		var payload = r && (r.responseJSON || r);
		if (payload && payload._server_messages) {
			try {
				var arr = JSON.parse(payload._server_messages);
				var first = arr[0];
				var parsed = typeof first === "string" ? JSON.parse(first) : first;
				if (parsed && parsed.message) {
					msg = parsed.message;
				}
			} catch (e) {
				/* keep default */
			}
		}
		frappe.msgprint({ title: __("Error"), indicator: "red", message: msg });
	}

	function escapeHtml(text) {
		if (text === null || text === undefined) {
			return "";
		}
		const div = document.createElement("div");
		div.textContent = String(text);
		return div.innerHTML;
	}

	function stripHtml(html) {
		if (!html) {
			return "";
		}
		const d = document.createElement("div");
		d.innerHTML = html;
		return (d.textContent || d.innerText || "").trim();
	}

	function unreadCount(logs) {
		return (logs || []).filter(function (l) {
			return !Number(l.read);
		}).length;
	}

	function setUnreadBadge(root, logs) {
		const badge = root.querySelector("[data-notification-badge]");
		if (!badge) {
			return;
		}
		const n = unreadCount(logs);
		if (n > 0) {
			badge.textContent = String(n);
			badge.classList.remove("hide");
		} else {
			badge.classList.add("hide");
		}
	}

	function setupRealtimeForNotifications(onRefresh) {
		if (!frappe.realtime || frappe.boot.disable_async) {
			return;
		}
		const port = frappe.boot.socketio_port || 9000;
		frappe.realtime.init(port, false);
		frappe.realtime.on("notification", function () {
			onRefresh();
		});
	}

	function renderList(root, logs) {
		const ul = root.querySelector("[data-notification-list]");
		const empty = root.querySelector("[data-notification-empty]");
		if (!ul) {
			return;
		}
		ul.innerHTML = "";
		if (!logs || !logs.length) {
			empty && empty.classList.remove("hide");
			return;
		}
		empty && empty.classList.add("hide");
		logs.forEach(function (log) {
			const li = document.createElement("li");
			li.className = "passenger-notification-item" + (!Number(log.read) ? " unread" : "");
			const dismiss = document.createElement("button");
			dismiss.type = "button";
			dismiss.className = "passenger-notification-dismiss";
			dismiss.setAttribute("aria-label", __("Dismiss from list"));
			dismiss.textContent = "\u00d7";
			dismiss.addEventListener("click", function (e) {
				e.preventDefault();
				e.stopPropagation();
				frappe.call({
					method: PORTAL_HIDE_ONE,
					args: { docname: log.name },
					callback: function () {
						const panel = root.querySelector("[data-notification-panel]");
						const panelOpen = panel && !panel.classList.contains("hide");
						loadNotifications(root, { openPanel: panelOpen });
					},
					error: portalNotifyError,
				});
			});
			const link = document.createElement("a");
			link.href = log.link || "#";
			const title = stripHtml(log.subject) || __("Notification");
			link.innerHTML =
				"<div>" +
				escapeHtml(title) +
				'</div><div class="meta">' +
				escapeHtml(log.creation || "") +
				"</div>";
			link.addEventListener("click", function (e) {
				if (link.getAttribute("href") === "#") {
					e.preventDefault();
				}
				if (!Number(log.read)) {
					frappe.call({
						method: "frappe.desk.doctype.notification_log.notification_log.mark_as_read",
						args: { docname: log.name },
						callback: function () {
							loadNotifications(root, { openPanel: true });
						},
					});
				}
			});
			/* Link first so flex row lays out [content | ×]; avoids float overlap where <a> stole clicks on ×. */
			li.appendChild(link);
			li.appendChild(dismiss);
			ul.appendChild(li);
		});
	}

	function loadNotifications(root, opts) {
		opts = opts || {};
		frappe.call({
			method: PORTAL_LOGS,
			args: { limit: 30 },
			callback: function (r) {
				const logs = (r.message && r.message.notification_logs) || [];
				setUnreadBadge(root, logs);
				if (opts.openPanel) {
					renderList(root, logs);
				}
			},
			error: portalNotifyError,
		});
	}

	function wireBell(root) {
		const toggle = root.querySelector(".passenger-notification-toggle");
		const panel = root.querySelector("[data-notification-panel]");
		const dismissAll = root.querySelector("[data-portal-dismiss-all]");
		if (!toggle || !panel) {
			return;
		}
		toggle.addEventListener("click", function (e) {
			e.preventDefault();
			e.stopPropagation();
			const open = panel.classList.contains("hide");
			panel.classList.toggle("hide", !open);
			toggle.setAttribute("aria-expanded", open ? "true" : "false");
			if (open) {
				loadNotifications(root, { openPanel: true });
			}
		});
		document.addEventListener("click", function (e) {
			if (!root.contains(e.target)) {
				panel.classList.add("hide");
				toggle.setAttribute("aria-expanded", "false");
			}
		});
		if (dismissAll) {
			dismissAll.addEventListener("click", function (e) {
				e.preventDefault();
				e.stopPropagation();
				frappe.call({
					method: PORTAL_HIDE_ALL,
					callback: function () {
						loadNotifications(root, { openPanel: true });
					},
					error: portalNotifyError,
				});
			});
		}
		setupRealtimeForNotifications(function () {
			const panelOpen = !panel.classList.contains("hide");
			loadNotifications(root, { openPanel: panelOpen });
		});
		loadNotifications(root, { openPanel: false });
	}

	frappe.ready(function () {
		if (!frappe.session || frappe.session.user === "Guest") {
			return;
		}
		const root = document.getElementById("passenger-notification-bell");
		if (!root) {
			return;
		}
		wireBell(root);
	});
})();
