#!/usr/bin/env python3
"""
Meta Messaging API Webhook Server (Instagram / Messenger)
Starter FastAPI app — handles verification, signature checking, and replies.
"""
import os
import json
import hmac
import hashlib
import requests
from datetime import datetime
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

app = FastAPI(title="Meta Messaging Webhook")

# ─── Config ──────────────────────────────────────────────────────────────────
VERIFY_TOKEN      = os.getenv("VERIFY_TOKEN",       "change_me_verify")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN",  "")
APP_SECRET        = os.getenv("APP_SECRET",         "")
WEBHOOK_PATH      = os.getenv("WEBHOOK_PATH",       "/webhook")

# ─── Helpers ─────────────────────────────────────────────────────────────────

def log_event(label: str, data: dict):
    ts = datetime.utcnow().isoformat()
    print(f"[{ts}] [{label}] {json.dumps(data, ensure_ascii=False, indent=2)}")

def send_message(recipient_id: str, text: str):
    if not PAGE_ACCESS_TOKEN:
        print("[WARN] PAGE_ACCESS_TOKEN not set, cannot reply.")
        return False
    url = "https://graph.facebook.com/v18.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message":   {"text": text},
        "messaging_type": "RESPONSE"
    }
    params = {"access_token": PAGE_ACCESS_TOKEN}
    try:
        r = requests.post(url, json=payload, params=params, timeout=15)
        r.raise_for_status()
        print(f"[INFO] Reply sent to {recipient_id}: {text[:60]}...")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")
        return False

# ─── Webhook GET (Meta verification) ───────────────────────────────────────────
@app.get(WEBHOOK_PATH, response_class=PlainTextResponse)
async def verify(
    hub_mode:          str = Query(..., alias="hub.mode"),
    hub_verify_token:  str = Query(..., alias="hub.verify_token"),
    hub_challenge:     str = Query(..., alias="hub.challenge"),
):
    if hub_mode != "subscribe":
        raise HTTPException(status_code=400, detail="Bad mode")
    if hub_verify_token != VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid verify token")
    print("[INFO] Webhook verified successfully.")
    return hub_challenge

# ─── Webhook POST (events) ─────────────────────────────────────────────────────
@app.post(WEBHOOK_PATH)
async def receive_event(request: Request):
    body = await request.body()
    body_text = body.decode("utf-8")

    # Optional HMAC signature check
    if APP_SECRET:
        sig_header = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            APP_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, sig_header):
            raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Bad JSON")

    log_event("WEBHOOK", data)

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            msg      = event.get("message", {})
            postback = event.get("postback", {})

            if msg and "text" in msg:
                text = msg["text"]
                print(f"[DM] From {sender_id}: {text}")
                # TODO: replace with your bot logic
                reply = f"Echo: {text}"
                send_message(sender_id, reply)

            elif postback:
                payload = postback.get("payload", "")
                print(f"[POSTBACK] From {sender_id}: payload={payload}")

    return JSONResponse(content={"status": "ok"})

# ─── Health check ────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "up", "time": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=port)
