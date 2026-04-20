"""
Escalation logic — routes complex/unresolved cases to human agents.
Notifies via webhook, email, or Slack.
"""
import json
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional

import requests

from config import ESCALATION_WEBHOOK_URL, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
from ticket import update_ticket, add_note, STATUS_ESCALATED

logger = logging.getLogger(__name__)

ESCALATION_REASONS = {
    "unresolved": "Agent could not resolve the issue after multiple attempts",
    "angry_customer": "Customer sentiment is highly negative",
    "sla_breach": "SLA breach imminent or already occurred",
    "billing": "Billing/payment dispute requires human review",
    "legal": "Legal or compliance concern raised",
    "manual": "Customer explicitly requested human agent",
}


def escalate_ticket(
    ticket_id: str,
    customer_id: str,
    reason_code: str = "unresolved",
    summary: str = "",
    notify_email: Optional[str] = None,
) -> dict:
    """
    Escalate a ticket to a human agent.
    Returns escalation record.
    """
    reason = ESCALATION_REASONS.get(reason_code, reason_code)
    escalation = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "reason": reason,
        "summary": summary,
        "escalated_at": datetime.utcnow().isoformat(),
        "status": "pending_human",
    }

    # Update ticket status
    update_ticket(ticket_id, status=STATUS_ESCALATED, assigned_to="human_queue")
    add_note(ticket_id, f"Escalated: {reason}. {summary}", author="system")

    # Fire webhook if configured
    if ESCALATION_WEBHOOK_URL:
        _notify_webhook(escalation)

    # Send email notification if provided
    if notify_email:
        _notify_email(notify_email, escalation)

    logger.info(f"Ticket {ticket_id} escalated. Reason: {reason}")
    return escalation


def _notify_webhook(payload: dict):
    try:
        resp = requests.post(
            ESCALATION_WEBHOOK_URL,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Escalation webhook failed: {e}")


def _notify_email(to_email: str, escalation: dict):
    if not SMTP_USER:
        logger.warning("SMTP not configured, skipping email notification")
        return
    try:
        body = (
            f"Ticket {escalation['ticket_id']} has been escalated.\n\n"
            f"Customer: {escalation['customer_id']}\n"
            f"Reason: {escalation['reason']}\n"
            f"Summary: {escalation['summary']}\n"
            f"Time: {escalation['escalated_at']}"
        )
        msg = MIMEText(body)
        msg["Subject"] = f"[ESCALATION] Ticket {escalation['ticket_id']} needs attention"
        msg["From"] = SMTP_USER
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
    except Exception as e:
        logger.error(f"Escalation email failed: {e}")
