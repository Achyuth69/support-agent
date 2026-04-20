"""
Core LangChain agent — Enterprise Customer Support Agent.
Supports: Groq, Gemini, OpenAI (set LLM_PROVIDER in .env)
"""
import logging
from typing import Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from config import LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, GROQ_API_KEY, GEMINI_API_KEY
from memory import get_memory, update_memory, append_conversation, get_conversation_history
from tools.search_kb import search_knowledge_base
from tools.create_ticket import create_support_ticket
from tools.escalate import escalate_to_human

logger = logging.getLogger(__name__)

TOOLS = [search_knowledge_base, create_support_ticket, escalate_to_human]

SYSTEM_PROMPT = (
    "You are a friendly and professional enterprise customer support agent. "
    "Help customers resolve their issues efficiently.\n\n"
    "TOOLS AVAILABLE:\n"
    "1. search_knowledge_base — search FAQs. Use this FIRST for every question.\n"
    "2. create_support_ticket — create a ticket when KB has no answer.\n"
    "3. escalate_to_human — escalate when customer is angry, asks for human, "
    "or issue is billing/legal/security.\n\n"
    "RULES:\n"
    "- Always search KB first before creating a ticket\n"
    "- If customer says they are angry, frustrated, or wants a human — escalate immediately\n"
    "- Respond in the same language the customer uses\n"
    "- Be warm, concise, and solution-focused\n"
    "- Always confirm ticket ID when a ticket is created"
)


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
            temperature=0.3,
        )
    elif LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=LLM_MODEL or "gemini-1.5-pro",
            google_api_key=GEMINI_API_KEY,
            temperature=0.3,
            convert_system_message_to_human=True,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL or "gpt-4o",
            api_key=OPENAI_API_KEY,
            temperature=0.3,
        )


def _build_agent():
    llm = _build_llm()
    logger.info(f"Building agent — provider: {LLM_PROVIDER}, model: {LLM_MODEL}")
    prompt = _build_prompt()
    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True,
        return_intermediate_steps=False,
    )


_agent_executor = None


def get_agent_executor() -> AgentExecutor:
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = _build_agent()
    return _agent_executor


def _to_lc_history(history: list) -> list:
    msgs = []
    for msg in history[-20:]:
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
    # Load memory
    mem = get_memory(customer_id)
    if customer_email and not mem.get("email"):
        update_memory(customer_id, {"email": customer_email})
    if customer_name and not mem.get("name"):
        update_memory(customer_id, {"name": customer_name})
    mem = get_memory(customer_id)

    history = get_conversation_history(customer_id)

    # Prepend context so agent knows who it's talking to
    context = (
        f"[Customer ID: {customer_id} | "
        f"Name: {mem.get('name') or customer_name or 'Unknown'} | "
        f"Channel: {channel} | "
        f"Sentiment: {mem.get('sentiment', 'neutral')}]\n"
    )
    enriched = context + user_message

    try:
        executor = get_agent_executor()
        result = executor.invoke({
            "input": enriched,
            "chat_history": _to_lc_history(history),
        })
        response = result.get("output", "I'm sorry, I couldn't process your request. Please try again.")
    except Exception as e:
        logger.error(f"Agent error for {customer_id}: {e}", exc_info=True)
        response = "I'm sorry, something went wrong on my end. Please try again or type 'human agent' to speak with a person."

    # Save to memory
    append_conversation(customer_id, "human", user_message)
    append_conversation(customer_id, "assistant", response)

    # Sentiment tracking
    negative = ["angry", "frustrated", "terrible", "worst", "useless", "lawsuit", "ridiculous", "horrible"]
    if any(w in user_message.lower() for w in negative):
        update_memory(customer_id, {"sentiment": "negative"})

    return response
