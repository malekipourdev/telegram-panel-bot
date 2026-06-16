import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from models import User, ReferralLink, ReferralReward, Payment, UserServiceSubscription, ServicePackage
from config import settings
import random
import string
from decimal import Decimal

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def get_or_create_user(db: Session, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> User:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=False,
                is_active=True,
                balance=0.00
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {telegram_id}")
        
        return user
    
    @staticmethod
    def get_user_by_telegram_id(db: Session, telegram_id: int) -> User:
        return db.query(User).filter(User.telegram_id == telegram_id).first()
    
    @staticmethod
    def get_user_balance(db: Session, user_id: int) -> float:
        user = db.query(User).filter(User.id == user_id).first()
        return float(user.balance) if user else 0.0
    
    @staticmethod
    def create_referral_link(db: Session, user_id: int) -> ReferralLink:
        existing = db.query(ReferralLink).filter(ReferralLink.user_id == user_id).first()
        
        if existing:
            return existing
        
        invite_code = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        referral_link = ReferralLink(
            user_id=user_id,
            invite_code=invite_code
        )
        db.add(referral_link)
        db.commit()
        db.refresh(referral_link)
        logger.info(f"Created referral link for user {user_id}: {invite_code}")
        
        return referral_link
    
    @staticmethod
    def get_referral_link(db: Session, user_id: int) -> ReferralLink:
        return db.query(ReferralLink).filter(ReferralLink.user_id == user_id).first()
    
    @staticmethod
    def add_balance(db: Session, user_id: int, amount: float) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            user.balance = float(user.balance) + amount
            db.commit()
            db.refresh(user)
            logger.info(f"Added {amount} to user {user_id} balance. New balance: {user.balance}")
        
        return user
    
    @staticmethod
    def deduct_balance(db: Session, user_id: int, amount: float) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False
        
        current_balance = float(user.balance)
        if current_balance < amount:
            return False
        
        user.balance = current_balance - amount
        db.commit()
        db.refresh(user)
        logger.info(f"Deducted {amount} from user {user_id} balance. New balance: {user.balance}")
        
        return True
    
    @staticmethod
    def is_user_admin(db: Session, user_id: int) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        return user.is_admin if user else False
    
    @staticmethod
    def is_user_admin_by_telegram_id(db: Session, telegram_id: int) -> bool:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        return user.is_admin if user else False
    
    @staticmethod
    def get_user_referral_stats(db: Session, user_id: int) -> dict:
        referral_link = db.query(ReferralLink).filter(ReferralLink.user_id == user_id).first()
        
        if not referral_link:
            return {"click_count": 0, "referral_count": 0, "total_reward": 0}
        
        total_reward = db.query(func.sum(ReferralReward.reward_amount)).filter(
            ReferralReward.referrer_user_id == user_id,
            ReferralReward.is_claimed == True
        ).scalar()
        
        return {
            "click_count": referral_link.click_count,
            "referral_count": referral_link.referral_count,
            "total_reward": float(total_reward) if total_reward else 0.0
        }

    @staticmethod
    async def check_trial_eligibility(db: Session, user_id: int) -> bool:
        """
        Checks if a user is eligible for a free trial.
        A user can only request one trial every 30 days.
        """
        # Calculate the datetime for 30 days ago from now
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Check if any active/expired test subscription exists in the last 30 days
        has_recent_trial = db.query(UserServiceSubscription).join(
            ServicePackage, UserServiceSubscription.service_package_id == ServicePackage.id
        ).filter(
            UserServiceSubscription.user_id == user_id,
            ServicePackage.gb_amount == 52428800,  # 50 MB in bytes
            UserServiceSubscription.created_at >= thirty_days_ago
        ).first()
        
        # If a recent trial is found, the user is NOT eligible (returns False)
        return has_recent_trial is None

    @staticmethod
    async def create_subscription_record(db: Session, user_id: int, package_id: int, duration_days: int) -> UserServiceSubscription:
        """
        Creates a new service subscription record in the database.
        """
        expiry_date = datetime.utcnow() + timedelta(days=duration_days)
        
        new_sub = UserServiceSubscription(
            user_id=user_id,
            service_package_id=package_id,
            status="active",
            expiry_date=expiry_date
        )
        db.add(new_sub)
        db.commit()
        db.refresh(new_sub)
        return new_sub
    
    @staticmethod
    def get_active_packages(db: Session) -> list[ServicePackage]:
        """
        Retrieves all currently active service packages available for purchase.
        """
        return db.query(ServicePackage).filter(ServicePackage.is_active == True).all()

    @staticmethod
    async def process_purchase_payment(db: Session, user_id: int, package_price: Decimal, package_id: int) -> bool:
        """
        Deducts the user balance and logs a verified payment record for the service purchase.
        Returns True if successful, False if insufficient balance.
        """
        user = db.query(User).filter(User.id == user_id).with_for_update().first()
        
        if user.balance < package_price:
            return False
            
        # Deduct the amount safely
        user.balance -= package_price
        
        # Log the internal payment receipt
        purchase_payment = Payment(
            user_id=user.id,
            amount=package_price,
            status="verified", # Verified immediately since it uses internal wallet balance
            payment_type="service_purchase",
            description=f"Purchased package ID: {package_id}",
            created_at=datetime.utcnow(),
            verified_at=datetime.utcnow()
        )
        db.add(purchase_payment)
        # Note: We do not commit here yet. We commit in the command handler after the panel successfully builds the config.
        return True
    