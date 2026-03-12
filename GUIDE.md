# Aura Sales Bot

An AI sales agent that handles the full pipeline from first contact to booked meeting, with zero human involvement.

## What it does
A visitor opens the chat, talks to **Aura** (the AI consultant), shares their details, and gets followed up automatically — lead saved, booking link shared in chat.

## Stack
- **Language:** Python 3.11 + FastAPI
- **AI:** DeepSeek (`deepseek-chat`)
- **Hosting:** Render (auto-deploys from `github.com/FUMFGRP/SalesGPT`, branch `main`)
- **Email:** Resend from `info@aurasky.cloud`
- **Leads DB:** `leads.json` + Google Sheets (via Apps Script webhook)
- **Booking:** Cal.com API

## Endpoints
| Route | Purpose |
|---|---|
| `GET /` | Health check + config status |
| `GET /chat` | Web chat UI |
| `POST /chat` | Send a message (JSON: `message`, `session_id`) |
| `GET /leads` | View all captured leads |

## Environment variables required
```
DEEPSEEK_API_KEY
RESEND_API_KEY
RESEND_FROM_EMAIL=info@aurasky.cloud
GOOGLE_SHEET_WEBHOOK
CALCOM_API_KEY
RETELL_API_KEY
RETELL_AGENT_ID
RETELL_FROM_NUMBER
```

## How it works
1. Customer chats → Aura responds via DeepSeek
2. Bot extracts name, email, phone, interest from conversation
3. Lead saved to `leads.json` and synced to Google Sheets
4. When ready to book, Aura shares the Cal.com link (fetched dynamically at startup)

## Voice calls (Retell AI)
When a lead's phone number is captured for the first time, the bot auto-triggers an outbound AI call via Retell.
Webhook for call events: `POST /retell/webhook` — point this to your deployed URL in the Retell dashboard.
