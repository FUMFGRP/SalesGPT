"""
Aura Sky Cloud Bot - Pure HTTP version (No tiktoken, guaranteed to deploy)
Uses requests library only - no heavy dependencies
"""

import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
import requests

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Aura Sky Cloud Bot")

@app.on_event("startup")
def startup():
    global calcom_booking_url
    calcom_booking_url = fetch_calcom_booking_url()
    if calcom_booking_url:
        logger.info(f"Cal.com booking URL: {calcom_booking_url}")
    else:
        logger.warning("Cal.com booking URL not fetched — check CALCOM_API_KEY")

# Sessions
sessions: Dict[str, Any] = {}

# Leads file
LEADS_FILE = "leads.json"

def load_leads() -> list:
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "r") as f:
            return json.load(f)
    return []

def save_lead(session_id: str, session: dict):
    leads = load_leads()
    existing = next((l for l in leads if l["session_id"] == session_id), None)
    entry = {
        "session_id": session_id,
        "name": session.get("name"),
        "email": session.get("email"),
        "phone": session.get("phone"),
        "interest": session.get("interest"),
        "messages": len(session.get("history", [])),
        "last_seen": datetime.utcnow().isoformat(),
        "created_at": existing.get("created_at") if existing else datetime.utcnow().isoformat(),
    }
    if existing:
        leads[leads.index(existing)] = entry
    else:
        leads.append(entry)
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2)
    sync_to_sheets(entry, is_new=existing is None)

    # Trigger Retell call the first time a phone number is captured
    phone = session.get("phone")
    had_phone_before = existing and existing.get("phone")
    if phone and not had_phone_before:
        trigger_retell_call(phone, lead_name=session.get("name", ""))

    # Send booking link email the first time an email is captured
    email = session.get("email")
    had_email_before = existing and existing.get("email")
    if email and not had_email_before and calcom_booking_url:
        name = session.get("name") or "there"
        send_email(
            to=email,
            subject="Your booking link — Aura Sky Cloud",
            body=f"Hi {name},\n\nThanks for chatting with us! Here's your link to book a call with the Aura Sky Cloud team:\n\n{calcom_booking_url}\n\nLooking forward to speaking with you.\n\nAura\nAura Sky Cloud"
        )

def sync_to_sheets(lead: dict, is_new: bool = True):
    """Append new lead row to Google Sheet via Apps Script webhook."""
    webhook = os.getenv("GOOGLE_SHEET_WEBHOOK")
    if not webhook or not is_new:
        return
    try:
        requests.post(webhook, json={
            "date": lead.get("created_at", "")[:10],
            "name": lead.get("name") or "",
            "email": lead.get("email") or "",
            "phone": lead.get("phone") or "",
            "interest": lead.get("interest") or "",
            "messages": str(lead.get("messages", 0)),
        }, timeout=10)
    except Exception as e:
        logger.error(f"Sheets sync error: {e}")

def extract_lead_info(message: str, session: dict):
    """Extract name, email, phone from message and update session."""
    import re
    if re.search(r"[\w.+-]+@[\w-]+\.\w+", message):
        session["email"] = re.search(r"[\w.+-]+@[\w-]+\.\w+", message).group()
    if re.search(r"\+?[\d\s\-()]{7,15}", message):
        session["phone"] = re.search(r"\+?[\d\s\-()]{7,15}", message).group().strip()
    for service in ["coaching", "retainer", "project", "essential", "professional"]:
        if service in message.lower():
            session["interest"] = service
    name_match = re.search(r"(?:my name is|i am|i'm|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", message, re.IGNORECASE)
    if name_match and not session.get("name"):
        session["name"] = name_match.group(1)

# Config
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

RETELL_API_KEY = os.getenv("RETELL_API_KEY")
RETELL_AGENT_ID = os.getenv("RETELL_AGENT_ID")
RETELL_FROM_NUMBER = os.getenv("RETELL_FROM_NUMBER")  # e.g. +15551234567

