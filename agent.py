"""
Enterprise Customer Support Agent — Core Agent
Uses direct LLM tool calling without AgentExecutor for maximum compatibility.
"""
import json
import logging
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from config import LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, GROQ_API_KEY, GEMINI_API_KEY
from memory import get_memory, update_memory, append_conversation, get_conversation_history
from tools.search_kb import search_knowledge_base
from tools.create_ticket import create_support_ticket
from tools.escalate import escalate_to_human

logger = logging.getLogger(__name__)

TOOLS = [search_knowledge_base, create_support_ticket, escalate_to_human]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

SYSTEM_PROMPT = """You are a warm, professional customer support agent.

You have access to these tools:
- search_knowledge_base: Search FAQs. Use this FIRST for every customer question.
- create_support_ticket: Create a ticket when KB has no answer.
- escalate_to_human: Use when customer is angry or asks for a human agent.

Rules:
1. Always search the knowledge base first
2. Give answers conversationally and warmly
3. If KB has no answer, create a support ticket
4. If customer is angry or wants human — escalate
5. Always respond in the customer's language
6. Mention ticket ID clearly when created"""


def _build_llm():
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=LLM_MODEL or "llama-3.3-70b-versatile",
            api_key=GROQ_API_KEY,
            temperature=0.2,
        )
    elif LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=LLM_MODEL or "gemini-1.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.2,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL or "gpt-4o",
            api_key=OPENAI_API_KEY,
            temperature=0.2,
        )


_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = _build_llm().bind_tools(TOOLS)
        logger.info(f"LLM ready — provider={LLM_PROVIDER} model={LLM_MODEL}")
    return _llm


def _to_lc_history(history: list) -> list:
    msgs = []
    for msg in history[-10:]:
        if msg["role"] == "human":
            msgs.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            msgs.append(AIMessage(content=msg["content"]))
    return msgs


def _run_tool(tool_name: str, tool_args: dict) -> str:
    tool: BaseTool = TOOLS_BY_NAME.get(tool_name)
    if not tool:
        return f"Tool {tool_name} not found."
    try:
        return tool.invoke(tool_args)
    except Exception as e:
        logger.error(f"Tool {tool_name} error: {e}", exc_info=True)
        return f"Tool execution completed with note: {str(e)[:100]}"


def run_agent(
    customer_id: str,
    user_message: str,
    channel: str = "chat",
    customer_email: Optional[str] = None,
    customer_name: Optional[str] = None,
) -> str:
    # Load memory
    mem = get_memory(customer_id)
    if customer_email and not mem.get("email"):
        update_memory(customer_id, {"email": customer_email})
    if customer_name and not mem.get("name"):
        update_memory(customer_id, {"name": customer_name})
    mem = get_memory(customer_id)
    history = get_conversation_history(customer_id)

    context = (
        f"[Customer ID: {customer_id} | "
        f"Name: {mem.get('name') or customer_name or 'Guest'} | "
        f"Channel: {channel}]\n\n"
    )

    # Build messages
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages += _to_lc_history(history)
    messages.append(HumanMessage(content=context + user_message))

    try:
        llm = get_llm()

        # First LLM call
        response = llm.invoke(messages)
        messages.append(response)

        # Execute tool calls if any (up to 5 rounds)
        for _ in range(5):
            if not response.tool_calls:
                break

            # Run all tool calls
            for tc in response.tool_calls:
                tool_result = _run_tool(tc["name"], tc["args"])
                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tc["id"],
                ))

            # Get next LLM response
            response = llm.invoke(messages)
            messages.append(response)

        final = response.content
        if not final or not final.strip():
            final = "I'm here to help! Could you please provide more details about your issue?"

    except Exception as e:
        logger.error(f"Agent error [{customer_id}]: {e}", exc_info=True)
        final = "I apologize for the trouble. Please try again in a moment, or type 'human agent' to speak with a person."

    # Save conversation
    append_conversation(customer_id, "human", user_message)
    append_conversation(customer_id, "assistant", final)

    # Sentiment tracking
    negative = ["angry", "frustrated", "terrible", "worst", "useless", "lawsuit", "ridiculous", "horrible"]
    if any(w in user_message.lower() for w in negative):
        update_memory(customer_id, {"sentiment": "negative"})

    return final
