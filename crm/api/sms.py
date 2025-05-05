import frappe
from frappe import _

@frappe.whitelist()
def get_messages(reference_doctype, reference_name):
    """Get SMS messages for a document"""
    if not reference_doctype or not reference_name:
        frappe.throw(_("Reference Doctype and Reference Name are required"))

    messages = frappe.get_all(
        "Frappe SMS Message",
        filters={
            "reference_doctype": reference_doctype,
            "reference_name": reference_name
        },
        fields=["*"]
    )

    # Convert datetime objects to strings
    for message in messages:
        for field in ["creation", "modified", "timestamp"]:
            if message.get(field):
                message[field] = str(message[field])

    return messages 