CALCOM_API_KEY = os.getenv("CALCOM_API_KEY")
CALCOM_API_URL = "https://api.cal.com/v1"
calcom_booking_url: str = ""  # populated at startup

def fetch_calcom_booking_url() -> str:
    """Return booking URL. Uses CALCOM_BOOKING_URL env var directly if set, otherwise fetches via API."""
    # Direct override — most reliable
    direct = os.getenv("CALCOM_BOOKING_URL", "").strip()
    logger.info(f"Cal.com CALCOM_BOOKING_URL env value: '{direct}'")
    if direct:
        logger.info(f"Cal.com booking URL from env: {direct}")
        return direct

    if not CALCOM_API_KEY:
        return ""
    try:
        # Get profile (username)
        me = requests.get(f"{CALCOM_API_URL}/me?apiKey={CALCOM_API_KEY}", timeout=10)
        logger.info(f"Cal.com /me status={me.status_code} body={me.text[:300]}")
        if me.status_code != 200:
            return ""
        username = me.json().get("user", {}).get("username", "")

        # Get event types
        et = requests.get(f"{CALCOM_API_URL}/event-types?apiKey={CALCOM_API_KEY}", timeout=10)
        logger.info(f"Cal.com /event-types status={et.status_code} body={et.text[:300]}")
        if et.status_code != 200:
            return f"https://cal.com/{username}" if username else ""
        event_types = et.json().get("event_types", [])
        if not event_types:
            return f"https://cal.com/{username}" if username else ""
        slug = event_types[0].get("slug", "")
        return f"https://cal.com/{username}/{slug}"
    except Exception as e:
        logger.error(f"Cal.com fetch error: {e}")
        return ""

def build_system_prompt() -> str:
    booking_line = f"\nBOOKING: When the customer is ready to book, share this link: {calcom_booking_url}" if calcom_booking_url else ""
    return f"""You are Aura, an AI Solutions Consultant for Aura Sky Cloud.

CORE PROMISE: "If dealing with IT systems frustrates you, we bring clarity to that conversation."

SERVICES:
- Clarity Coaching: €100 (1 hour)
- Essential Retainer: €250/month
- Professional Retainer: €500/month
- Full Project: €5,000 (Discovery + Build)

What clients get: One AI-Team (Product Manager + Workflows + Specialists)
{booking_line}
Be warm, empathetic, and professional. When a customer seems ready to move forward or asks how to book, share the booking link."""

def get_ai_response(message: str, history: List[dict]) -> str:
    """Call DeepSeek API directly via HTTP"""
    if not DEEPSEEK_API_KEY:
        return "⚠️ Bot not configured. Add DEEPSEEK_API_KEY to environment variables."

    try:
        messages = [{"role": "system", "content": build_system_prompt()}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})

        response = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return f"Error: {response.status_code} - {response.text[:100]}"
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Sorry, error: {str(e)[:100]}"

