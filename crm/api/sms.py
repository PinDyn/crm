import frappe
from frappe import _

@frappe.whitelist()
def get_messages(reference_doctype, reference_name):
    """Get Whapi messages for a document"""
    if not reference_doctype or not reference_name:
        frappe.throw(_("Reference Doctype and Reference Name are required"))

    messages = frappe.get_all(
        "Whapi Message",
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

@frappe.whitelist()
def send_message(reference_doctype, reference_name, message, recipient, whapi_channel=None):
    """Send a Whapi message"""
    if not reference_doctype or not reference_name:
        frappe.throw(_("Reference Doctype and Reference Name are required"))
    
    if not message:
        frappe.throw(_("Message is required"))
    
    if not recipient:
        frappe.throw(_("Recipient is required"))

    # Get default whapi channel if not specified
    if not whapi_channel:
        channels = frappe.get_all("Whapi Channel", filters={"enabled": 1}, limit=1)
        if not channels:
            frappe.throw(_("No enabled Whapi Channel found. Please configure a Whapi Channel first."))
        whapi_channel = channels[0].name

    # Create Whapi Message document
    whapi_message = frappe.new_doc("Whapi Message")
    whapi_message.update({
        "type": "Outgoing",
        "to": recipient,
        "message": message,
        "content_type": "text",
        "whapi_channel": whapi_channel,
        "reference_doctype": reference_doctype,
        "reference_name": reference_name
    })
    
    whapi_message.insert(ignore_permissions=True)
    
    return {
        "message": "Message sent successfully",
        "message_id": whapi_message.name
    } 