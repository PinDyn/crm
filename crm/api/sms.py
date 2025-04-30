import frappe
import json
from frappe import _
from frappe.core.doctype.sms_settings.sms_settings import send_sms

def on_update(doc, method):
    frappe.publish_realtime(
        "sms_message",
        {
            "reference_doctype": doc.reference_doctype,
            "reference_name": doc.reference_name,
        },
    )

@frappe.whitelist()
def is_sms_enabled():
    if not frappe.db.exists("DocType", "SMS Settings"):
        return False
    return frappe.get_cached_value("SMS Settings", "SMS Settings", "enabled")

@frappe.whitelist()
def is_sms_installed():
    if not frappe.db.exists("DocType", "SMS Settings"):
        return False
    return True

@frappe.whitelist()
def get_sms_messages(reference_doctype, reference_name):
    if not frappe.db.exists("DocType", "SMS Message"):
        return []
    messages = []

    if reference_doctype == "CRM Deal":
        lead = frappe.db.get_value(reference_doctype, reference_name, "lead")
        if lead:
            messages = frappe.get_all(
                "SMS Message",
                filters={
                    "reference_doctype": "CRM Lead",
                    "reference_name": lead,
                },
                fields=[
                    "name",
                    "type",
                    "to",
                    "from",
                    "message",
                    "message_id",
                    "is_reply",
                    "reply_to_message_id",
                    "creation",
                    "status",
                    "reference_doctype",
                    "reference_name",
                ],
            )

    messages += frappe.get_all(
        "SMS Message",
        filters={
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
        },
        fields=[
            "name",
            "type",
            "to",
            "from",
            "message",
            "message_id",
            "is_reply",
            "reply_to_message_id",
            "creation",
            "status",
            "reference_doctype",
            "reference_name",
        ],
    )

    # Filter messages to get only replies
    reply_messages = [message for message in messages if message["is_reply"]]

    # Iterate through reply messages
    for reply_message in reply_messages:
        # Find the message that this message is replying to
        replied_message = next(
            (m for m in messages if m["message_id"] == reply_message["reply_to_message_id"]),
            None,
        )

        # If the replied message is found, add the reply details to the reply message
        if replied_message:
            reply_message["reply_message"] = replied_message["message"]
            reply_message["reply_to"] = replied_message["name"]
            reply_message["reply_to_type"] = replied_message["type"]

    return messages

@frappe.whitelist()
def create_sms_message(
    reference_doctype,
    reference_name,
    message,
    to,
    reply_to=None,
):
    # Create SMS Message doc
    doc = frappe.new_doc("SMS Message")

    if reply_to:
        reply_doc = frappe.get_doc("SMS Message", reply_to)
        doc.update(
            {
                "is_reply": True,
                "reply_to_message_id": reply_doc.message_id,
            }
        )

    doc.update(
        {
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "message": message,
            "to": to,
        }
    )
    doc.insert(ignore_permissions=True)

    # Send SMS using ERPNext's SMS functionality
    try:
        send_sms([to], message)
        doc.status = "Sent"
    except Exception as e:
        doc.status = "Failed"
        frappe.log_error(f"Failed to send SMS: {str(e)}")
    
    doc.save(ignore_permissions=True)
    return doc.name 