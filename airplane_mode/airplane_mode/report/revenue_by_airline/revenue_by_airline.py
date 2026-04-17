# Copyright (c) 2026, ALYF and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Coalesce, Sum
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()

	Airline = DocType("Airline")
	Airplane = DocType("Airplane")
	Flight = DocType("Airplane Flight")
	Ticket = DocType("Airplane Ticket")

	revenue_expr = Coalesce(Sum(Ticket.total_amount), 0)
	data = (
		frappe.qb.from_(Airline)
		.left_join(Airplane)
		.on(Airplane.airline == Airline.name)
		.left_join(Flight)
		.on(Flight.airplane == Airplane.name)
		.left_join(Ticket)
		.on((Ticket.flight == Flight.name) & (Ticket.docstatus == 1))
		.select(
			Airline.name.as_("airline"),
			revenue_expr.as_("revenue"),
		)
		.groupby(Airline.name)
		.orderby(revenue_expr, order=frappe.qb.desc)
	).run(as_dict=True)

	total = flt(sum(flt(row["revenue"]) for row in data))
	chart = get_chart(data)
	report_summary = [
		{
			"value": total,
			"indicator": "Blue",
			"label": _("Total Revenue"),
			"datatype": "Currency",
		}
	]

	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{
			"label": _("Airline"),
			"fieldname": "airline",
			"fieldtype": "Link",
			"options": "Airline",
			"width": 240,
		},
		{
			"label": _("Revenue"),
			"fieldname": "revenue",
			"fieldtype": "Currency",
			"width": 160,
		},
	]


def get_chart(data):
	labels = [row["airline"] for row in data]
	values = [flt(row["revenue"]) for row in data]
	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Revenue"), "values": values}],
		},
		"type": "donut",
	}
