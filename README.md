# Enterprise Customer Support Agent

An advanced AI-powered customer support agent with full enterprise integrations.

## Features

| Feature | Details |
|---|---|
| Multi-channel | Chat API, WhatsApp (Twilio), Email (SMTP/webhook) |
| CRM | Salesforce — contact lookup, case creation |
| Ticketing | Zendesk — ticket create/update/search |
| Memory | Per-customer context (Redis or in-memory) |
| SLA Tracking | Response & resolution SLA with breach detection |
| Escalation | Webhook + email notification to human agents |
| Multi-language | 10 Indian + global languages via GPT-4o |
| Knowledge Base | Searchable KB (swap with vector DB for production) |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run the server
python main.py
```

Server starts at `http://localhost:8000`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat` | Send a chat message |
| POST | `/webhook/whatsapp` | Twilio WhatsApp webhook |
| POST | `/webhook/email` | Incoming email webhook |
| GET | `/tickets/{id}` | Get ticket + SLA status |
| GET | `/customers/{id}/tickets` | List customer tickets |
| GET | `/tickets` | All open tickets |
| GET | `/customers/{id}/memory` | Customer context |
| DELETE | `/customers/{id}/memory` | Reset customer memory |
| GET | `/health` | Health check |

## Example Chat Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_001",
    "message": "I want a refund for my order",
    "channel": "chat",
    "customer_email": "customer@example.com",
    "customer_name": "Rahul Sharma"
  }'
```

## Architecture

```
main.py (FastAPI)
  └── agent.py (LangChain Agent + GPT-4o)
        ├── tools/search_kb.py       → Knowledge base search
        ├── tools/create_ticket.py   → Ticket creation
        └── tools/escalate.py        → Human escalation
              ├── integrations/salesforce.py
              ├── integrations/zendesk.py
              └── integrations/whatsapp.py
        └── memory.py                → Per-customer context
        └── ticket.py                → SLA tracking
        └── escalation.py            → Escalation logic
```

## Production Recommendations

- Replace in-memory KB with **Pinecone / Weaviate** for semantic search
- Use **PostgreSQL** for ticket persistence instead of in-memory dict
- Enable **Redis** for distributed customer memory
- Add **authentication** (API keys / OAuth) to all endpoints
- Deploy behind **nginx** with SSL
- Set up **Celery** for async background tasks
