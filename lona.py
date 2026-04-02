import tkinter as tk
from tkinter import scrolledtext
from telethon import TelegramClient, events
import threading
import requests
import asyncio
import random
from datetime import datetime
from collections import deque

# ====================== CONFIG ======================
api_id = 32875170
api_hash = "4e63309a51eaa1c7d3015fda5db51a9a"
groq_api_key = "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"
phone_number = "+962795637371"
GIPHY_API_KEY = "lvNnJcWgoXM08f2uRFOvNQwHCKrbnK3U"

# ====================== تذكيرات ======================
reminders = [
    "يا قلبي، كيفك اليوم؟", "فكرت فيك، شو أخبارك؟", "هههه والله تذكرتك، كيف الأحوال؟",
    "شو عامل يا حلو؟", "الدنيا حلوة وانت فيها 🌸", "بتفتقدك شوي، حكيني عن يومك",
    "كيفك يا روحي؟", "الله يسعدك، شو في جديد؟"
]

# ====================== متغيرات ======================
auto_reply_enabled = {}        # chat_id: True/False
conversation_history = {}      # user_id: deque
MAX_HISTORY = 10
MY_USER_ID = None

def add_to_history(user_id, role, content):
    if user_id not in conversation_history:
        conversation_history[user_id] = deque(maxlen=MAX_HISTORY)
    conversation_history[user_id].append({"role": role, "content": content})

def get_history(user_id):
    return list(conversation_history.get(user_id, []))

# ====================== جلب GIF ======================
def get_gif_url(keyword="cute"):
    try:
        url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={keyword}&limit=1&rating=g"
        r = requests.get(url, timeout=6)
        data = r.json()
        if data.get('data'):
            return data['data'][0]['images']['original']['url']
    except:
        pass
    return None

# ====================== AI ======================
def ask_ai(text, history):
    system_prompt = """أنت لين، بنت أردنية لطيفة 23 سنة. تتكلمي لهجة أردنية حلوة وطبيعية.
استخدمي: يا قلبي، هههه، والله، يا حلو، يا روحي... الردود قصيرة وودية ومتناسقة."""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": text})

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "temperature": 0.78,
            "max_tokens": 90
        }
        r = requests.post(url, headers=headers, json=data, timeout=8)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return "هههه تمام يا قلبي، شو في؟"

# ====================== GUI ======================
root = tk.Tk()
root.title("لين 💕 - Auto Reply أردنية")
root.geometry("1280x900")
root.configure(bg="#0a0a0a")

title = tk.Label(root, text="لين 💕 - Auto Reply أردنية", font=("Consolas", 18, "bold"), fg="#ff69b4", bg="#0a0a0a")
title.pack(pady=10)

is_global_on = tk.BooleanVar(value=True)

def toggle_global():
    if is_global_on.get():
        status_label.config(text="● شغالة (عام)", fg="#00ff00")
        toggle_btn.config(text="⛔ إيقاف الكل", bg="#ff4444")
    else:
        status_label.config(text="● متوقفة (عام)", fg="#ff4444")
        toggle_btn.config(text="▶ تشغيل الكل", bg="#00cc00")

toggle_btn = tk.Button(root, text="⛔ إيقاف الكل", font=("Consolas", 12, "bold"),
                       bg="#ff4444", fg="white", width=22, height=2,
                       command=lambda: (is_global_on.set(not is_global_on.get()), toggle_global()))
toggle_btn.pack(pady=8)

status_label = tk.Label(root, text="● شغالة (عام)", font=("Consolas", 14, "bold"), fg="#00ff00", bg="#0a0a0a")
status_label.pack(pady=5)

log_box = scrolledtext.ScrolledText(root, bg="#0a0a0a", fg="#ff69b4", font=("Consolas", 10))
log_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_box.insert(tk.END, f"[{ts}] {msg}\n")
    log_box.see(tk.END)

# ====================== TELEGRAM ======================
client = None

