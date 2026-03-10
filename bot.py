import os
import logging
from PIL import Image
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =============================================
# SOZLAMALAR - bularni o'zgartiring
# =============================================
import os
TOKEN = os.environ.get("TOKEN")   # BotFather dan olgan token
LOGO_PATH = "logo.png"             # Logo fayl nomi (bot.py bilan bir papkada bo'lishi kerak)
LOGO_SCALE = 0.12                  # Logoning kattaligi: 0.20 = rasmning 15% i
LOGO_POSITION = "bottom-left"      # Joylashuv: bottom-right | bottom-left | top-right | top-left | center
LOGO_OPACITY = 220                 # Shaffoflik: 0 (ko'rinmas) ~ 255 (to'liq ko'rinadi)
LOGO_MARGIN = 15                   # Chekkadan masofa (pixel)
# =============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def add_logo(image_bytes: bytes) -> bytes:
    """Rasmga logo qo'shadi va bytes qaytaradi."""
    # Asosiy rasmni ochish
    main_img = Image.open(BytesIO(image_bytes)).convert("RGBA")
    main_w, main_h = main_img.size

    # Logoni ochish
    logo = Image.open(LOGO_PATH).convert("RGBA")

    # Logo o'lchamini hisoblash
    logo_w = int(main_w * LOGO_SCALE)
    logo_h = int(logo.height * (logo_w / logo.width))
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

    # Logo shaffofligini sozlash
    if LOGO_OPACITY < 255:
        r, g, b, a = logo.split()
        a = a.point(lambda x: int(x * LOGO_OPACITY / 255))
        logo = Image.merge("RGBA", (r, g, b, a))

    # Logo joylashuvini hisoblash
    m = LOGO_MARGIN
    positions = {
        "bottom-right": (main_w - logo_w - m, main_h - logo_h - m),
        "bottom-left":  (m, main_h - logo_h - m),
        "top-right":    (main_w - logo_w - m, m),
        "top-left":     (m, m),
        "center":       ((main_w - logo_w) // 2, (main_h - logo_h) // 2),
    }
    pos = positions.get(LOGO_POSITION, positions["bottom-right"])

    # Logoni rasmga qo'yish
    overlay = Image.new("RGBA", main_img.size, (0, 0, 0, 0))
    overlay.paste(logo, pos, logo)
    result = Image.alpha_composite(main_img, overlay)

    # JPEG sifatida saqlash
    output = BytesIO()
    result.convert("RGB").save(output, format="JPEG", quality=95)
    output.seek(0)
    return output.read()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! 👋\n\n"
        "Menga rasm yuboring — men unga avtomatik logo qo'shib qaytaraman. 🖼️✅"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi rasm yuborsa ishga tushadi."""
    await update.message.reply_text("⏳ Rasm qayta ishlanmoqda...")

    try:
        # Telegramdan rasmni yuklab olish (eng yuqori sifatli)
        photo = await update.message.photo[-1].get_file()
        image_bytes = await photo.download_as_bytearray()

        # Logoni qo'shish
        result_bytes = add_logo(bytes(image_bytes))

        # Natijani yuborish
        await update.message.reply_photo(
            photo=BytesIO(result_bytes),
            caption="✅ Tayyor! Logo qo'shildi."
        )

    except FileNotFoundError:
        await update.message.reply_text(
            "❌ Xato: `logo.png` fayli topilmadi!\n"
            "Bot papkasiga logo.png ni joylashtiring."
        )
    except Exception as e:
        logging.error(f"Xato: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fayl sifatida yuborilgan rasmlarni ham qabul qiladi."""
    doc = update.message.document
    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        await update.message.reply_text("⚠️ Faqat rasm fayllari qabul qilinadi.")
        return

    await update.message.reply_text("⏳ Rasm qayta ishlanmoqda...")

    try:
        file = await doc.get_file()
        image_bytes = await file.download_as_bytearray()
        result_bytes = add_logo(bytes(image_bytes))

        await update.message.reply_photo(
            photo=BytesIO(result_bytes),
            caption="✅ Tayyor! Logo qo'shildi."
        )

    except FileNotFoundError:
        await update.message.reply_text("❌ Xato: `logo.png` fayli topilmadi!")
    except Exception as e:
        logging.error(f"Xato: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


def main():
    if not os.path.exists(LOGO_PATH):
        print(f"⚠️  DIQQAT: '{LOGO_PATH}' fayli topilmadi! Bot ishlaydi, lekin xato beradi.")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    print("✅ Bot ishlamoqda... Ctrl+C bilan to'xtatish mumkin.")
    app.run_polling()


if __name__ == "__main__":
    main()
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot ishlayapti!")
    def log_message(self, *args):
        pass

def run_server():
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

Thread(target=run_server, daemon=True).start()
