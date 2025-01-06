from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackContext, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime

# ChromeDriver yolunu buraya giriyoruz
CHROMEDRIVER_PATH = "/Users/bugragrms/Desktop/chromedriver-mac-arm64/chromedriver"

# Global değişkenler
user_data = {}


def check_stock(url: str, size: str) -> str:
    """Belirtilen URL ve beden için stok durumunu kontrol eder."""
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
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)

        # Bütün beden butonlarını kontrol et
        size_buttons = driver.find_elements(By.CLASS_NAME, 'size-selector-sizes-size__button')

        # Bedenleri ve uyarıları ekrana yazdırarak hangi bedenlerin bulunduğunu görelim
        for size_button in size_buttons:
            size_info = size_button.find_element(By.CLASS_NAME, 'size-selector-sizes-size__info')
            size_label = size_info.find_element(By.CLASS_NAME, 'size-selector-sizes-size__label').text.strip()
            qa_action = size_button.get_attribute('data-qa-action')  # 'data-qa-action' attribute'unu al

            # Kullanıcının istediği beden ile karşılaştır
            if size_label == size:
                # Eğer "size-low-on-stock" varsa
                if qa_action == "size-low-on-stock":
                    return "Az kalmış, acele et!"

                # Eğer "size-out-of-stock" varsa
                if qa_action == "size-out-of-stock":
                    return None  # Stokta yok, mesaj atma

                # Eğer "size-in-stock" varsa, stokta var
                if qa_action == "size-in-stock":
                    return "Ürün mevcut"

        # Eğer buton bulunamazsa, bedeni bulamıyoruz demektir.
        return "Ürün Bulunamadı"

    finally:
        driver.quit()


async def start(update: Update, context: CallbackContext) -> int:
    """Başlangıç komutu. Kullanıcıdan URL istemek için."""
    await update.message.reply_text("Lütfen kontrol etmek istediğiniz ürünün URL'sini gönderin.")
    return 1  # Bir sonraki adıma geçiş


async def get_url(update: Update, context: CallbackContext) -> int:
    """Kullanıcıdan URL alır ve beden bilgisini ister."""
    user_data["url"] = update.message.text
    await update.message.reply_text("Şimdi lütfen beden bilgisini (ör. S, M, L) gönderin.")
    return 2


async def get_size(update: Update, context: CallbackContext) -> int:
    """Kullanıcıdan beden bilgisini alır ve stok kontrolünü başlatır."""
    user_data["size"] = update.message.text
    await update.message.reply_text(
        "Bilgiler alındı. Stok durumu düzenli olarak kontrol edilecek. Güncellemeler için bekleyin!"
    )

    # APScheduler ile stok kontrolü başlatılıyor
    context.job_queue.run_repeating(
        callback=scheduled_stock_check,
        interval=10,  # 10 saniye
        first=0,
        chat_id=update.message.chat_id,
        name=str(update.message.chat_id),
    )

    # Saat başı çalıştığını bildiren mesajı gönder
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
    url = user_data.get("url")
    size = user_data.get("size")
    if not url or not size:
        return

    try:
        stock_status = check_stock(url, size)
        if stock_status:  # Eğer ürün stokta varsa (None değilse)
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text=f"Stok Durumu: {stock_status}\nLink: {url}",
            )
    except Exception as e:
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=f"Stok kontrolü sırasında bir hata oluştu: {str(e)}",
        )


async def notify_hourly_check(context: CallbackContext) -> None:
    """Saat başı çalıştığını bildiren mesaj gönderir."""
    try:
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="Stok kontrolü hala aktif, kontrol ediyorum..."
        )
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")


async def cancel(update: Update, context: CallbackContext) -> int:
    """Konuşmayı iptal eder."""
    await update.message.reply_text("İşlem iptal edildi.")
    return ConversationHandler.END


def main():
    """Telegram botun ana döngüsü."""
    application = Application.builder().token("7766024537:AAG5JGEZA_swpWJjKWyZWhdQnaJt4Wdj1tU").build()

    # Konuşma işleyicisi
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_url)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_size)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
