import httpx
from fastapi import FastAPI, HTTPException, status
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="3X-UI Panel Bridge API")

# Setup configuration according to your Swagger screenshot
# Do not include the trailing slash at the end of the base URL
PANEL_BASE_URL = os.getenv("SANAYI_API_BASE_URL", "https://start724.online:48127")
PANEL_WEB_BASE_PATH = ""  # فعلا خالی، چون URL کامل در .env موجود است

# Replace this with your actual API Token from Settings -> Security
API_BEARER_TOKEN = os.getenv("SANAYI_API_SECRET", "BcHHuqGxpAbcf6b1vBZf96px3lZ3pKBKC62bCCFq1Eij2Ivj")

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "test_token_12345")

# ==================== API ENDPOINTS ====================

@app.get("/clients", tags=["Testing"])
async def get_panel_clients():
    """
    Fetches the clients list from 3X-UI panel using Bearer Token Authentication.
    """
    # Constructing the exact URL from your screenshot:
    list_url = f"{PANEL_BASE_URL}/panel/api/clients/list"
    
    # Setting up the Bearer Token authentication headers as requested by 3X-UI docs
    custom_headers = {
        "Authorization": f"Bearer {API_BEARER_TOKEN}",
        "Accept": "application/json",
        "User-Agent": "FastAPI-Bot-Bridge"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Sending the asynchronous GET request with Bearer token headers
            response = await client.get(list_url, headers=custom_headers, timeout=12.0)
            
            # Handle standard authentication or route errors
            if response.status_code == 401 or response.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired API Bearer Token. Please check panel settings."
                )
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_BAD_GATEWAY,
                    detail=f"Panel API responded with status code: {response.status_code}"
                )
                
            # Returns the successful JSON client list to your frontend/client
            return response.json()

        except httpx.RequestError as exc:
            # Captures network layer issues (DNS failure, connection timeouts, etc.)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Network error trying to reach the upstream panel server: {exc}"
            )


# ==================== TELEGRAM BOT HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start - شروع ربات"""
    await update.message.reply_text(
        "👋 سلام! من ربات پنل 3X-UI هستم.\n\n"
        "دستورات موجود:\n"
        "/clients - دریافت لیست کلاینت‌ها\n"
        "/test - ایجاد کلاینت تست 50 مگابایتی"
    )


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /test - ایجاد کلاینت تست 50 مگابایتی"""
    try:
        await update.message.reply_text("⏳ در حال ایجاد کلاینت تست...")
        
        # ایجاد ایمیل یکتا برای هر تست
        import uuid
        test_email = f"test_{uuid.uuid4().hex[:8]}"
        
        # URL برای اضافه کردن کلاینت
        add_url = f"{PANEL_BASE_URL}/panel/api/clients/add"
        
        # اطلاعات کلاینت تست
        client_payload = {
            "client": {
                "email": test_email,
                "totalGB": 52428800,  # 50 مگابایت (52,428,800 بایت)
                "expiryTime": 0,  # بدون انقضا
                "tgId": 0,
                "limitIp": 0,
                "enable": True
            },
            "inboundIds": [1]
        }
        
        custom_headers = {
            "Authorization": f"Bearer {API_BEARER_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "FastAPI-Bot-Bridge"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                add_url,
                json=client_payload,
                headers=custom_headers,
                timeout=12.0
            )
            
            if response.status_code != 200:
                await update.message.reply_text(
                    f"❌ خطا در ایجاد کلاینت!\nکد وضعیت: {response.status_code}\n\n{response.text[:200]}"
                )
                logger.error(f"Error creating test client: {response.text}")
                return
            
            result = response.json()
            
            if result.get("success"):
                await update.message.reply_text(
                    f"✅ کلاینت تست با موفقیت ایجاد شد!\n\n"
                    f"📧 ایمیل: `{test_email}`\n"
                    f"📦 حجم: 50 مگابایت\n"
                    f"🔌 اینباند: 1\n\n"
                    f"حالا می‌تونی `/clients` رو دریافت کنی و کانفیگ رو کپی کنی"
                )
            else:
                await update.message.reply_text(
                    f"❌ خطایی رخ داد!\n{result.get('msg', 'نامشخص')}"
                )
                
    except Exception as e:
        logger.error(f"Error in test_command: {e}")
        await update.message.reply_text(f"❌ خطایی رخ داد: {str(e)}")


async def clients_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /clients - دریافت لیست کلاینت‌ها"""
    try:
        # صدا زدن API ما
        list_url = f"{PANEL_BASE_URL}/panel/api/clients/list"
        custom_headers = {
            "Authorization": f"Bearer {API_BEARER_TOKEN}",
            "Accept": "application/json",
            "User-Agent": "FastAPI-Bot-Bridge"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(list_url, headers=custom_headers, timeout=12.0)
            
            if response.status_code != 200:
                await update.message.reply_text(
                    f"❌ خطا در دریافت داده‌ها!\nکد وضعیت: {response.status_code}"
                )
                return
            
            clients_data = response.json()
            
            # بررسی اینکه داده‌ها موجود هستند
            # ساختار جواب: {"success": true, "msg": "", "obj": [...]}
            clients_list = clients_data.get("obj", []) if isinstance(clients_data, dict) else []
            
            if not clients_list:
                await update.message.reply_text("📭 هیچ کلاینتی وجود ندارد!")
                return
            
            # ساخت پیام برای نمایش
            message = "📋 لیست کلاینت‌ها:\n\n"
            
            if isinstance(clients_list, list):
                for idx, client in enumerate(clients_list, 1):
                    client_email = client.get("email", "نامشخص") if isinstance(client, dict) else str(client)
                    message += f"{idx}. {client_email}\n"
            
            # ارسال پیام (اگر خیلی بزرگ شد به قطعات تقسیم کنیم)
            if len(message) > 4000:
                for chunk in [message[i:i+4000] for i in range(0, len(message), 4000)]:
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(message)
                
    except Exception as e:
        logger.error(f"Error in clients_command: {e}")
        await update.message.reply_text(f"❌ خطایی رخ داد: {str(e)}")


# ==================== TELEGRAM BOT SETUP ====================

async def setup_telegram_bot():
    """راه‌اندازی ربات تلگرام"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # اضافه کردن handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("clients", clients_command))
    application.add_handler(CommandHandler("test", test_command))
    
    # شروع polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    return application


# Global bot application
telegram_app = None


@app.on_event("startup")
async def startup_event():
    """راه‌اندازی شامل ربات تلگرام"""
    global telegram_app
    try:
        logger.info("🚀 شروع راه‌اندازی ربات تلگرام...")
        telegram_app = await setup_telegram_bot()
        logger.info("✅ ربات تلگرام با موفقیت راه‌اندازی شد")
    except Exception as e:
        logger.error(f"❌ خطا در راه‌اندازی ربات: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """خاموش کردن ربات تلگرام"""
    global telegram_app
    if telegram_app:
        await telegram_app.stop()
        logger.info("ربات تلگرام خاموش شد")