"""
Enterprise Customer Support Agent — FastAPI server.
Handles chat, email webhook, and WhatsApp webhook endpoints.
"""
import logging
import traceback
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent import run_agent
from ticket import get_ticket, list_customer_tickets, check_sla_breach, get_open_tickets
from memory import get_memory, clear_memory
from integrations.whatsapp import parse_whatsapp_webhook, send_whatsapp, send_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise Customer Support Agent",
    description="AI-powered support agent with Salesforce, Zendesk, WhatsApp, and Email integrations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")


# ─── Models ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    customer_id: str
    message: str
    channel: str = "chat"
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None


class ChatResponse(BaseModel):
    customer_id: str
    response: str
    channel: str


class EmailWebhookPayload(BaseModel):
    from_email: str
    from_name: Optional[str] = None
    subject: str
    body: str
    customer_id: Optional[str] = None


# ─── Chat ─────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    logger.info(f"Chat from customer {req.customer_id} via {req.channel}")
    try:
        response = run_agent(
            customer_id=req.customer_id,
            user_message=req.message,
            channel=req.channel,
            customer_email=req.customer_email,
            customer_name=req.customer_name,
        )
    except Exception as e:
        logger.error(f"Chat error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    return ChatResponse(customer_id=req.customer_id, response=response, channel=req.channel)


# ─── WhatsApp Webhook ─────────────────────────────────────────────────────────

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    form_data = await request.form()
    payload = dict(form_data)
    parsed = parse_whatsapp_webhook(payload)
    customer_id = f"wa_{parsed['from'].replace('+', '')}"
    message = parsed["body"]
    if not message:
        return {"status": "ignored"}

    async def process_and_reply():
        response = run_agent(customer_id=customer_id, user_message=message, channel="whatsapp")
        send_whatsapp(parsed["from"], response)

    background_tasks.add_task(process_and_reply)
    return {"status": "processing"}


# ─── Email Webhook ────────────────────────────────────────────────────────────

@app.post("/webhook/email")
async def email_webhook(payload: EmailWebhookPayload, background_tasks: BackgroundTasks):
    customer_id = payload.customer_id or f"email_{payload.from_email.replace('@', '_').replace('.', '_')}"
    message = f"Subject: {payload.subject}\n\n{payload.body}"

    async def process_and_reply():
        response = run_agent(
            customer_id=customer_id,
            user_message=message,
            channel="email",
            customer_email=payload.from_email,
            customer_name=payload.from_name,
        )
        send_email(to_email=payload.from_email, subject=f"Re: {payload.subject}", body_text=response)

    background_tasks.add_task(process_and_reply)
    return {"status": "processing", "customer_id": customer_id}


# ─── Tickets ──────────────────────────────────────────────────────────────────

@app.get("/tickets/{ticket_id}")
def get_ticket_endpoint(ticket_id: str):
    t = get_ticket(ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {**t, "sla_status": check_sla_breach(ticket_id)}


@app.get("/customers/{customer_id}/tickets")
def customer_tickets(customer_id: str):
    return list_customer_tickets(customer_id)


@app.get("/tickets")
def all_open_tickets():
    return get_open_tickets()


# ─── Memory ───────────────────────────────────────────────────────────────────

@app.get("/customers/{customer_id}/memory")
def customer_memory(customer_id: str):
    return get_memory(customer_id)


@app.delete("/customers/{customer_id}/memory")
def reset_customer_memory(customer_id: str):
    clear_memory(customer_id)
    return {"status": "cleared", "customer_id": customer_id}


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "Enterprise Customer Support Agent"}


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
