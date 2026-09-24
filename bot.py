import telebot
import requests
import urllib.parse
import io
from PIL import Image

# =========================================================
# تنظیمات
# =========================================================

BOT_TOKEN = "8881950718:AAFR0GeaLBBr3Rk1rGcULyyUz4KdyOyeWgI"
MODEL = "flux"   # یا turbo / kontext


# =========================================================
# ربات
# =========================================================

bot = telebot.TeleBot(BOT_TOKEN)


# =========================================================
# ترجمه فارسی به انگلیسی
# =========================================================

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


# =========================================================
# حذف لوگو از عکس
# =========================================================

def remove_watermark(image_bytes, crop_percent=10):
    """
    حذف لوگو از عکس با کراپ کردن درصدی از پایین عکس.
    crop_percent: چند درصد از پایین حذف بشه (پیش‌فرض ۱۰٪)
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size

    # محاسبه ارتفاع جدید (بالای عکس بمونه)
    new_height = int(h * (100 - crop_percent) / 100)

    # کراپ کردن عکس (چپ، بالا، راست، پایین)
    cropped = img.crop((0, 0, w, new_height))

    # تبدیل به بایت
    out = io.BytesIO()
    cropped.save(out, format="JPEG", quality=95)
    return out.getvalue()


# =========================================================
# دستور start
# =========================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "سلام 👋\n\n"
        "توضیح تصویرت رو به فارسی بنویس تا برات بسازم.\n\n"
        "مثال:\n"
        "یک گربه روی رنگین‌کمان"
    )


# =========================================================
# دریافت پیام و ساخت تصویر
# =========================================================

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

        # ساخت URL - endpoint رایگان
        encoded = urllib.parse.quote(prompt_en)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model={MODEL}&width=1024&height=1024&nologo=true"
        )
        print(f"URL: {url}")

        # درخواست
        r = requests.get(url, timeout=180)
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type')}")

        # مدیریت خطاها
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

        # حذف لوگو (کراپ ۱۰٪ از پایین عکس)
        clean_image = remove_watermark(r.content, crop_percent=10)

        # ارسال تصویر تمیز
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_photo(
            message.chat.id,
            photo=clean_image,
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
