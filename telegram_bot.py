import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackContext, MessageHandler, filters
import firebase_admin
from firebase_admin import credentials, firestore
import random
import string
from dotenv import load_dotenv
import os
import logging
from telegram.ext import Application
from logging.handlers import RotatingFileHandler

# .env dosyasını yükleyin
load_dotenv()

# Bot token'ını al
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

if bot_token is None:
    raise ValueError("Bot token environment variable is not set")

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Konsola log yazdırma
        RotatingFileHandler("logs/app.log", maxBytes=5*1024*1024, backupCount=3)  # Log dosyasına yazma
    ]
)

# Firebase bağlantısı
cred = credentials.Certificate("/Users/bugragrms/Desktop/stockChecker/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ChromeDriver'ı otomatik olarak yükle
chromedriver_autoinstaller.install()

# Global değişkenler
user_data = {}

# Stok kontrol fonksiyonu
def check_stock(url: str, size: str) -> str:
    """Belirtilen URL ve beden için stok durumunu kontrol eder."""
    logging.info(f"Stok kontrolü başlatılıyor: URL={url}, Beden={size}")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )

    # ChromeDriver'ı başlat
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        size_buttons = driver.find_elements(By.CLASS_NAME, 'size-selector-sizes-size__button')

        for size_button in size_buttons:
            size_info = size_button.find_element(By.CLASS_NAME, 'size-selector-sizes-size__info')
            size_label = size_info.find_element(By.CLASS_NAME, 'size-selector-sizes-size__label').text.strip()
            qa_action = size_button.get_attribute('data-qa-action')

            if size_label == size:
                if qa_action == "size-low-on-stock":
                    logging.info(f"Az kalmış ürün bulundu: {url}, Beden: {size}")
                    return "Az kalmış, acele et!"
                if qa_action == "size-out-of-stock":
                    logging.info(f"Stokta olmayan ürün bulundu: {url}, Beden: {size}")
                    return None
                if qa_action == "size-in-stock":
                    logging.info(f"Ürün mevcut: {url}, Beden: {size}")
                    return "Ürün mevcut"

        logging.info(f"Ürün bulunamadı: {url}, Beden: {size}")
        return "Ürün Bulunamadı"

    finally:
        driver.quit()

# Veritabanına ürün eklerken her kullanıcıya özgü işlem yapmalıyız
def add_product_to_user(chat_id, url, size, status):
    """Veritabanına ürün ekler."""
    user_ref = db.collection("users").document(str(chat_id))
    products_ref = user_ref.collection("products")

    # Benzersiz ürün ID'si oluştur
    product_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

    products_ref.document(product_id).set({
        "url": url,
        "size": size,
        "status": status
    })

    logging.info(f"Kullanıcıya ürün eklendi: {product_id} - URL: {url}, Beden: {size}, Durum: {status}")
    return product_id  # Ürün ID'sini döndür

# Kullanıcının ürünlerini listeleme
async def list_products(update: Update, context: CallbackContext) -> int:
    """Kullanıcıya mevcut ürünleri listeleyin."""
    chat_id = update.message.chat_id
    user_ref = db.collection("users").document(str(chat_id))
    products_ref = user_ref.collection("products")

    products = products_ref.stream()
    product_list = []
    for product in products:
        product_data = product.to_dict()
        product_list.append(
            f"{product.id} - {product_data['url']} (Beden: {product_data['size']}, Durum: {product_data['status']})")

    if product_list:
        await update.message.reply_text("Mevcut ürünler:\n" + "\n".join(product_list))
        await update.message.reply_text("Silmek istediğiniz ürünün ID'sini gönderin.")
        return 3  # Ürün silme işlemini başlatmak için
    else:
        await update.message.reply_text("Henüz ürün eklemediniz. Lütfen bir ürün ekleyin.")
        logging.info(f"Kullanıcı {chat_id} henüz ürün eklemedi.")
        return ConversationHandler.END


# Ürün silme fonksiyonu
async def delete_product(update: Update, context: CallbackContext) -> int:
    """Kullanıcıdan ürün silme işlemi alınır."""
    product_id = update.message.text.strip()  # Silinmek istenen ürün ID'si
    chat_id = update.message.chat_id
    user_ref = db.collection("users").document(str(chat_id))
    products_ref = user_ref.collection("products")

    # Firebase'den ürünü sil
    product_ref = products_ref.document(product_id)
    product_ref.delete()

    logging.info(f"Kullanıcı {chat_id} ürününü sildi: {product_id}")
    await update.message.reply_text(f"Ürün {product_id} silindi!")
    return ConversationHandler.END


