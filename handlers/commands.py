import logging
from telegram import Update
from telegram.ext import ContextTypes

from services.panel import PanelAPIClient
from services.user import UserService
from database import SessionLocal
from config import settings

logger = logging.getLogger(__name__)
panel_client = PanelAPIClient()


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db = SessionLocal()
    
    try:
        db_user = UserService.get_or_create_user(
            db=db,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        await update.message.reply_text(
            "Welcome to 3X-UI Panel Bot\n\n"
            "Available commands:\n"
            "/clients - Get list of all clients\n"
            "/test - Create test client (50MB)\n"
            "/balance - Check your balance\n"
            "/referral - Get your referral link"
        )
        logger.info(f"User {user.id} started the bot")
    except Exception as e:
        logger.error(f"Error in handle_start: {e}")
        await update.message.reply_text("Error starting bot. Please try again later.")
    finally:
        db.close()


async def handle_clients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db = SessionLocal()
    
    try:
        db_user = UserService.get_user_by_telegram_id(db, user.id)
        
        if not db_user:
            await update.message.reply_text("Please use /start first to register.")
            return
        
        await update.message.reply_text("Fetching clients...")
        
        data = await panel_client.get_clients_list()
        clients = data.get("obj", [])
        
        if not clients:
            await update.message.reply_text("No clients found")
            return
        
        message = "Your Clients:\n\n"
        for idx, client in enumerate(clients, 1):
            email = client.get("email", "Unknown")
            message += f"{idx}. {email}\n"
        
        if len(message) > 4096:
            for chunk in [message[i:i+4096] for i in range(0, len(message), 4096)]:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in handle_clients: {e}")
        await update.message.reply_text(f"Error fetching clients: {str(e)}")
    finally:
        db.close()


async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db = SessionLocal()
    
    try:
        db_user = UserService.get_user_by_telegram_id(db, user.id)
        
        if not db_user:
            await update.message.reply_text("Please use /start first to register.")
            return
        
        balance = UserService.get_user_balance(db, db_user.id)
        
        await update.message.reply_text(
            f"💰 Your Balance\n\n"
            f"Balance: {balance:,.2f} Tomans"
        )
    except Exception as e:
        logger.error(f"Error in handle_balance: {e}")
        await update.message.reply_text("Error fetching balance.")
    finally:
        db.close()


async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db = SessionLocal()
    
    try:
        db_user = UserService.get_user_by_telegram_id(db, user.id)
        
        if not db_user:
            await update.message.reply_text("Please use /start first to register.")
            return
        
        referral_link = UserService.get_referral_link(db, db_user.id)
        
        if not referral_link:
            referral_link = UserService.create_referral_link(db, db_user.id)
        
        stats = UserService.get_user_referral_stats(db, db_user.id)
        
        referral_url = f"https://t.me/your_bot_username?start={referral_link.invite_code}"
        
        await update.message.reply_text(
            f"🔗 Your Referral Link\n\n"
            f"Link: {referral_url}\n\n"
            f"Stats:\n"
            f"Clicks: {stats['click_count']}\n"
            f"Referrals: {stats['referral_count']}\n"
            f"Total Reward: {stats['total_reward']:,.2f} Tomans"
        )
    except Exception as e:
        logger.error(f"Error in handle_referral: {e}")
        await update.message.reply_text("Error fetching referral link.")
    finally:
        db.close()
