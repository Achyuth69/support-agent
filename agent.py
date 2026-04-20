"""
Enterprise Customer Support Agent — Core Agent
Supports: Groq, Gemini, OpenAI
"""
import logging
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from config import LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, GROQ_API_KEY, GEMINI_API_KEY
from memory import get_memory, update_memory, append_conversation, get_conversation_history
from tools.search_kb import search_knowledge_base
from tools.create_ticket import create_support_ticket
from tools.escalate import escalate_to_human

logger = logging.getLogger(__name__)

TOOLS = [search_knowledge_base, create_support_ticket, escalate_to_human]

SYSTEM_PROMPT = """You are a warm, professional enterprise customer support agent for a company.

TOOLS:
- search_knowledge_base: Search FAQs. ALWAYS use this first for any customer question.
- create_support_ticket: Create a ticket when KB has no answer or issue needs tracking.
- escalate_to_human: Use when customer is angry, asks for human, or issue is billing/legal/security.

BEHAVIOR:
1. For EVERY customer question, search the knowledge base first
2. Give the answer from KB directly and naturally — don't just copy-paste, explain it conversationally
3. If KB has no answer, create a support ticket and give the ticket ID
4. If customer is angry or says "human agent" — escalate immediately
5. Always respond in the same language the customer writes in
6. Be warm, empathetic, and concise
7. When a ticket is created, always mention the ticket ID clearly

IMPORTANT: You must always use at least one tool per response. Never respond without searching the KB first."""


def _build_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])


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
            convert_system_message_to_human=True,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL or "gpt-4o",
            api_key=OPENAI_API_KEY,
            temperature=0.2,
        )


def _build_agent():
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    llm = _build_llm()
    logger.info(f"Agent ready — provider={LLM_PROVIDER} model={LLM_MODEL}")
    prompt = _build_prompt()
    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        max_iterations=6,
        handle_parsing_errors=True,
        return_intermediate_steps=False,
    )


_agent_executor = None


def get_agent_executor():
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = _build_agent()
    return _agent_executor


def _to_lc_history(history: list) -> list:
    msgs = []
    for msg in history[-16:]:
        if msg["role"] == "human":
            msgs.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            msgs.append(AIMessage(content=msg["content"]))
    return msgs


def run_agent(
    customer_id: str,
    user_message: str,
    channel: str = "chat",
    customer_email: Optional[str] = None,
    customer_name: Optional[str] = None,
) -> str:
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
        f"Channel: {channel} | "
        f"Sentiment: {mem.get('sentiment', 'neutral')}]\n\n"
    )

    try:
        executor = get_agent_executor()
        result = executor.invoke({
            "input": context + user_message,
            "chat_history": _to_lc_history(history),
        })
        response = result.get("output", "")
        if not response:
            response = "I'm here to help! Could you please describe your issue in more detail?"
    except Exception as e:
        logger.error(f"Agent error [{customer_id}]: {e}", exc_info=True)
        response = "I apologize for the inconvenience. Our team has been notified. Please try again or type 'human agent' to speak with a person directly."

    append_conversation(customer_id, "human", user_message)
    append_conversation(customer_id, "assistant", response)

    negative = ["angry", "frustrated", "terrible", "worst", "useless", "lawsuit", "ridiculous", "horrible", "pathetic"]
    if any(w in user_message.lower() for w in negative):
        update_memory(customer_id, {"sentiment": "negative"})

    return response
