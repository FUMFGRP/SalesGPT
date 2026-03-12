# Aura Sky Cloud Bot — Status Report for Joe

This is an AI sales bot that runs 24/7 and handles the full pipeline from first contact to booked meeting — no human involvement needed.

---

## Current Status Overview

| Piece | Status | Notes |
|---|---|---|
| AI chat bot | Live | Deployed on Render |
| Lead capture | Live | Saves name, email, phone, interest |
| Google Sheets sync | Live | Every new lead appears in the sheet automatically |
| Email (Resend) | Live | DNS verified — emails send from info@aurasky.cloud |
| Cal.com booking | Live | Booking link auto-fetched and shared in chat |
| Retell AI (voice calls) | Connected | Triggers outbound AI call when a phone number is captured |

**Live chat URL:** your Render service URL + `/chat`
**Leads sheet:** https://docs.google.com/spreadsheets/d/1Q7_EDZnGiUJzwpBPK8c1S3OdDefO-ywaXOG3o4woPUw

---

## APIs & What They Do

### 1. DeepSeek (AI Brain)
- **What:** Sends every customer message to DeepSeek and gets Aura's reply
- **Key:** `DEEPSEEK_API_KEY`
- **Cost:** Much cheaper than GPT-4 — roughly $0.001 per conversation
- **Get it:** platform.deepseek.com

### 2. Resend (Email)
- **What:** Sends transactional emails (confirmations, follow-ups) from info@aurasky.cloud
- **Key:** `RESEND_API_KEY`
- **Cost:** Free up to 3,000 emails/month
- **Status:** Waiting on DNS verification (see above)

### 3. Google Sheets (Lead Database)
- **What:** Every new lead is appended as a row — date, name, email, phone, interest, message count
- **How:** Google Apps Script webhook (no API key needed, just the webhook URL)
- **Cost:** Free

### 4. Render (Hosting)
- **What:** Runs the bot 24/7 on the internet
- **Cost:** Free tier (note: sleeps after 15 min of inactivity, first response can be slow — upgrade to $7/month to keep it always on)
- **Repo:** github.com/FUMFGRP/SalesGPT

### 5. Cal.com (Meeting Booking)
- **What:** The booking link shared in chat. The bot fetches the live link from Cal.com at startup so it's always current.
- **Key:** `CALCOM_API_KEY`
- **Cost:** Free

### 6. Retell AI (Outbound Voice Calls)
- **What:** When a lead shares their phone number in chat, the bot automatically triggers an outbound AI voice call via Retell. The Retell agent introduces itself and can guide the lead to book.
- **Keys needed:** `RETELL_API_KEY`, `RETELL_AGENT_ID`, `RETELL_FROM_NUMBER`
- **Webhook:** `POST /retell/webhook` — receives call status events (call started, ended, etc.)
- **Cost:** Pay-per-minute (check retellai.com for current rates)
- **Status:** Code integrated. Retell agent + phone number still need to be configured in the Retell dashboard.

---

## The Full Autopilot Flow

```
Customer visits chat
       |
Talks to Aura (DeepSeek)
       |
Shares name + email + phone
       |
Lead saved to Google Sheets
       |
Retell AI calls their number automatically
       |
AI voice agent continues the conversation
       |
Booking link shared → they book a slot
       |
Confirmation email sent via Resend (once DNS is verified)
       |
Done — zero human involvement
```

---

## Tech Stack

- **Language:** Python 3.11
- **Framework:** FastAPI
- **Dependencies:** `fastapi`, `uvicorn`, `requests`, `python-dotenv`
- **Hosting:** Render (auto-deploys from GitHub on every push)
- **Repo:** github.com/FUMFGRP/SalesGPT, branch `main`

---

## Services Pricing Summary

| Service | Monthly Cost |
|---|---|
| DeepSeek | ~$0.50–2 depending on volume |
| Resend | Free (up to 3,000 emails) |
| Google Sheets | Free |
| Render (always-on) | $7 (or free with cold starts) |
| Retell AI (calls) | Pay-per-minute (~$0.05–0.15/min) |
| Cal.com | Free |
| **Total** | **~$8–17/month** |
