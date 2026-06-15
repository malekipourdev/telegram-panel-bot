import logging
from telegram import Update
from telegram.ext import ContextTypes
import uuid

from services.panel import PanelAPIClient
from config import settings

logger = logging.getLogger(__name__)
panel_client = PanelAPIClient()


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to 3X-UI Panel Bot\n\n"
        "Available commands:\n"
        "/clients - Get list of all clients\n"
        "/test - Create test client (50MB)"
    )


async def handle_clients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text("Fetching clients...")
        
        data = await panel_client.get_clients_list()
        clients = data.get("obj", [])
        
        if not clients:
            await update.message.reply_text("No clients found")
            return
        
        message = "Clients List:\n\n"
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


async def handle_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text("Creating test client...")
        
        test_email = f"test_{uuid.uuid4().hex[:8]}"
        
        result = await panel_client.create_client(
            email=test_email,
            total_bytes=settings.TEST_CLIENT_SIZE_BYTES,
            inbound_id=settings.DEFAULT_INBOUND_ID
        )
        
        if result.get("success"):
            await update.message.reply_text(
                f"✅ Test client created successfully!\n\n"
                f"Email: `{test_email}`\n"
                f"Size: 50MB\n"
                f"Inbound: {settings.DEFAULT_INBOUND_ID}"
            )
        else:
            await update.message.reply_text(f"Error: {result.get('msg', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error in handle_test: {e}")
        await update.message.reply_text(f"Error creating test client: {str(e)}")
