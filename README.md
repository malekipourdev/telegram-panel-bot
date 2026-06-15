# Telegram Sanayi Bot

---

خوش آمدید! این پروژه یک ربات تلگرام است که با پنل سنایی یکپارچه شده است.

## ویژگی‌ها

- 🔌 اتصال به API سنایی
- 📋 دریافت لیست کاربران
- 🐳 داکرایزشده کامل
- ⚡ استفاده از FastAPI
- 🔄 Async/await support

## پیش‌نیازها

- Docker و Docker Compose
- یا Python 3.10+

## متغیرهای محیط

فایل `.env` را با مقادیر زیر ایجاد کنید:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
SANAYI_API_BASE_URL=https://api.sanayi.panel
SANAYI_API_KEY=your_api_key
SANAYI_API_SECRET=your_api_secret
API_HOST=0.0.0.0
API_PORT=8000
```

## نصب و اجرا

### با Docker Compose (توصیه‌شده)

```bash
docker-compose up -d
```

### بدون Docker

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرا
python main.py
```

## API Endpoints

- `GET /health` - بررسی وضعیت سرویس
- `GET /api/clients` - دریافت لیست تمام کاربران
- `GET /api/clients/{client_id}` - دریافت اطلاعات کاربر خاص
- `POST /api/webhook/telegram` - Webhook برای دریافت پیام‌های تلگرام

## ساختار پروژه

```
.
├── main.py              # نقطه ورود اپلیکیشن
├── config.py           # تنظیمات و متغیرهای محیط
├── sanayi_client.py    # کلاینت API سنایی
├── routes.py           # مسیرهای API
├── Dockerfile          # تنظیمات Docker
├── docker-compose.yml  # تنظیمات Docker Compose
├── requirements.txt    # وابستگی‌های Python
└── README.md          # این فایل
```
