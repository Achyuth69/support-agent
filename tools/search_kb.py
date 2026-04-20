"""
Knowledge Base search tool — compatible with LangChain 0.2+ tool calling.
"""
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

KNOWLEDGE_BASE = [
    {"id": "kb001", "title": "How to reset your password",
     "content": "To reset your password: 1. Go to the login page and click 'Forgot Password'. 2. Enter your registered email. 3. Check your inbox for a reset link (check spam too). 4. Click the link and set a new password. The link expires in 30 minutes.",
     "tags": ["password", "reset", "login", "forgot", "account"]},
    {"id": "kb002", "title": "Account verification / email not received",
     "content": "If you haven't received your verification email: 1. Check your spam or junk folder. 2. Make sure you entered the correct email at signup. 3. Click 'Resend Verification Email' on the login page. If still not received after 10 minutes, contact support.",
     "tags": ["verification", "email", "confirm", "activate", "account"]},
    {"id": "kb003", "title": "How to update account details",
     "content": "To update your account: 1. Log in. 2. Click your profile icon (top right) → Account Settings. 3. Edit your name, phone, or email. 4. Click Save Changes. Email changes require re-verification.",
     "tags": ["update", "account", "name", "email", "phone", "profile", "change"]},
    {"id": "kb004", "title": "How to delete your account",
     "content": "To delete your account: 1. Log in → Account Settings → scroll to bottom. 2. Click 'Delete Account'. 3. Confirm by typing your email. All data deleted within 30 days. This cannot be undone.",
     "tags": ["delete", "account", "close", "remove", "deactivate"]},
    {"id": "kb005", "title": "Account locked or suspended",
     "content": "Account may be locked due to: too many failed login attempts (auto-unlocks after 30 min), suspicious activity, or ToS violation. To unlock: wait 30 min, use Forgot Password, or contact support with ID proof.",
     "tags": ["locked", "suspended", "blocked", "account", "login", "banned"]},
    {"id": "kb006", "title": "Refund policy and how to request a refund",
     "content": "Refund policy: Digital products refundable within 7 days if unused. Physical products within 30 days in original condition. Subscriptions: prorated refund if cancelled within 14 days. To request: Log in → Orders → find order → click 'Request Refund'. Processed in 5-7 business days.",
     "tags": ["refund", "money back", "return", "billing", "payment", "charge"]},
    {"id": "kb007", "title": "How to update payment method",
     "content": "To update payment: 1. Log in → Account Settings → Billing. 2. Click 'Payment Methods'. 3. Add new card or update existing. 4. Set as default. We accept Visa, Mastercard, Rupay, UPI, Net Banking.",
     "tags": ["payment", "card", "billing", "update", "credit card", "debit card", "UPI"]},
    {"id": "kb008", "title": "Incorrect or double charge",
     "content": "If charged incorrectly: 1. Check billing history in Account Settings → Billing. 2. Banks sometimes show pending authorizations that auto-reverse in 3-5 days. 3. If confirmed incorrect, contact support with order ID and screenshot. We investigate within 48 hours.",
     "tags": ["wrong charge", "double charge", "overcharged", "billing error", "duplicate", "dispute"]},
    {"id": "kb009", "title": "How to get an invoice or receipt",
     "content": "To download invoice: Log in → Account Settings → Billing History → find transaction → click 'Download Invoice'. PDF format with GST details. Also emailed after every payment.",
     "tags": ["invoice", "receipt", "billing", "GST", "tax", "download"]},
    {"id": "kb010", "title": "How to upgrade or downgrade plan",
     "content": "To change plan: Log in → Account Settings → Subscription → click 'Change Plan' → select new plan → Confirm. Upgrading takes effect immediately (prorated charge). Downgrading takes effect at end of billing cycle.",
     "tags": ["upgrade", "downgrade", "plan", "subscription", "change plan", "pricing"]},
    {"id": "kb011", "title": "How to cancel subscription",
     "content": "To cancel: Log in → Account Settings → Subscription → click 'Cancel Plan' → select reason → Confirm. Access continues until end of billing period. No further charges. Data kept 90 days. Can reactivate anytime.",
     "tags": ["cancel", "subscription", "stop", "end plan", "unsubscribe", "billing"]},
    {"id": "kb012", "title": "Free trial information",
     "content": "Free trial: 14 days, full access, no credit card required. Reminder email 3 days before expiry. After trial: if payment method added, moves to paid plan automatically. If not, account paused (data kept 30 days).",
     "tags": ["free trial", "trial", "demo", "expire", "subscription", "free"]},
    {"id": "kb013", "title": "How to track your order",
     "content": "To track order: Log in → My Orders → click order → see status and tracking number → click tracking number for courier website. Also get updates via email and SMS. Standard delivery: 3-5 business days. Express: 1-2 days.",
     "tags": ["track", "order", "shipping", "delivery", "courier", "status", "where is my order"]},
    {"id": "kb014", "title": "How to return a product",
     "content": "To return: Log in → My Orders → select order → click 'Return Item' → select item and reason → choose pickup or drop-off → print return label. Return window: 30 days from delivery. Refund in 5-7 days after receipt. Items must be unused in original packaging.",
     "tags": ["return", "product", "send back", "exchange", "refund", "order", "damaged"]},
    {"id": "kb015", "title": "Order not delivered / missing package",
     "content": "If order not arrived: 1. Check tracking in My Orders. 2. Check if delivery was attempted. 3. Wait 1 extra business day. If still missing after expected date, contact support with order ID. We investigate with courier (2-3 days) and reship or refund if confirmed lost.",
     "tags": ["not delivered", "missing", "lost", "package", "order", "shipping"]},
    {"id": "kb016", "title": "App or website not loading",
     "content": "If not loading: 1. Refresh page (Ctrl+R). 2. Clear browser cache and cookies. 3. Try different browser. 4. Disable browser extensions. 5. Check internet connection. 6. Try different device. Check status.ourcompany.com for outages.",
     "tags": ["not loading", "error", "crash", "broken", "website", "app", "technical", "bug", "slow"]},
    {"id": "kb017", "title": "Mobile app issues",
     "content": "If mobile app crashing: 1. Force close and reopen. 2. Check for updates in App Store/Play Store. 3. Restart phone. 4. Uninstall and reinstall (data saved in cloud). 5. Ensure iOS 14+ or Android 9+. 6. Need 200MB free storage.",
     "tags": ["mobile", "app", "crash", "android", "ios", "not working", "phone"]},
    {"id": "kb018", "title": "Account hacked or compromised",
     "content": "If account hacked: 1. Immediately change password via Forgot Password. 2. Log in → Account Settings → Security → 'Log out all devices'. 3. Enable 2FA. 4. Contact support immediately. We respond to compromise reports within 1 hour. We never ask for your password.",
     "tags": ["hacked", "security", "unauthorized", "breach", "compromised", "stolen"]},
    {"id": "kb019", "title": "How to enable Two-Factor Authentication (2FA)",
     "content": "To enable 2FA: Log in → Account Settings → Security → Two-Factor Authentication → Enable 2FA → choose Authenticator App or SMS → scan QR code with Google Authenticator or Authy → enter 6-digit code → Enable. Save backup codes safely.",
     "tags": ["2FA", "two factor", "authentication", "security", "OTP", "protect"]},
    {"id": "kb020", "title": "How to use promo codes",
     "content": "To apply promo code: Add items to cart → checkout → enter code in 'Promo Code' field → click Apply. Common issues: code expired, minimum order not met, one-time use per account, category-specific restrictions.",
     "tags": ["promo", "coupon", "discount", "code", "offer", "voucher", "deal"]},
    {"id": "kb021", "title": "How to contact support",
     "content": "Contact support: Live Chat (24/7 on website/app), Email: support@ourcompany.com (response within 4 hours), WhatsApp: +91-XXXXXXXXXX (9AM-9PM IST), Phone: 1800-XXX-XXXX (toll-free, 9AM-6PM Mon-Sat). For urgent issues use Live Chat.",
     "tags": ["contact", "support", "help", "complaint", "reach", "phone", "email", "chat"]},
]


class KBInput(BaseModel):
    query: str = Field(description="The customer's question or issue in natural language")


def _search_kb(query: str) -> str:
    query_lower = query.lower()
    results = []
    for article in KNOWLEDGE_BASE:
        score = 0
        for word in query_lower.split():
            if len(word) < 3:
                continue
            if word in article["title"].lower() or word in article["content"].lower():
                score += 1
            if any(word in tag for tag in article["tags"]):
                score += 2
        if score > 0:
            results.append((score, article))
    if not results:
        return "No relevant knowledge base articles found for this query."
    results.sort(key=lambda x: x[0], reverse=True)
    output = []
    for _, article in results[:2]:
        output.append(f"**{article['title']}**\n{article['content']}")
    return "\n\n---\n\n".join(output)


search_knowledge_base = StructuredTool.from_function(
    func=_search_kb,
    name="search_knowledge_base",
    description="Search the internal knowledge base for answers to customer questions. Use this FIRST before creating tickets.",
    args_schema=KBInput,
)
