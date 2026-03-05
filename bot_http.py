"""
Aura Sky Cloud Bot - Pure HTTP version (No tiktoken, guaranteed to deploy)
Uses requests library only - no heavy dependencies
"""

import os
import json
import logging
from typing import Dict, Any, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
import requests

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Aura Sky Cloud Bot")

# Sessions
sessions: Dict[str, Any] = {}

# Config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are Aura, an AI Solutions Consultant for Aura Sky Cloud.

CORE PROMISE: "If dealing with IT systems frustrates you, we bring clarity to that conversation."

SERVICES:
- Clarity Coaching: €100 (1 hour)
- Essential Retainer: €250/month
- Professional Retainer: €500/month
- Full Project: €5,000 (Discovery + Build)

What clients get: One AI-Team (Product Manager + Workflows + Specialists)

Be warm, empathetic, and professional."""

def get_ai_response(message: str, history: List[dict]) -> str:
    """Call OpenRouter API directly via HTTP"""
    if not OPENROUTER_API_KEY:
        return "⚠️ Bot not configured. Add OPENROUTER_API_KEY to environment variables."
    
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})
        
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://aurasky.cloud",
                "X-Title": "Aura Sky Cloud Bot"
            },
            json={
                "model": "openai/gpt-4",
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
                    statusEl.textContent = "✅ Connected to OpenRouter";
                    statusEl.className = "status connected";
                    add("bot", "👋 Hello! I'm Aura from Aura Sky Cloud.\\n\\nIf dealing with IT systems frustrates you, I bring clarity to that conversation.\\n\\nWhat's your biggest tech headache right now?");
                } else {
                    statusEl.textContent = "❌ Not configured - Add OPENROUTER_API_KEY";
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
            d.textContent = t;
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
        "configured": bool(OPENROUTER_API_KEY),
        "service": "Aura Sky Cloud Bot",
        "version": "HTTP Edition"
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
    reply = get_ai_response(msg, sessions[sid]["history"])
    sessions[sid]["history"].append({"role": "assistant", "content": reply})
    
    return {"response": reply}

@app.post("/email")
async def send_email_endpoint(request: Request):
    data = await request.json()
    success = send_email(
        data.get("to"), 
        data.get("subject", "Test"), 
        data.get("body", "Test email")
    )
    return {"success": success}

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 Aura Sky Cloud Bot - HTTP Edition")
    print("=" * 50)
    print(f"OpenRouter: {'✅' if OPENROUTER_API_KEY else '❌'}")
    print(f"Resend: {'✅' if os.getenv('RESEND_API_KEY') else '❌'}")
    print("=" * 50)
    print("🌐 Web Chat: http://localhost:8000/chat")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
