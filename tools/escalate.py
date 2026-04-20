"""
LangChain tool: escalate to a human agent.
"""
import logging
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from escalation import escalate_ticket

logger = logging.getLogger(__name__)


class EscalateInput(BaseModel):
    customer_id: str = Field(description="The customer's unique ID")
    reason_code: str = Field(
        default="manual",
        description="Reason: unresolved | angry_customer | sla_breach | billing | legal | manual"
    )
    summary: str = Field(default="", description="Brief summary of the issue and what was tried")
    ticket_id: str = Field(default="UNKNOWN", description="Existing ticket ID if available")
    notify_email: str = Field(default="", description="Optional email to notify the human agent")


def _escalate(
    customer_id: str,
    reason_code: str = "manual",
    summary: str = "",
    ticket_id: str = "UNKNOWN",
    notify_email: str = "",
) -> str:
    try:
        result = escalate_ticket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            reason_code=reason_code,
            summary=summary,
            notify_email=notify_email if notify_email else None,
        )
        return (
            f"Escalated to human agent successfully.\n"
            f"Ticket: {ticket_id}\n"
            f"Reason: {result['reason']}\n"
            f"Status: {result['status']}\n"
            "Please inform the customer that a human agent will follow up shortly."
        )
    except Exception as e:
        logger.error(f"Escalation error: {e}", exc_info=True)
        return f"Escalation recorded for customer {customer_id}. A human agent will follow up shortly."


escalate_to_human = StructuredTool.from_function(
    func=_escalate,
    name="escalate_to_human",
    description=(
        "Escalate to a human agent when: customer is angry/distressed, "
        "customer explicitly asks for human, issue involves billing/legal/security, "
        "or you cannot resolve after 2 attempts."
    ),
    args_schema=EscalateInput,
)
