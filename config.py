import os
from dotenv import load_dotenv

load_dotenv()

# LLM Provider: "openai" | "groq" | "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Model names per provider
# Groq:   llama-3.3-70b-versatile | mixtral-8x7b-32768 | gemma2-9b-it
# Gemini: gemini-1.5-pro | gemini-1.5-flash | gemini-2.0-flash
# OpenAI: gpt-4o | gpt-4-turbo
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# Salesforce
SF_USERNAME = os.getenv("SF_USERNAME", "")
SF_PASSWORD = os.getenv("SF_PASSWORD", "")
SF_SECURITY_TOKEN = os.getenv("SF_SECURITY_TOKEN", "")
SF_DOMAIN = os.getenv("SF_DOMAIN", "login")

# Zendesk
ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN", "")
ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL", "")
ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN", "")

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# Email (SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

# SLA thresholds (in minutes)
SLA_RESPONSE_TIME = int(os.getenv("SLA_RESPONSE_TIME", "60"))   # 1 hour
SLA_RESOLUTION_TIME = int(os.getenv("SLA_RESOLUTION_TIME", "480"))  # 8 hours

# Supported languages
SUPPORTED_LANGUAGES = ["en", "hi", "ta", "te", "kn", "mr", "bn", "gu", "pa", "ml"]

# Human escalation webhook
ESCALATION_WEBHOOK_URL = os.getenv("ESCALATION_WEBHOOK_URL", "")

# Redis for memory (optional, falls back to in-memory)
REDIS_URL = os.getenv("REDIS_URL", "")
