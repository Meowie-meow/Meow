import telebot
import requests
import urllib.parse
import time

# =========================================================
# تنظیمات
# =========================================================

BOT_TOKEN = "توکن_ربات_خودت_رو_اینجا_بذار"
MODEL = "flux"   # یا turbo / kontext


# =========================================================
# ربات
# =========================================================

bot = telebot.TeleBot(8881950718:AAFR0GeaLBBr3Rk1rGcULyyUz4KdyOyeWgI)


def translate_to_english(text):
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": "fa|en"},
            timeout=10
        )
        data = r.json()
        result = data["responseData"]["translatedText"]
        return result if result else text
    except Exception:
        return text


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "سلام 👋\n\n"
        "توضیح تصویرت رو به فارسی بنویس تا برات بسازم.\n\n"
        "مثال:\n"
        "یک گربه روی رنگین‌کمان"
    )


@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    prompt_fa = message.text.strip()
    if not prompt_fa:
        return

    msg = bot.reply_to(message, "⏳ در حال ساخت تصویر...")

    try:
        # ترجمه به انگلیسی
        prompt_en = translate_to_english(prompt_fa)
        print(f"FA: {prompt_fa}")
        print(f"EN: {prompt_en}")

        # endpoint رایگان (بدون کلید)
        encoded = urllib.parse.quote(prompt_en)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model={MODEL}&width=1024&height=1024&nologo=true"
        )
        print(f"URL: {url}")

        r = requests.get(url, timeout=180)
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type')}")

        if r.status_code == 429:
            bot.edit_message_text(
                "⏳ درخواست‌ها زیاده. لطفاً ۱۵ ثانیه صبر کن و دوباره بفرست.",
                chat_id=message.chat.id,
                message_id=msg.message_id
            )
            return

        if r.status_code != 200:
            bot.edit_message_text(
                f"❌ خطا: HTTP {r.status_code}",
                chat_id=message.chat.id,
                message_id=msg.message_id
            )
            return

        if not r.headers.get("Content-Type", "").startswith("image"):
            bot.edit_message_text(
                f"❌ پاسخ سرور تصویر نیست:\n{r.text[:200]}",
                chat_id=message.chat.id,
                message_id=msg.message_id
            )
            return

        # ارسال تصویر
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_photo(
            message.chat.id,
            photo=r.content,
            caption=f"🎨 {prompt_fa}"
        )

    except Exception as e:
        print(f"ERROR: {e}")
        try:
            bot.edit_message_text(
                f"❌ خطا:\n{str(e)[:200]}",
                chat_id=message.chat.id,
                message_id=msg.message_id
            )
        except Exception:
            pass


# =========================================================
# اجرا
# =========================================================

print("✅ ربات روشنه. منتظر پیام‌ها...")
bot.polling(none_stop=True)
