"""
Per-customer context memory with optional Redis backend.
Falls back to in-memory dict if Redis is not configured.
"""
import json
import logging
from datetime import datetime
from typing import Optional
from config import REDIS_URL

logger = logging.getLogger(__name__)

# Try Redis, fall back to in-memory
_memory_store: dict = {}

try:
    if REDIS_URL:
        import redis
        _redis = redis.from_url(REDIS_URL, decode_responses=True)
        _USE_REDIS = True
    else:
        _redis = None
        _USE_REDIS = False
except Exception:
    _redis = None
    _USE_REDIS = False


def _key(customer_id: str) -> str:
    return f"csa:memory:{customer_id}"


def get_memory(customer_id: str) -> dict:
    """Retrieve full memory context for a customer."""
    if _USE_REDIS:
        try:
            raw = _redis.get(_key(customer_id))
            return json.loads(raw) if raw else _default_memory(customer_id)
        except Exception as e:
            logger.warning(f"Redis get failed, using in-memory: {e}")
    return _memory_store.get(customer_id, _default_memory(customer_id))


def update_memory(customer_id: str, updates: dict) -> dict:
    """Merge updates into customer memory and persist."""
    mem = get_memory(customer_id)
    mem.update(updates)
    mem["last_seen"] = datetime.utcnow().isoformat()
    _save_memory(customer_id, mem)
    return mem


def append_conversation(customer_id: str, role: str, content: str):
    """Append a message to the customer's conversation history."""
    mem = get_memory(customer_id)
    mem.setdefault("history", []).append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })
    # Keep last 50 messages to avoid bloat
    mem["history"] = mem["history"][-50:]
    _save_memory(customer_id, mem)


def get_conversation_history(customer_id: str) -> list:
    return get_memory(customer_id).get("history", [])


def clear_memory(customer_id: str):
    if _USE_REDIS:
        _redis.delete(_key(customer_id))
    else:
        _memory_store.pop(customer_id, None)


def _save_memory(customer_id: str, mem: dict):
    if _USE_REDIS:
        try:
            _redis.set(_key(customer_id), json.dumps(mem), ex=86400 * 30)
            return
        except Exception as e:
            logger.warning(f"Redis save failed, using in-memory: {e}")
    _memory_store[customer_id] = mem


def _default_memory(customer_id: str) -> dict:
    return {
        "customer_id": customer_id,
        "name": None,
        "email": None,
        "phone": None,
        "language": "en",
        "open_tickets": [],
        "history": [],
        "sentiment": "neutral",
        "last_seen": None,
        "crm_id": None,
        "zendesk_id": None,
    }
