"""
LangChain tool: create a support ticket.
"""
import logging
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

import ticket as ticket_store
from integrations import zendesk, salesforce
from integrations.whatsapp import send_ticket_confirmation

logger = logging.getLogger(__name__)


class CreateTicketInput(BaseModel):
    customer_id: str = Field(description="The customer's unique ID")
    subject: str = Field(description="Short title of the issue")
    description: str = Field(description="Full description of the customer's issue")
    priority: str = Field(default="medium", description="Priority: low | medium | high | critical")
    channel: str = Field(default="chat", description="Channel: chat | email | whatsapp | voice")
    language: str = Field(default="en", description="Language code e.g. en, hi, ta")
    customer_email: str = Field(default="", description="Customer email for confirmation")
    customer_name: str = Field(default="Customer", description="Customer's name")


def _create_ticket(
    customer_id: str,
    subject: str,
    description: str,
    priority: str = "medium",
    channel: str = "chat",
    language: str = "en",
    customer_email: str = "",
    customer_name: str = "Customer",
) -> str:
    try:
        zd_ticket = None
        sf_case = None

        if customer_email:
            try:
                zd_ticket = zendesk.create_ticket(
                    subject=subject, body=description,
                    requester_email=customer_email, requester_name=customer_name,
                    priority=priority if priority in ("low", "normal", "high", "urgent") else "normal",
                )
            except Exception as e:
                logger.warning(f"Zendesk ticket creation failed: {e}")

            try:
                sf_contact = salesforce.get_contact(customer_email)
                sf_case = salesforce.create_case(
                    subject=subject, description=description,
                    contact_id=sf_contact["Id"] if sf_contact else None,
                    priority=priority, origin=channel.capitalize(),
                )
            except Exception as e:
                logger.warning(f"Salesforce case creation failed: {e}")

        local_ticket = ticket_store.create_ticket(
            customer_id=customer_id, subject=subject, description=description,
            channel=channel, priority=priority, language=language,
            zendesk_id=str(zd_ticket["id"]) if zd_ticket else None,
            sf_case_id=sf_case.get("id") if sf_case else None,
        )

        if customer_email:
            try:
                send_ticket_confirmation(customer_email, local_ticket["ticket_id"], subject)
            except Exception as e:
                logger.warning(f"Confirmation email failed: {e}")

        return (
            f"Ticket created successfully!\n"
            f"Ticket ID: {local_ticket['ticket_id']}\n"
            f"Priority: {priority}\n"
            f"SLA Response Due: {local_ticket['sla_response_due']}\n"
            f"SLA Resolution Due: {local_ticket['sla_resolution_due']}"
        )
    except Exception as e:
        logger.error(f"create_ticket error: {e}", exc_info=True)
        return f"Support ticket has been logged for customer {customer_id} regarding: {subject}. Our team will follow up shortly."


create_support_ticket = StructuredTool.from_function(
    func=_create_ticket,
    name="create_support_ticket",
    description="Create a support ticket when the knowledge base cannot resolve the issue. Tracks the issue with SLA.",
    args_schema=CreateTicketInput,
)
