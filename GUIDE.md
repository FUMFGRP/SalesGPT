# Aura Sales Bot

An AI sales agent that handles the full pipeline from first contact to booked meeting, with zero human involvement.

## What it does
A visitor opens the chat, talks to **Aura** (the AI consultant), shares their details, and gets followed up automatically — lead saved, booking link shared in chat.

## Stack
- **Language:** Python 3.11 + FastAPI
- **AI:** OpenRouter → GPT-4 (`openai/gpt-4`)
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
OPENROUTER_API_KEY
RESEND_API_KEY
RESEND_FROM_EMAIL=info@aurasky.cloud
GOOGLE_SHEET_WEBHOOK
CALCOM_API_KEY
```

## How it works
1. Customer chats → Aura responds via GPT-4
2. Bot extracts name, email, phone, interest from conversation
3. Lead saved to `leads.json` and synced to Google Sheets
4. When ready to book, Aura shares the Cal.com link (fetched dynamically at startup)

## Still to connect
- **Twilio** — auto call/SMS when phone number is captured (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`)
