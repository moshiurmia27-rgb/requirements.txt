
import os
import httpx
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
ADMIN_ID = os.getenv("ADMIN_ID")
SUPPORT = os.getenv("SUPPORT_USERNAME", "@MNSupport")
PAYMENT_INFO = os.getenv(
    "PAYMENT_INFO", "Contact admin for payment instructions."
)

orders = []
user_choices = {}

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def telegram(method, data):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{API}/{method}", json=data)
        return r.json()

async def send(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text}
    if keyboard:
        data["reply_markup"] = {"inline_keyboard": keyboard}
    await telegram("sendMessage", data)

def menu():
    return [
        [{"text": "🌍 Select Country", "callback_data": "country"}],
        [{"text": "📱 SMS Services", "callback_data": "services"}],
        [{"text": "🛒 New Order", "callback_data": "order"}],
        [{"text": "📦 My Orders", "callback_data": "myorders"}],
        [{"text": "💰 My Balance", "callback_data": "balance"}],
        [{"text": "💳 Payment Method", "callback_data": "payment"}],
        [{"text": "👤 Support", "callback_data": "support"}],
    ]

@app.get("/")
async def home():
    return {"status": "MN Number Bot is running"}

@app.post("/webhook")
async def webhook(request: Request):
    secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if not WEBHOOK_SECRET or secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403)

    data = await request.json()

    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        user_id = msg["from"]["id"]
        text = msg.get("text", "")

        if text == "/start":
            await send(
                chat_id,
                "🤖 Welcome to MN Number Bot!\n\n"
                "Select an option below to continue.",
                menu()
            )

        elif text == "/admin":
            if str(user_id) == ADMIN_ID:
                await send(chat_id, "👑 MN Admin Panel", [
                    [{"text": "📋 View Orders",
                      "callback_data": "admin_orders"}]
                ])
            else:
                await send(chat_id, "Access denied.")

    if "callback_query" in data:
        q = data["callback_query"]
        chat_id = q["message"]["chat"]["id"]
        user_id = q["from"]["id"]
        action = q["data"]

        await telegram("answerCallbackQuery", {
            "callback_query_id": q["id"]
        })

        if action == "home":
            await send(chat_id, "🏠 Main Menu", menu())

        elif action == "country":
            await send(chat_id, "🌍 Select your country:", [
                [{"text": "Bangladesh",
                  "callback_data": "country_Bangladesh"}],
                [{"text": "Other Countries",
                  "callback_data": "country_Other"}],
                [{"text": "⬅️ Back",
                  "callback_data": "home"}]
            ])

        elif action.startswith("country_"):
            country = action.replace("country_", "")
            user_choices[user_id] = {"country": country}
            await send(chat_id, f"Selected: {country}\n\n"
                "Choose a verification service:", [
                [{"text": "Own Website Verification",
                  "callback_data": "service_website"}],
                [{"text": "Own App Verification",
                  "callback_data": "service_app"}],
                [{"text": "⬅️ Back",
                  "callback_data": "country"}]
            ])

        elif action == "services":
            await send(chat_id, "📱 Available Services:\n\n"
                "• Own Website Verification\n"
                "• Own App Verification\n"
                "• Customer SMS Notifications",
                [[{"text": "🏠 Main Menu",
                   "callback_data": "home"}]])

        elif action.startswith("service_"):
            service = action.replace("service_", "")
            user_choices.setdefault(user_id, {})["service"] = service
            await send(chat_id,
                f"Selected service: {service}\n\n"
                "Submit a setup request?",
                [[{"text": "✅ Submit Request",
                   "callback_data": "submit_order"}],
                 [{"text": "⬅️ Back",
                   "callback_data": "services"}]])

        elif action == "order":
            await send(chat_id, "First select a country:", [
                [{"text": "🌍 Select Country",
                  "callback_data": "country"}]
            ])

        elif action == "submit_order":
            choice = user_choices.get(user_id, {})
            if not choice.get("country") or not choice.get("service"):
                await send(chat_id,
                    "Please select a country and service first.")
            else:
                order = {
                    "id": len(orders) + 1,
                    "user": user_id,
                    "country": choice["country"],
                    "service": choice["service"],
                    "status": "Pending"
                }
                orders.append(order)
                await send(chat_id,
                    f"✅ Request submitted!\n"
                    f"Order ID: #{order['id']}\n"
                    f"Status: Pending")
        
        elif action == "myorders":
            mine = [o for o in orders if o["user"] == user_id]
            if not mine:
                result = "You have no orders yet."
            else:
                result = "📦 Your Orders:\n\n"
                for o in mine:
                    result += (
                        f"Order #{o['id']}\n"
                        f"Country: {o['country']}\n"
                        f"Service: {o['service']}\n"
                        f"Status: {o['status']}\n\n"
                    )
            await send(chat_id, result)

        elif action == "balance":
            await send(chat_id, "💰 Your Balance: 0.00")

        elif action == "payment":
            await send(chat_id, "💳 Payment Method\n\n" + PAYMENT_INFO)

        elif action == "support":
            await send(chat_id, f"👤 Support: {SUPPORT}")

        elif action == "admin_orders":
            if str(user_id) != ADMIN_ID:
                await send(chat_id, "Access denied.")
            elif not orders:
                await send(chat_id, "No orders yet.")
            else:
                result = "👑 All Requests:\n\n"
                for o in orders[-20:]:
                    result += (
                        f"#{o['id']} | User: {o['user']}\n"
                        f"{o['country']} | {o['service']}\n"
                        f"Status: {o['status']}\n\n"
                    )
                await send(chat_id, result)

    return {"ok": True}
