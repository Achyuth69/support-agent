"""
Zendesk integration — create/update tickets and fetch user info.
Uses the Zendesk REST API directly.
"""
import logging
from typing import Optional

import requests
from requests.auth import HTTPBasicAuth

from config import ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN

logger = logging.getLogger(__name__)

BASE_URL = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2"


def _auth():
    return HTTPBasicAuth(f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)


def _headers():
    return {"Content-Type": "application/json"}


def create_ticket(
    subject: str,
    body: str,
    requester_email: str,
    requester_name: str = "Customer",
    priority: str = "normal",
    tags: list = None,
) -> Optional[dict]:
    """Create a Zendesk ticket."""
    if not ZENDESK_SUBDOMAIN:
        logger.warning("Zendesk not configured")
        return None
    payload = {
        "ticket": {
            "subject": subject,
            "comment": {"body": body},
            "requester": {"name": requester_name, "email": requester_email},
            "priority": priority,
            "tags": tags or ["ai-agent"],
        }
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/tickets.json",
            json=payload,
            auth=_auth(),
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("ticket")
    except Exception as e:
        logger.error(f"Zendesk create_ticket error: {e}")
        return None


def update_ticket(ticket_id: str, status: str = None, comment: str = None) -> bool:
    """Update a Zendesk ticket status or add a comment."""
    if not ZENDESK_SUBDOMAIN:
        return False
    payload: dict = {"ticket": {}}
    if status:
        payload["ticket"]["status"] = status
    if comment:
        payload["ticket"]["comment"] = {"body": comment, "public": False}
    try:
        resp = requests.put(
            f"{BASE_URL}/tickets/{ticket_id}.json",
            json=payload,
            auth=_auth(),
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Zendesk update_ticket error: {e}")
        return False


def get_ticket(ticket_id: str) -> Optional[dict]:
    if not ZENDESK_SUBDOMAIN:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/tickets/{ticket_id}.json",
            auth=_auth(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("ticket")
    except Exception as e:
        logger.error(f"Zendesk get_ticket error: {e}")
        return None


def search_tickets(query: str) -> list:
    """Search Zendesk tickets."""
    if not ZENDESK_SUBDOMAIN:
        return []
    try:
        resp = requests.get(
            f"{BASE_URL}/search.json",
            params={"query": f"type:ticket {query}"},
            auth=_auth(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        logger.error(f"Zendesk search error: {e}")
        return []
