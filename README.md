# ZARA Stock Checker Telegram Bot

Bu Telegram botu, kullanıcıların belirli bir ürünün belirli bir bedeni için stok kontrolü yapmalarına yardımcı olur. Bot, her kullanıcının istediği ürün ve beden için stok durumunu takip eder ve kullanıcıya güncellemeler gönderir. Ayrıca, kullanıcılar ürünleri ekleyebilir, listeleyebilir ve silebilirler.

## Özellikler

- **Ürün Ekleme**: Kullanıcı, istediği ürünün URL'sini ve beden bilgisini girerek ürünü sisteme ekler.
- **Stok Durumu Kontrolü**: Bot, eklenen ürünün stok durumunu (Mevcut, Az kalmış, Tükenmiş) kontrol eder ve kullanıcıya bildirim gönderir.
- **Ürün Listeleme ve Silme**: Kullanıcı, eklediği ürünleri listeleyebilir ve dilediği ürünü silebilir.
- **Düzenli Stok Kontrolü**: Bot, her saat başı stok durumunu günceller ve kullanıcıya bildirir.
- **Logging ve Hata Yönetimi**: Tüm işlemler loglanır, hata durumlarında kullanıcıya bildirim gönderilir.

## Teknolojiler

- **Python 3.x**
- **Selenium**: Web sayfalarındaki ürünlerin stok durumunu kontrol etmek için kullanılır.
- **Firebase**: Kullanıcı bilgileri ve ürünler Firebase Firestore veritabanında saklanır.
- **Telegram Bot API**: Telegram üzerinden bot ile etkileşim sağlanır.
- **Logging**: Bot aktiviteleri loglanır ve hata durumları izlenir.
- **dotenv**: Ortam değişkenlerini (bot token'ı gibi) güvenli bir şekilde yüklemek için kullanılır.

## Kurulum

### 1. Gereksinimler

- Python 3.x
- `pip` paket yöneticisi

### 2. Bağımlılıkların Yüklenmesi

Proje klasörüne gidin ve gerekli bağımlılıkları yüklemek için aşağıdaki komutu çalıştırın:

```bash
pip install -r requirements.txt
```

## Ortam Değişkenlerinin Ayarlanması

`.env` dosyası içerisinde bulunan `TELEGRAM_BOT_TOKEN` yerine, botunuzu oluşturduğunuzda Telegram'dan alacağınız token'ı ekleyin.

## Firebase Bağlantısı

Firebase kullanıyorsanız, Firebase Console üzerinden bir proje oluşturun ve Firebase Admin SDK için JSON formatında bir anahtar (service account key) oluşturun. Bu anahtarı `serviceAccountKey.json` olarak kaydedin ve proje kök dizinine yerleştirin.

## Firebase Veritabanı Düzeni

### Koleksiyonlar ve Belgeler

#### `users` (Koleksiyon)
- `<user_id>` (Belge, her kullanıcı için benzersiz bir belge ID'si)

#### Alt Koleksiyon: `products`
- `<product_id>` (Belge, her ürün için benzersiz bir belge ID'si)
  - `url` (Alan): Ürünün URL'si
  - `size` (Alan): Ürünün bedeni
  - `status` (Alan): Stok durumu (ör. `"Ürün mevcut"`, `"Az kalmış"`, `"Ürün tükenmiş"`)


## ChromeDriver

Bot, Selenium kullanarak web sayfalarını kontrol eder. `chromedriver-autoinstaller` kullanılarak gerekli ChromeDriver sürümü otomatik olarak yüklenecektir. Ancak, Google Chrome'un sisteminizde yüklü olması gerekir.

## Botu Çalıştırma 

Botu çalıştırmak için aşağıdaki komutu kullanın:

```bash
python bot.py
```

# Kullanım

## Başlatma

Bot ile etkileşime başlamak için /start komutunu kullanın. Bot, kullanıcıdan ürün URL'sini ve beden bilgisini isteyecektir.

- **URL:** Kullanıcı, kontrol etmek istediği ürünün URL'sini gönderecek.
- **Beden:** Kullanıcı, ürünün beden bilgisini (ör. S, M, L) gönderecek.
- **Stok Durumu:** Bot, girilen URL ve beden için stok durumunu kontrol edecek. Durum "Ürün mevcut", "Az kalmış" veya "Ürün tükenmiş" olabilir.
