"""
WhatsApp (via Twilio) and Email sending integrations.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
)

logger = logging.getLogger(__name__)


# ─── WhatsApp ────────────────────────────────────────────────────────────────

def send_whatsapp(to_number: str, message: str) -> bool:
    """
    Send a WhatsApp message via Twilio.
    to_number should be in format: +91XXXXXXXXXX
    """
    if not TWILIO_ACCOUNT_SID:
        logger.warning("Twilio not configured, skipping WhatsApp send")
        return False
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
        )
        logger.info(f"WhatsApp sent: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp send failed: {e}")
        return False


def parse_whatsapp_webhook(payload: dict) -> dict:
    """Parse incoming Twilio WhatsApp webhook payload."""
    return {
        "from": payload.get("From", "").replace("whatsapp:", ""),
        "body": payload.get("Body", ""),
        "media_url": payload.get("MediaUrl0"),
        "message_sid": payload.get("MessageSid"),
    }


# ─── Email ───────────────────────────────────────────────────────────────────

def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
) -> bool:
    """Send an email via SMTP."""
    if not SMTP_USER:
        logger.warning("SMTP not configured, skipping email send")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_email

        msg.attach(MIMEText(body_text, "plain"))
        if body_html:
            msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())

        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def send_ticket_confirmation(to_email: str, ticket_id: str, subject: str) -> bool:
    """Send a ticket creation confirmation email."""
    text = (
        f"Thank you for contacting support.\n\n"
        f"Your ticket ID is: {ticket_id}\n"
        f"Subject: {subject}\n\n"
        f"Our team will get back to you within the SLA window.\n"
        f"You can reply to this email to add more details."
    )
    html = f"""
    <html><body>
    <p>Thank you for contacting support.</p>
    <p><strong>Ticket ID:</strong> {ticket_id}<br>
    <strong>Subject:</strong> {subject}</p>
    <p>Our team will get back to you within the SLA window.</p>
    </body></html>
    """
    return send_email(to_email, f"[Ticket #{ticket_id}] {subject}", text, html)
