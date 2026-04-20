"""
Ticket management with SLA tracking.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from config import SLA_RESPONSE_TIME, SLA_RESOLUTION_TIME

# In-memory ticket store (replace with DB in production)
_tickets: dict = {}


PRIORITY_MAP = {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
}

STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
STATUS_ESCALATED = "escalated"
STATUS_RESOLVED = "resolved"
STATUS_CLOSED = "closed"


def create_ticket(
    customer_id: str,
    subject: str,
    description: str,
    channel: str = "chat",
    priority: str = "medium",
    language: str = "en",
    zendesk_id: Optional[str] = None,
    sf_case_id: Optional[str] = None,
) -> dict:
    ticket_id = str(uuid.uuid4())[:8].upper()
    now = datetime.utcnow()
    ticket = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "subject": subject,
        "description": description,
        "channel": channel,
        "priority": priority,
        "language": language,
        "status": STATUS_OPEN,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "sla_response_due": (now + timedelta(minutes=SLA_RESPONSE_TIME)).isoformat(),
        "sla_resolution_due": (now + timedelta(minutes=SLA_RESOLUTION_TIME)).isoformat(),
        "sla_breached": False,
        "zendesk_id": zendesk_id,
        "sf_case_id": sf_case_id,
        "notes": [],
        "assigned_to": None,
    }
    _tickets[ticket_id] = ticket
    return ticket


def get_ticket(ticket_id: str) -> Optional[dict]:
    return _tickets.get(ticket_id)


def update_ticket(ticket_id: str, **kwargs) -> Optional[dict]:
    ticket = _tickets.get(ticket_id)
    if not ticket:
        return None
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    ticket.update(kwargs)
    return ticket


def add_note(ticket_id: str, note: str, author: str = "agent") -> Optional[dict]:
    ticket = _tickets.get(ticket_id)
    if not ticket:
        return None
    ticket["notes"].append({
        "author": author,
        "note": note,
        "timestamp": datetime.utcnow().isoformat()
    })
    ticket["updated_at"] = datetime.utcnow().isoformat()
    return ticket


def check_sla_breach(ticket_id: str) -> dict:
    """Check if SLA has been breached for a ticket."""
    ticket = _tickets.get(ticket_id)
    if not ticket:
        return {"breached": False, "reason": "Ticket not found"}

    now = datetime.utcnow()
    response_due = datetime.fromisoformat(ticket["sla_response_due"])
    resolution_due = datetime.fromisoformat(ticket["sla_resolution_due"])

    breached = False
    reasons = []

    if ticket["status"] == STATUS_OPEN and now > response_due:
        breached = True
        reasons.append("Response SLA breached")

    if ticket["status"] not in (STATUS_RESOLVED, STATUS_CLOSED) and now > resolution_due:
        breached = True
        reasons.append("Resolution SLA breached")

    if breached:
        ticket["sla_breached"] = True

    return {"breached": breached, "reasons": reasons, "ticket_id": ticket_id}


def list_customer_tickets(customer_id: str) -> list:
    return [t for t in _tickets.values() if t["customer_id"] == customer_id]


def get_open_tickets() -> list:
    return [t for t in _tickets.values() if t["status"] not in (STATUS_RESOLVED, STATUS_CLOSED)]
