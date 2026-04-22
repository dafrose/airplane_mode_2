<p>Dear {{doc.tenant}},</p>

<p>This is a reminder that <strong>rent is due</strong> for your shop lease.</p>

<ul>
  <li><strong>Payment</strong>: {{ doc.name }}</li>
  <li><strong>Lease</strong>: {{ doc.lease_contract }}</li>
  {% if doc.period_start %}<li><strong>Period</strong>: {{ frappe.utils.format_date(doc.period_start) }}{% if doc.period_end %} – {{ frappe.utils.format_date(doc.period_end) }}{% endif %}</li>{% endif %}
  <li><strong>Amount due</strong>: {{ frappe.utils.fmt_money(doc.amount_due, currency=frappe.db.get_value("Company", frappe.defaults.get_user_default("Company"), "default_currency") or "EUR") }}</li>
</ul>

<p>Please arrange payment as agreed. If you have questions, reply to this email or contact the airport leasing office.</p>

<p>Thank you,<br>{{ frappe.utils.get_defaults().get("company") or "Airport leasing" }}</p>