import logging
from telegram import Update
from telegram.ext import ContextTypes

from services.panel import PanelAPIClient
from services.user import UserService
from database import SessionLocal
from config import settings
import uuid
from models import ServicePackage, Client

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

async def handle_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /test command to issue a 50MB free trial configuration.
    Validates monthly eligibility before calling the Panel API.
    """
    user = update.effective_user
    db = SessionLocal()
    
    try:
        # 1. Verify if the user exists in our system
        db_user = UserService.get_user_by_telegram_id(db, user.id)
        if not db_user:
            await update.message.reply_text("Please use /start first to register.")
            return
            
        await update.message.reply_text("⏳ Checking eligibility and creating your test account...")
        
        # 2. Check if the user is eligible for a free trial (Once every 30 days)
        # Note: We will add 'check_trial_eligibility' method to UserService in the next step
        is_eligible = await UserService.check_trial_eligibility(db, db_user.id)
        if not is_eligible:
            await update.message.reply_text(
                "❌ You have already claimed your free trial for this month.\n"
                "Each user is allowed only one test account every 30 days."
                )
            return
            
        # 3. Retrieve the 50MB test package from database
        # 52,428,800 bytes = 50 Megabytes
        test_package = db.query(ServicePackage).filter(ServicePackage.gb_amount == 52428800).first()
        if not test_package:
            await update.message.reply_text("❌ Test package configuration not found in database. Please contact admin.")
            return
            
        # 4. Generate unique identifiers for the new client config
        unique_suffix = uuid.uuid4().hex[:6]
        test_email = f"test_{db_user.id}_{unique_suffix}"
        generated_uuid = str(uuid.uuid4())
        
        # 5. Call your Panel API Client to create the client on 3X-UI server
        # Note: Adjust the method name 'add_new_client' to match your actual PanelAPIClient implementation if needed
        panel_result = await panel_client.add_client(
            email=test_email, 
            total_bytes=test_package.gb_amount,
            inbound_id=1
        )
        
        if panel_result.get("success"):
            # 6. Create subscription record using UserService helper
            # Note: We will add 'create_subscription_record' to UserService as well
            subscription = await UserService.create_subscription_record(
                db=db, 
                user_id=db_user.id, 
                package_id=test_package.id, 
                duration_days=test_package.duration_days or 30
            )
            
            # 7. Map and save the client config into the local database
            new_client = Client(
                user_id=db_user.id,
                subscription_id=subscription.id,
                email=test_email,
                uuid=generated_uuid,
                inbound_id=1,
                status="active",
                total_gb=test_package.gb_amount,
                used_gb=0
            )
            db.add(new_client)
            db.commit()
            
            # 8. Generate dynamic subscription URL and respond to the user
            subscription_url = f"https://sub.yourdomain.com/sub/{generated_uuid}"
            await update.message.reply_text(
                f"✅ Test configuration created successfully!\n\n"
                f"📧 Email: `{test_email}`\n"
                f"📅 Validity: 30 Days\n\n"
                f"🔗 Your Subscription Link:\n"
                f"`{subscription_url}`",
                parse_mode="Markdown"
            )
            logger.info(f"Successfully generated 50MB trial for user {user.id}")
        else:
            error_msg = panel_result.get("msg", "Unknown panel error")
            await update.message.reply_text(f"❌ Failed to communicate with panel: {error_msg}")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error in handle_test: {e}")
        await update.message.reply_text("An internal server error occurred while generating your test account.")
    finally:
        db.close()