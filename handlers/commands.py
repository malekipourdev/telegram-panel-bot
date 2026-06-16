import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
            "/buy - Buy new config"
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
        
        referral_url = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={referral_link.invite_code}"
        
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
            
        # 4. Generate unique email identifier safely on the bot side
        unique_suffix = uuid.uuid4().hex[:6]
        test_email = f"test_{db_user.id}_{unique_suffix}"

        # 5. Call Panel API (It will create the account and return the REAL server-generated UUID)
        panel_result = await panel_client.create_client(
            email=test_email, 
            total_bytes=test_package.gb_amount,
            inbound_id=1
        )
        
        if panel_result.get("success"):
            # Extract the actual verified UUID from the response dict
            actual_uuid = panel_result.get("uuid")

            # 6. Create subscription record using UserService helper
            subscription = await UserService.create_subscription_record(
                db=db, 
                user_id=db_user.id, 
                package_id=test_package.id, 
                duration_days=test_package.duration_days or 30
            )
            
            # 7. Save into local database using the REAL panel UUID
            new_client = Client(
                user_id=db_user.id,
                subscription_id=subscription.id,
                email=test_email,
                uuid=actual_uuid,  # 100% matched with panel now
                inbound_id=1,
                status="active",
                total_gb=test_package.gb_amount,
                used_gb=0
            )
            db.add(new_client)
            db.commit()
            
            # 8. Dynamic subscription URL using the real UUID
            subscription_url = f"{settings.PANEL_SUB_URL_BASE}/{actual_uuid}"
            
            await update.message.reply_text(
                f"✅ Test configuration claimed successfully!\n\n"
                f"📋 Specifications:\n"
                f"📧 Email: `{test_email}`\n"
                f"📅 Validity: 30 Days\n\n"
                f"🔗 Your Subscription Link:\n"
                f"`{subscription_url}`",
                parse_mode="Markdown"
            )
            logger.info(f"Successfully generated 50MB trial for user {user.id} with verified UUID {actual_uuid}")
        else:
            error_msg = panel_result.get("msg", "Unknown panel error")
            await update.message.reply_text(f"❌ Failed to communicate with panel: {error_msg}")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error in handle_test: {e}")
        await update.message.reply_text("An internal server error occurred while generating your test account.")
    finally:
        db.close()

async def handle_buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Displays the available shopping packages to the user using inline keyboard buttons.
    """
    db = SessionLocal()
    try:
        packages = UserService.get_active_packages(db)
        if not packages:
            await update.message.reply_text("❌ No active packages found at the moment.")
            return

        keyboard = []
        for pkg in packages:
            # Format: Name - Gigabytes GB - Price Tomans
            # Storing package ID inside the callback_data
            button_text = f"📦 {pkg.name} ({pkg.gb_amount // (1024**3)}GB) - {pkg.price:,.0f} Tomans"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"buy_pkg_{pkg.id}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🛒 Please select your desired service package:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error displaying buy menu: {e}")
        await update.message.reply_text("An error occurred while loading the shop menu.")
    finally:
        db.close()

async def handle_package_purchase_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processes the inline button click for package injection. Checks balance,
    deducts funds, communicates with Sanayi Panel and registers the new subscription.
    """
    query = update.callback_query
    await query.answer() # Acknowledge the callback immediately to stop the loading animation on Telegram
    
    user = query.from_user
    package_id = int(query.data.split("_")[-1]) # Extracts the trailing ID from 'buy_pkg_X'
    
    db = SessionLocal()
    try:
        # 1. Verify User and Package existence
        db_user = UserService.get_user_by_telegram_id(db, user.id)
        package = db.query(ServicePackage).filter(ServicePackage.id == package_id, ServicePackage.is_active == True).first()
        
        if not package:
            await query.edit_message_text("❌ This package is no longer available.")
            return

        await query.edit_message_text("⏳ Processing payment and provisioning account on the server...")

        # 2. Try to deduct internal balance
        is_paid = await UserService.process_purchase_payment(db, db_user.id, package.price, package.id)
        if not is_paid:
            await query.edit_message_text(
                f"❌ Insufficient Balance.\n\n"
                f"Package Price: {package.price:,.0f} Tomans\n"
                f"Your Current Balance: {db_user.balance:,.0f} Tomans\n\n"
                f"Please charge your wallet first using the /balance menu."
            )
            return

        # 3. Create unique identifiers for the panel configuration
        unique_suffix = uuid.uuid4().hex[:6]
        client_email = f"user_{db_user.id}_{unique_suffix}"

        # 4. Request the Panel API Client to create the account 
        # (It will create the account and return the REAL server-generated UUID)
        panel_result = await panel_client.create_client(
            email=client_email,
            total_bytes=package.gb_amount,
            inbound_id=1 # Default inbound ID
        )

        if panel_result.get("success"):
            # === FIXED: Extract the actual verified UUID from the response dict exactly like /test ===
            actual_uuid = panel_result.get("uuid")

            # 5. Build subscription database record
            subscription = await UserService.create_subscription_record(
                db=db,
                user_id=db_user.id,
                package_id=package.id,
                duration_days=package.duration_days or 30
            )

            # 6. Save the genuine client node linking the subscription ID and using the REAL panel UUID
            new_client = Client(
                user_id=db_user.id,
                subscription_id=subscription.id,
                email=client_email,
                uuid=actual_uuid, # <=== 100% matched with panel now!
                inbound_id=1,
                status="active",
                total_gb=package.gb_amount,
                used_gb=0
            )
            db.add(new_client)
            
            # Commit all operations together atomically (Balance deduction + Sub creation + Client creation)
            db.commit()

            # 7. Deliver the clean subscription URL to the buyer using the real UUID
            subscription_url = f"{settings.PANEL_SUB_URL_BASE}/{actual_uuid}"
            await query.edit_message_text(
                f"🎉 Order Completed Successfully!\n\n"
                f"📦 Package: *{package.name}*\n"
                f"📊 Volume: {package.gb_amount // (1024**3)} GB\n"
                f"📅 Expiry Period: {package.duration_days or 30} Days\n\n"
                f"🔗 Your Configuration Subscription Link:\n"
                f"`{subscription_url}`",
                parse_mode="Markdown"
            )
            logger.info(f"User {user.id} successfully purchased package {package.name} (ID: {package.id}) with UUID {actual_uuid}")
        else:
            # Rollback the balance deduction since the panel failed to create the account
            db.rollback()
            error_msg = panel_result.get("msg", "Panel connection fault")
            await query.edit_message_text(f"❌ Core Server Error: {error_msg}. Money has been refunded back to your balance.")

    except Exception as e:
        db.rollback()
        logger.error(f"Fatal error in handle_package_purchase_callback: {e}")
        await query.edit_message_text("❌ A critical internal system error occurred during purchase.")
    finally:
        db.close()