async def run_bot():
    global client, MY_USER_ID
    client = TelegramClient("auto_reply_session", api_id, api_hash, sequential_updates=True)

    try:
        await client.connect()
        log("[SYSTEM] جاري الاتصال بتليجرام...")

        if not await client.is_user_authorized():
            log(f"[LOGIN] إرسال كود إلى {phone_number}")
            await client.send_code_request(phone_number)
            code = input("\n>>> أدخل كود التحقق: ").strip()
            if code:
                await client.sign_in(phone_number, code)
                log("[LOGIN] ✅ تم الدخول بنجاح!")

        # جلب معرفك تلقائياً
        me = await client.get_me()
        MY_USER_ID = me.id
        log(f"[INFO] حسابك: {me.first_name} | User ID: {MY_USER_ID}")
        log("[SYSTEM] لين جاهزة - التحكم بـ on/off فقط منك أنت")

        @client.on(events.NewMessage(incoming=True))
        async def handler(event):
            if not event.is_private:
                return

            sender = await event.get_sender()
            name = sender.first_name or "Unknown"
            user_id = sender.id
            chat_id = event.chat_id
            text = event.message.text.strip() if event.message.text else ""

            log(f"[IN] من {name} (ID: {user_id})")

            # ==================== التحكم فقط منك أنت ====================
            if user_id == MY_USER_ID and text:
                lower = text.lower().strip()

                # أوامر الإيقاف
                if lower in ["off", "أوف", "ايقاف", "ايقاف الرد"]:
                    auto_reply_enabled[chat_id] = False
                    await event.reply("✅ تم إيقاف الرد التلقائي في هذا الشات.\nاكتب 'on' أو 'أون' عشان أرجع أرد.")
                    log(f"[CONTROL] إيقاف الرد في شات: {name}")
                    return

                # أوامر التشغيل
                elif lower in ["on", "أون", "تشغيل", "رجع"]:
                    auto_reply_enabled[chat_id] = True
                    await event.reply("✅ تم تشغيل الرد التلقائي في هذا الشات 💕\nصرت أرد عليك تاني يا قلبي.")
                    log(f"[CONTROL] تشغيل الرد في شات: {name}")
                    return

            # التحقق من حالة الرد التلقائي
            if not is_global_on.get():
                return
            if auto_reply_enabled.get(chat_id, True) is False:
                return

            # حفظ الرسالة في السياق
            if text:
                add_to_history(user_id, "user", text)

            # رد على ستيكر أو GIF
            if event.message.sticker or getattr(event.message, 'gif', None):
                gif_url = get_gif_url(random.choice(["cute", "laugh", "love", "kiss", "happy"]))
                if gif_url:
                    await event.reply(file=gif_url)
                    log("[REPLIED WITH GIF]")
                else:
                    reply = "هههه حلو الستيكر يا قلبي!"
                    await event.reply(reply)
                    add_to_history(user_id, "assistant", reply)
                return

            # رد نصي عادي
            if text:
                history = get_history(user_id)
                reply_text = ask_ai(f"الرسالة من {name}: {text}", history)
                await event.reply(reply_text)
                log(f"[REPLIED] {reply_text}")
                add_to_history(user_id, "assistant", reply_text)
            else:
                reply_text = "شو في يا قلبي؟"
                await event.reply(reply_text)
                add_to_history(user_id, "assistant", reply_text)

        # تذكيرات عشوائية
        async def random_reminders():
            while True:
                await asyncio.sleep(random.randint(1800, 3600))
                if is_global_on.get():
                    log(f"[REMINDER] {random.choice(reminders)}")

        asyncio.create_task(random_reminders())

        async with client:
            await client.run_until_disconnected()

    except Exception as e:
        log(f"[ERROR] {str(e)}")

def start_bot():
    threading.Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()
    log("=== لين 💕 - Auto Reply (on/off + أون/أوف) ===")
    log(f"رقم الهاتف: {phone_number}")
    log("استخدم on / off أو أون / أوف داخل الشات (أنت فقط)\n")

# تشغيل البرنامج
start_bot()
toggle_global()

root.mainloop()
