import frappe
from frappe import _

@frappe.whitelist()
def get_messages(reference_doctype, reference_name, mobile_no):
    """Get Whapi messages for a document using mobile number"""
    if not mobile_no:
        frappe.throw(_("Mobile number is required"))

    # Get messages using mobile number like whapi_chat app
    messages = frappe.get_all(
        "Whapi Message",
        filters={},  # No base filters
        or_filters=[
            ["from", "=", mobile_no],  # Incoming messages from this contact
            ["to", "=", mobile_no]     # Outgoing messages to this contact
        ],
        fields=[
            "name", "type", "status", "message", "raw_message", "from", "to", "creation",
            "attach", "content_type", "whapi_channel", "reference_doctype", "reference_name"
        ],
        order_by="creation asc"
    )

    # Convert datetime objects to strings and get actual file URLs
    for message in messages:
        for field in ["creation", "modified", "timestamp"]:
            if message.get(field):
                message[field] = str(message[field])
        
        # If there's an attachment, try to get the actual file URL
        if message.get("attach"):
            try:
                # Try to get the file document
                file_doc = frappe.get_doc("File", {"file_url": message["attach"]})
                if file_doc and file_doc.file_url:
                    # Use the actual file URL from the File doctype
                    message["attach"] = file_doc.file_url
                    # Also add file name if available
                    if file_doc.file_name:
                        message["file_name"] = file_doc.file_name
                    # Add mime type if available
                    if file_doc.content_type:
                        message["mime_type"] = file_doc.content_type
                    
                    # Debug: Log the file URL being used
                    frappe.logger().debug(f"File URL for message {message.get('name')}: {file_doc.file_url}")
                else:
                    # If file doesn't exist, remove the attachment
                    frappe.logger().warning(f"File document exists but has no file_url for message {message.get('name')}")
                    message["attach"] = None
                    message["content_type"] = "text"
            except frappe.DoesNotExistError:
                # File doesn't exist, remove the attachment
                frappe.logger().warning(f"File not found for message {message.get('name')}: {message.get('attach')}")
                message["attach"] = None
                message["content_type"] = "text"
            except Exception as e:
                # Log error but continue
                frappe.log_error(f"Error getting file for message {message.get('name')}: {str(e)}")
                message["attach"] = None
                message["content_type"] = "text"

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
        channels = frappe.get_all("Whapi Channel", limit=1)
        if not channels:
            frappe.throw(_("No Whapi Channel found. Please configure a Whapi Channel first."))
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