async def start(update: Update, context: CallbackContext) -> int:
    """Başlangıç komutu. Kullanıcıdan URL istemek için."""
    logging.info(f"Kullanıcı {update.message.chat_id} başlangıç komutunu verdi.")
    await update.message.reply_text("Lütfen kontrol etmek istediğiniz ürünün URL'sini gönderin.")
    return 1  # Bir sonraki adıma geçiş


async def get_url(update: Update, context: CallbackContext) -> int:
    """Kullanıcıdan URL alır ve beden bilgisini ister."""
    user_data["url"] = update.message.text
    logging.info(f"Kullanıcı {update.message.chat_id} URL'yi girdi: {user_data['url']}")
    await update.message.reply_text("Şimdi lütfen beden bilgisini (ör. S, M, L) gönderin.")
    return 2


async def get_size(update: Update, context: CallbackContext) -> int:
    """Kullanıcıdan beden bilgisini alır ve stok kontrolünü başlatır."""
    user_data["size"] = update.message.text
    logging.info(f"Kullanıcı {update.message.chat_id} beden bilgisini girdi: {user_data['size']}")
    await update.message.reply_text(
        "Bilgiler alındı. Stok durumu düzenli olarak kontrol edilecek. Güncellemeler için bekleyin!"
    )

    # Firebase'e kaydet
    stock_status = check_stock(user_data["url"], user_data["size"])
    product_id = add_product_to_user(update.message.chat_id, user_data["url"], user_data["size"], stock_status)

    # Saat başı çalıştığını bildiren mesajı gönder
    context.job_queue.run_repeating(
        callback=scheduled_stock_check,
        interval=10,  # 10 saniye
        first=0,
        chat_id=update.message.chat_id,
        name=str(update.message.chat_id),
    )

    # Saat başı kontrolü bildir
    context.job_queue.run_repeating(
        callback=notify_hourly_check,
        interval=3600,  # 1 saat
        first=0,
        chat_id=update.message.chat_id,
        name=f"hourly_check_{update.message.chat_id}",
    )

    return ConversationHandler.END

async def scheduled_stock_check(context: CallbackContext) -> None:
    """Düzenli aralıklarla stok kontrolü yapar ve sonucu kullanıcıya gönderir."""
    chat_id = context.job.chat_id
    user_ref = db.collection("users").document(str(chat_id))  # Kullanıcıya özgü referans
    products_ref = user_ref.collection("products")  # Kullanıcıya özgü ürün koleksiyonu

    try:
        for product_doc in products_ref.stream():
            product = product_doc.to_dict()
            url = product.get("url")
            size = product.get("size")
            stock_status = check_stock(url, size)

            # Stok durumu güncelleme ve bildirim gönderme
            if stock_status:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"Stok Durumu: {stock_status}\nLink: {url}",
                )
                # Stok durumunu Firebase'de güncelle
                products_ref.document(product_doc.id).update({"status": stock_status})
                logging.info(f"Stok durumu güncellendi: {url} - {size} - Durum: {stock_status}")
            elif stock_status is None:
                # Ürün stokta yoksa sadece durumu güncelle
                products_ref.document(product_doc.id).update({"status": "Ürün tükenmiş"})
                logging.info(f"Stokta olmayan ürün güncellendi: {url} - {size} - Durum: 'Ürün tükenmiş'")

    except Exception as e:
        logging.error(f"Stok kontrolü sırasında bir hata oluştu: {str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Stok kontrolü sırasında bir hata oluştu: {str(e)}",
        )


async def notify_hourly_check(context: CallbackContext) -> None:
    """Saat başı çalıştığını bildiren mesaj gönderir."""
    try:
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="Stok kontrolü hala aktif, kontrol ediyorum..."
        )
        logging.info(f"Saat başı kontrol: Kullanıcı {context.job.chat_id}")
    except Exception as e:
        logging.error(f"Saat başı kontrol mesajı gönderilirken hata oluştu: {str(e)}")


async def cancel(update: Update, context: CallbackContext) -> int:
    """Konuşmayı iptal eder."""
    logging.info(f"Kullanıcı {update.message.chat_id} işlemi iptal etti.")
    await update.message.reply_text("İşlem iptal edildi.")
    return ConversationHandler.END


def main():
    """Telegram botun ana döngüsü."""
    application = Application.builder().token(bot_token).build()

    # Konuşma işleyicisi
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("list", list_products)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_url)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_size)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_product)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    logging.info("Telegram bot çalışmaya başladı.")
    application.run_polling()


if __name__ == "__main__":
    main()
