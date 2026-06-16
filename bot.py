import logging
from telegram.ext import Application, CommandHandler

from config import settings
from handlers.commands import (
    handle_start, 
    handle_clients, 
    handle_balance,
    handle_referral,
    handle_test,    
)

logger = logging.getLogger(__name__)


async def setup_bot() -> Application:
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("clients", handle_clients))
    application.add_handler(CommandHandler("balance", handle_balance))
    application.add_handler(CommandHandler("referral", handle_referral))
    application.add_handler(CommandHandler("test", handle_test))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info("Bot started successfully")
    return application


async def stop_bot(application: Application) -> None:
    await application.stop()
    logger.info("Bot stopped")
