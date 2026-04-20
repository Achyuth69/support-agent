"""
Salesforce CRM integration — lookup/create contacts and cases.
Uses simple_salesforce library.
"""
import logging
from typing import Optional

from config import SF_USERNAME, SF_PASSWORD, SF_SECURITY_TOKEN, SF_DOMAIN

logger = logging.getLogger(__name__)

_sf = None


def _get_client():
    global _sf
    if _sf:
        return _sf
    try:
        from simple_salesforce import Salesforce
        _sf = Salesforce(
            username=SF_USERNAME,
            password=SF_PASSWORD,
            security_token=SF_SECURITY_TOKEN,
            domain=SF_DOMAIN,
        )
        return _sf
    except Exception as e:
        logger.error(f"Salesforce connection failed: {e}")
        return None


def get_contact(email: str) -> Optional[dict]:
    """Look up a Salesforce contact by email."""
    sf = _get_client()
    if not sf:
        return None
    try:
        result = sf.query(
            f"SELECT Id, Name, Email, Phone, AccountId FROM Contact WHERE Email = '{email}' LIMIT 1"
        )
        records = result.get("records", [])
        return records[0] if records else None
    except Exception as e:
        logger.error(f"SF get_contact error: {e}")
        return None


def create_case(
    subject: str,
    description: str,
    contact_id: Optional[str] = None,
    priority: str = "Medium",
    origin: str = "Chat",
) -> Optional[dict]:
    """Create a Salesforce Case."""
    sf = _get_client()
    if not sf:
        return None
    try:
        data = {
            "Subject": subject,
            "Description": description,
            "Priority": priority.capitalize(),
            "Origin": origin,
            "Status": "New",
        }
        if contact_id:
            data["ContactId"] = contact_id
        result = sf.Case.create(data)
        return result
    except Exception as e:
        logger.error(f"SF create_case error: {e}")
        return None


def update_case(case_id: str, **kwargs) -> bool:
    """Update a Salesforce Case."""
    sf = _get_client()
    if not sf:
        return False
    try:
        sf.Case.update(case_id, kwargs)
        return True
    except Exception as e:
        logger.error(f"SF update_case error: {e}")
        return False


def get_case(case_id: str) -> Optional[dict]:
    sf = _get_client()
    if not sf:
        return None
    try:
        return sf.Case.get(case_id)
    except Exception as e:
        logger.error(f"SF get_case error: {e}")
        return None