def trigger_retell_call(to_number: str, lead_name: str = "") -> bool:
    """Initiate an outbound AI voice call via Retell when a phone number is captured."""
    if not RETELL_API_KEY or not RETELL_AGENT_ID or not RETELL_FROM_NUMBER:
        logger.warning("Retell not configured — skipping call (need RETELL_API_KEY, RETELL_AGENT_ID, RETELL_FROM_NUMBER)")
        return False
    try:
        payload = {
            "from_number": RETELL_FROM_NUMBER,
            "to_number": to_number,
            "agent_id": RETELL_AGENT_ID,
            "retell_llm_dynamic_variables": {
                "lead_name": lead_name or "there",
            },
        }
        res = requests.post(
            "https://api.retellai.com/v2/create-phone-call",
            headers={
                "Authorization": f"Bearer {RETELL_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        if res.status_code in (200, 201):
            call_id = res.json().get("call_id", "")
            logger.info(f"Retell call started: {call_id} → {to_number}")
            return True
        else:
            logger.error(f"Retell error: {res.status_code} {res.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"Retell call exception: {e}")
        return False

def send_email(to: str, subject: str, body: str) -> bool:
    """Send email via Resend HTTP API"""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        return False
    
    try:
        res = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": os.getenv("RESEND_FROM_EMAIL", "info@aurasky.cloud"),
                "to": to,
                "subject": subject,
                "text": body
            }
        )
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Email error: {e}")
        return False

# Simple web chat HTML
WEB_CHAT_HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aura Sky Cloud Bot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; height: 100vh; display: flex; flex-direction: column; }
        .header { background: #0A2540; color: white; padding: 1rem 1.5rem; }
        .header h1 { font-size: 1.25rem; }
        .header span { color: #7C9A6A; }
        .chat-container { flex: 1; max-width: 800px; width: 100%; margin: 0 auto; background: white; display: flex; flex-direction: column; }
        .messages { flex: 1; overflow-y: auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
        .message { max-width: 80%; padding: 1rem; border-radius: 12px; line-height: 1.5; white-space: pre-wrap; }
        .message.user { background: #0A2540; color: white; align-self: flex-end; }
        .message.bot { background: #F6F9FC; color: #1A1A2E; align-self: flex-start; border: 1px solid #E8EDF2; }
        .input-area { display: flex; padding: 1rem; border-top: 1px solid #E8EDF2; gap: 0.5rem; }
        .input-area input { flex: 1; padding: 0.75rem; border: 2px solid #E8EDF2; border-radius: 8px; font-size: 1rem; }
        .input-area input:focus { border-color: #7C9A6A; outline: none; }
        .input-area button { padding: 0.75rem 1.5rem; background: #C9A227; color: #0A2540; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
        .input-area button:hover { background: #E0BC4A; }
        .status { padding: 0.5rem 1rem; font-size: 0.75rem; color: #5A6578; background: #F6F9FC; border-top: 1px solid #E8EDF2; }
        .status.connected { color: #7C9A6A; }
        .status.error { color: #dc2626; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Aura <span>Sky Cloud</span> Bot</h1>
    </div>
    <div class="chat-container">
        <div class="messages" id="messages"></div>
        <div class="input-area">
            <input type="text" id="msg" placeholder="Type your message..." onkeypress="if(event.key==='Enter') send()">
            <button onclick="send()">Send</button>
        </div>
    </div>
    <div class="status" id="status">Loading...</div>
    <script>
        const sess = "web-" + Math.random().toString(36).substr(2, 9);
        
        async function check() {
            try {
                const r = await fetch("/");
                const d = await r.json();
                const statusEl = document.getElementById("status");
                if (d.configured) {
                    statusEl.textContent = "✅ Connected to DeepSeek";
                    statusEl.className = "status connected";
                    add("bot", "👋 Hello! I'm Aura from Aura Sky Cloud.\\n\\nIf dealing with IT systems frustrates you, I bring clarity to that conversation.\\n\\nWhat's your biggest tech headache right now?");
                } else {
                    statusEl.textContent = "❌ Not configured - Add DEEPSEEK_API_KEY";
                    statusEl.className = "status error";
                }
            } catch(e) {
                document.getElementById("status").textContent = "❌ Error: " + e.message;
                document.getElementById("status").className = "status error";
            }
        }
        
        function add(s, t) {
            const d = document.createElement("div");
            d.className = "message " + s;
            // Escape HTML then convert URLs to clickable links
            const escaped = t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
            const linked = escaped.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" style="color:inherit;text-decoration:underline;">$1</a>');
            d.innerHTML = linked.replace(/\n/g, "<br>");
            document.getElementById("messages").appendChild(d);
            document.getElementById("messages").scrollTop = 999999;
        }
        
        async function send() {
            const i = document.getElementById("msg");
            const t = i.value.trim();
            if (!t) return;
            add("user", t);
            i.value = "";
            try {
                const r = await fetch("/chat", {
                    method: "POST", 
                    headers: {"Content-Type": "application/json"}, 
                    body: JSON.stringify({message: t, session_id: sess})
                });
                const d = await r.json();
                add("bot", d.response);
            } catch(e) {
                add("bot", "❌ Error: " + e.message);
            }
        }
        
        check();
        document.getElementById("msg").focus();
    </script>
</body>
</html>'''

@app.get("/")
def root():
    return {
        "status": "online",
        "configured": bool(DEEPSEEK_API_KEY),
        "service": "Aura Sky Cloud Bot",
        "version": "HTTP Edition",
        "calcom": calcom_booking_url or "not configured"
    }

@app.get("/chat", response_class=HTMLResponse)
def chat():
    return WEB_CHAT_HTML

@app.post("/chat")
async def chat_msg(request: Request):
    data = await request.json()
    msg = data.get("message", "")
    sid = data.get("session_id", "web")
    
    if sid not in sessions:
        sessions[sid] = {"history": []}

    sessions[sid]["history"].append({"role": "user", "content": msg})
    extract_lead_info(msg, sessions[sid])
    reply = get_ai_response(msg, sessions[sid]["history"])
    sessions[sid]["history"].append({"role": "assistant", "content": reply})
    save_lead(sid, sessions[sid])

    return {"response": reply}

@app.get("/leads")
def get_leads():
    return {"leads": load_leads(), "total": len(load_leads())}

@app.post("/email")
async def send_email_endpoint(request: Request):
    data = await request.json()
    success = send_email(
        data.get("to"), 
        data.get("subject", "Test"), 
        data.get("body", "Test email")
    )
    return {"success": success}

@app.post("/inbound-email")
async def inbound_email(request: Request):
    """Receive inbound emails from Resend, process through Aura, reply to sender."""
    import re
    data = await request.json()

    raw_from = data.get("from", "")
    # Parse "Name <email>" or plain "email"
    match = re.search(r"[\w.+-]+@[\w-]+\.\w+", raw_from)
    sender_email = match.group() if match else ""
    if not sender_email:
        logger.warning(f"Inbound email: could not parse sender from '{raw_from}'")
        return {"ok": False, "reason": "no sender email"}

    subject = data.get("subject", "")
    body = (data.get("text") or data.get("html") or "").strip()
    if not body:
        return {"ok": False, "reason": "empty body"}

    logger.info(f"Inbound email from {sender_email}: {subject[:60]}")

    # Use email address as session ID so history persists across replies
    sid = f"email-{sender_email}"
    if sid not in sessions:
        sessions[sid] = {"history": [], "email": sender_email}

    sessions[sid]["history"].append({"role": "user", "content": body})
    extract_lead_info(body, sessions[sid])
    # Ensure email is always set from the sender address
    sessions[sid]["email"] = sender_email

    reply = get_ai_response(body, sessions[sid]["history"])
    sessions[sid]["history"].append({"role": "assistant", "content": reply})
    save_lead(sid, sessions[sid])

    # Reply to sender
    reply_subject = f"Re: {subject}" if subject and not subject.lower().startswith("re:") else subject or "Aura Sky Cloud"
    send_email(to=sender_email, subject=reply_subject, body=reply)

    return {"ok": True}

@app.post("/retell/webhook")
async def retell_webhook(request: Request):
    """Receive call event updates from Retell (call_started, call_ended, etc.)."""
    data = await request.json()
    event = data.get("event")
    call_id = data.get("data", {}).get("call_id", "")
    logger.info(f"Retell webhook: event={event} call_id={call_id}")
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 Aura Sky Cloud Bot - HTTP Edition")
    print("=" * 50)
    print(f"DeepSeek: {'✅' if DEEPSEEK_API_KEY else '❌'} (model: {DEEPSEEK_MODEL})")
    print(f"Resend: {'✅' if os.getenv('RESEND_API_KEY') else '❌'}")
    print(f"Cal.com: {'✅ ' + calcom_booking_url if calcom_booking_url else '❌ booking URL not set'}")
    print(f"Retell: {'✅' if RETELL_API_KEY and RETELL_AGENT_ID else '❌ (need RETELL_API_KEY + RETELL_AGENT_ID + RETELL_FROM_NUMBER)'}")
    print("=" * 50)
    print("🌐 Web Chat: http://localhost:8000/chat")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
