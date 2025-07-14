// Copyright (c) 2025, adheena and contributors
// For license information, please see license.txt

frappe.query_reports["Daily Sales Report"] = {
	"filters": [
		{
            "fieldname": "date",
            "label": "Date",
            "fieldtype": "Date"
        },
		{
            "fieldname": "sales_person",
            "label": "Sales Person",
            "fieldtype": "Link",
            "options": "Sales Person"
        }

	]
};

