import os
import logging
from PIL import Image
from io import BytesIO
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =============================================
# SOZLAMALAR
# =============================================
TOKEN = os.environ.get("TOKEN")
LOGO_PATH = "logo.png"
LOGO_SCALE = 0.10
LOGO_POSITION = "bottom-left"
LOGO_OPACITY = 220
LOGO_MARGIN = 15
# =============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot ishlayapti!")
    def log_message(self, *args):
        pass

def run_server():
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()


def add_logo(image_bytes: bytes) -> bytes:
    main_img = Image.open(BytesIO(image_bytes)).convert("RGBA")
    main_w, main_h = main_img.size

    logo = Image.open(LOGO_PATH).convert("RGBA")

    logo_w = int(main_w * LOGO_SCALE)
    logo_h = int(logo.height * (logo_w / logo.width))
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

    if LOGO_OPACITY < 255:
        r, g, b, a = logo.split()
        a = a.point(lambda x: int(x * LOGO_OPACITY / 255))
        logo = Image.merge("RGBA", (r, g, b, a))

    m = LOGO_MARGIN
    positions = {
        "bottom-right": (main_w - logo_w - m, main_h - logo_h - m),
        "bottom-left":  (m, main_h - logo_h - m),
        "top-right":    (main_w - logo_w - m, m),
        "top-left":     (m, m),
        "center":       ((main_w - logo_w) // 2, (main_h - logo_h) // 2),
    }
    pos = positions.get(LOGO_POSITION, positions["bottom-left"])

    overlay = Image.new("RGBA", main_img.size, (0, 0, 0, 0))
    overlay.paste(logo, pos, logo)
    result = Image.alpha_composite(main_img, overlay)

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
    await update.message.reply_text("⏳ Rasm qayta ishlanmoqda...")
    try:
        photo = await update.message.photo[-1].get_file()
        image_bytes = await photo.download_as_bytearray()
        result_bytes = add_logo(bytes(image_bytes))
        await update.message.reply_photo(
            photo=BytesIO(result_bytes),
            caption="✅ Tayyor! Logo qo'shildi."
        )
    except FileNotFoundError:
        await update.message.reply_text("❌ Xato: logo.png fayli topilmadi!")
    except Exception as e:
        logging.error(f"Xato: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text("❌ Xato: logo.png fayli topilmadi!")
    except Exception as e:
        logging.error(f"Xato: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


def main():
    Thread(target=run_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    print("✅ Bot ishlamoqda...")
    app.run_polling()


if __name__ == "__main__":
    main()
