
import os
import httpx
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.get("/")
async def home():
    return {"status": "Bot is running"}

@app.post("/webhook")
async def webhook(request: Request):
    secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if not WEBHOOK_SECRET or secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403)

    data = await request.json()
    message = data.get("message", {})

    chat = message.get("chat", {})
    text = message.get("text", "")
    chat_id = chat.get("id")

    if chat_id and BOT_TOKEN:
        if text == "/start":
            reply = "Welcome! Bot is working."
        elif text == "/help":
            reply = "How can I help you?"
        else:
            reply = "Your message: " + text

        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": reply
                }
            )

    return {"ok": True}
