# Aura Sky Cloud Bot — Overview for Joe

This is an AI sales bot that runs 24/7 and handles the full pipeline from first contact to booked meeting — no human involvement needed.

---

## What It Does

A person visits the chat link, talks to **Aura** (the AI consultant), shares their contact details and interest, and gets followed up automatically — phone call, SMS with booking link, confirmation email.

---

## Live Right Now

| Piece | Status | Details |
|---|---|---|
| AI chat bot | Live | Deployed on Render |
| Lead capture | Live | Saves name, email, phone, interest |
| Google Sheets sync | Live | Every new lead appears in the sheet automatically |
| Email | Live | Sends via Resend from info@aurasky.cloud |

**Live chat URL:** your Render service URL + `/chat`
**Leads sheet:** https://docs.google.com/spreadsheets/d/1Q7_EDZnGiUJzwpBPK8c1S3OdDefO-ywaXOG3o4woPUw

---

## APIs & What They Do

### 1. OpenRouter (AI Brain)
- **What:** Sends every customer message to GPT-4 and gets Aura's reply
- **Key:** `OPENROUTER_API_KEY`
- **Cost:** ~$0.01 per conversation
- **Get it:** openrouter.ai

### 2. Resend (Email)
- **What:** Sends transactional emails (confirmations, follow-ups) from info@aurasky.cloud
- **Key:** `RESEND_API_KEY`
- **Cost:** Free up to 3,000 emails/month
- **Get it:** resend.com

### 3. Google Sheets (Lead Database)
- **What:** Every new lead is appended as a row — date, name, email, phone, interest, message count
- **How:** Google Apps Script webhook (no API key needed, just the webhook URL)
- **Key:** `GOOGLE_SHEET_WEBHOOK`
- **Cost:** Free

### 4. Render (Hosting)
- **What:** Runs the bot 24/7 on the internet
- **Cost:** Free tier (note: sleeps after 15 min of inactivity, first response can be slow — upgrade to $7/month to keep it always on)
- **Repo:** github.com/FUMFGRP/SalesGPT

---

## Still To Connect

### 5. Twilio (Calls & SMS)
- **What:** When a lead shares their phone number, the bot automatically calls them. They can press a key to get an SMS with the booking link.
- **Keys needed:** `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- **Cost:** ~$1/month for the number + $0.01/minute for calls + $0.0075/SMS
- **Get it:** twilio.com

### 6. Cal.com (Meeting Booking)
- **What:** The booking link sent via SMS and shared in chat. Full API integration lets the bot check availability and book directly in the conversation.
- **Keys needed:** `CALCOM_API_KEY`, booking URL
- **Cost:** Free
- **Get it:** cal.com

---

## The Full Autopilot Flow (once Twilio + Cal.com are connected)

```
Customer visits chat
       |
Talks to Aura (GPT-4)
       |
Shares name + email + phone
       |
Lead saved to Google Sheets
       |
Twilio calls their number automatically
       |
They press 1 (talk) or 2 (book online)
       |
SMS sent with cal.com booking link
       |
They book a slot
       |
Confirmation email sent via Resend
       |
Done — zero human involvement
```

---

## Tech Stack

- **Language:** Python 3.11
- **Framework:** FastAPI
- **Dependencies:** `fastapi`, `uvicorn`, `requests`, `python-dotenv` (4 packages, no heavy ML libraries)
- **Hosting:** Render (auto-deploys from GitHub on every push)
- **Repo:** github.com/FUMFGRP/SalesGPT, branch `main`

---

## Services Pricing Summary

| Service | Monthly Cost |
|---|---|
| OpenRouter (GPT-4) | ~$5–20 depending on volume |
| Resend | Free |
| Google Sheets | Free |
| Render (always-on) | $7 (or free with cold starts) |
| Twilio | ~$2–10 depending on call volume |
| Cal.com | Free |
| **Total** | **~$10–40/month** |
