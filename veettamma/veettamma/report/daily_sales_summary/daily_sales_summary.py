# Copyright (c) 2025, adheena and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []
	columns = get_cloumns()
	data = get_data(filters)
	return columns, data

def get_cloumns():
	columns = [
		{"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 120},
		{"fieldname": "sales_person", "label": "Sales Person", "fieldtype": "Link", "options": "Sales Person", "width": 160},
		{"fieldname": "number_of_paid_invoices", "label": "Number of Paid Invoices", "fieldtype": "Int", "width": 180},
		{"fieldname": "total_amount_paid_invoices", "label": "Total Amount of Paid Invoices", "fieldtype": "Currency", "width": 200},
		{"fieldname": "number_of_partially_paid_invoices", "label": "Number of Partially Paid Invoices", "fieldtype": "Int", "width": 220},
		{"fieldname": "total_amount_partially_paid_invoices", "label": "Total Amount of Partially Paid Invoices", "fieldtype": "Currency", "width": 240},
		{"fieldname": "amount_received_towards_ob", "label": "Amount Received Towards Outstanding", "fieldtype": "Currency", "width": 240},
		{"fieldname": "total_amount", "label": "Total Amount", "fieldtype": "Currency", "width": 200},
		{"fieldname": "cash_amount", "label": "Cash Amount", "fieldtype": "Currency", "width": 150},
		{"fieldname": "upi_amount", "label": "UPI Amount", "fieldtype": "Currency", "width": 150},
		{"fieldname": "bank_transfer_amount", "label": "Bank Transfer Amount", "fieldtype": "Currency", "width": 180},
		{"fieldname": "cheque_amount", "label": "Cheque Amount", "fieldtype": "Currency", "width": 150},
	]
	return columns

def get_data(filters=None):
	if not filters:
		filters = {}

	conditions = "SI.docstatus = 1"
	params = {}

	if filters.get("date"):
		conditions += " AND SI.posting_date = %(date)s"
		params["date"] = filters["date"]

	if filters.get("sales_person"):
		conditions += " AND ST.sales_person = %(sales_person)s"
		params["sales_person"] = filters["sales_person"]

	query = f"""
		SELECT
			SI.posting_date AS date,
			ST.sales_person,
			
			COUNT(CASE WHEN SI.status = 'Paid' THEN 1 END) AS number_of_paid_invoices,
			SUM(CASE WHEN SI.status = 'Paid' THEN SI.grand_total ELSE 0 END) AS total_amount_paid_invoices,

			COUNT(CASE WHEN SI.status = 'Partly Paid' THEN 1 END) AS number_of_partially_paid_invoices,
			SUM(CASE WHEN SI.status = 'Partly Paid' THEN (SI.grand_total - SI.outstanding_amount) ELSE 0 END) AS total_amount_partially_paid_invoices,

			(
				SELECT IFNULL(SUM(PE.paid_amount), 0)
				FROM `tabPayment Entry Reference` PER
				JOIN `tabPayment Entry` PE ON PER.parent = PE.name
				JOIN `tabSales Invoice` SI_OB ON PER.reference_name = SI_OB.name
				JOIN `tabSales Team` ST_OB ON ST_OB.parent = SI_OB.name
				WHERE PER.reference_doctype = 'Sales Invoice'
				AND PE.docstatus = 1
				AND SI_OB.posting_date <> SI.posting_date
				AND PE.posting_date = SI.posting_date
				AND ST_OB.sales_person = ST.sales_person
			) AS amount_received_towards_ob,

			(
				SUM(CASE WHEN SI.status = 'Paid' THEN SI.grand_total ELSE 0 END) +
				SUM(CASE WHEN SI.status = 'Partly Paid' THEN (SI.grand_total - SI.outstanding_amount) ELSE 0 END) +
				(
					SELECT IFNULL(SUM(PE.paid_amount), 0)
					FROM `tabPayment Entry Reference` PER
					JOIN `tabPayment Entry` PE ON PER.parent = PE.name
					JOIN `tabSales Invoice` SI_OB ON PER.reference_name = SI_OB.name
					JOIN `tabSales Team` ST_OB ON ST_OB.parent = SI_OB.name
					WHERE PER.reference_doctype = 'Sales Invoice'
					AND PE.docstatus = 1
					AND SI_OB.posting_date <> SI.posting_date
					AND PE.posting_date = SI.posting_date
					AND ST_OB.sales_person = ST.sales_person
				)
			) AS total_amount,

			(
				SELECT SUM(PE.paid_amount)
				FROM `tabPayment Entry Reference` PER
				JOIN `tabPayment Entry` PE ON PE.name = PER.parent
				JOIN `tabSales Team` ST2 ON PER.reference_name = ST2.parent
				WHERE PER.reference_doctype = 'Sales Invoice'
				AND PE.docstatus = 1
				AND PE.mode_of_payment = 'Cash'
				AND ST2.sales_person = ST.sales_person
				AND PE.posting_date = SI.posting_date
			) AS cash_amount,

			(
				SELECT SUM(PE.paid_amount)
				FROM `tabPayment Entry Reference` PER
				JOIN `tabPayment Entry` PE ON PE.name = PER.parent
				JOIN `tabSales Team` ST2 ON PER.reference_name = ST2.parent
				WHERE PER.reference_doctype = 'Sales Invoice'
				AND PE.docstatus = 1
				AND PE.mode_of_payment = 'UPI'
				AND ST2.sales_person = ST.sales_person
				AND PE.posting_date = SI.posting_date
			) AS upi_amount,

			(
				SELECT SUM(PE.paid_amount)
				FROM `tabPayment Entry Reference` PER
				JOIN `tabPayment Entry` PE ON PE.name = PER.parent
				JOIN `tabSales Team` ST2 ON PER.reference_name = ST2.parent
				WHERE PER.reference_doctype = 'Sales Invoice'
				AND PE.docstatus = 1
				AND PE.mode_of_payment = 'Bank Transfer'
				AND ST2.sales_person = ST.sales_person
				AND PE.posting_date = SI.posting_date
			) AS bank_transfer_amount,

			(
				SELECT SUM(PE.paid_amount)
				FROM `tabPayment Entry Reference` PER
				JOIN `tabPayment Entry` PE ON PE.name = PER.parent
				JOIN `tabSales Team` ST2 ON PER.reference_name = ST2.parent
				WHERE PER.reference_doctype = 'Sales Invoice'
				AND PE.docstatus = 1
				AND PE.mode_of_payment = 'Cheque'
				AND ST2.sales_person = ST.sales_person
				AND PE.posting_date = SI.posting_date
			) AS cheque_amount

		FROM
			`tabSales Invoice` SI
		JOIN
			`tabSales Team` ST
		ON SI.name = ST.parent
		WHERE
			{conditions}
		GROUP BY
			SI.posting_date, ST.sales_person
		ORDER BY
			SI.posting_date DESC, ST.sales_person DESC
	"""

	raw_data = frappe.db.sql(query, params, as_dict=True)

	data = [
		row for row in raw_data if any([
			row.get("total_amount_paid_invoices"),
			row.get("total_amount_partially_paid_invoices"),
			row.get("amount_received_towards_ob"),
			row.get("total_amount"),
			row.get("cash_amount"),
			row.get("upi_amount"),
			row.get("bank_transfer_amount"),
			row.get("cheque_amount")
		])
	]
	return data