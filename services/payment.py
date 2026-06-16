import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Payment, PaymentMethod, User
from datetime import datetime

logger = logging.getLogger(__name__)


class PaymentService:
    @staticmethod
    def create_payment_request(db: Session, user_id: int, amount: float, 
                              payment_type: str = "balance_increase") -> Payment:
        payment = Payment(
            user_id=user_id,
            amount=amount,
            status="pending",
            payment_type=payment_type
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        logger.info(f"Created payment request: {payment.id} for user {user_id}, amount: {amount}")
        
        return payment
    
    @staticmethod
    def get_pending_payments(db: Session) -> list:
        return db.query(Payment).filter(Payment.status == "pending").all()
    
    @staticmethod
    def get_payment_by_id(db: Session, payment_id: int) -> Payment:
        return db.query(Payment).filter(Payment.id == payment_id).first()
    
    @staticmethod
    def verify_payment(db: Session, payment_id: int, admin_id: int, admin_note: str = None) -> Payment:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if payment:
            payment.status = "verified"
            payment.verified_at = datetime.utcnow()
            payment.verified_by_admin_id = admin_id
            payment.admin_note = admin_note
            
            if payment.payment_type == "balance_increase":
                user = db.query(User).filter(User.id == payment.user_id).first()
                if user:
                    user.balance = float(user.balance) + float(payment.amount)
            
            db.commit()
            db.refresh(payment)
            logger.info(f"Verified payment: {payment_id}")
        
        return payment
    
    @staticmethod
    def reject_payment(db: Session, payment_id: int, admin_id: int, admin_note: str = None) -> Payment:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if payment:
            payment.status = "rejected"
            payment.verified_at = datetime.utcnow()
            payment.verified_by_admin_id = admin_id
            payment.admin_note = admin_note
            
            db.commit()
            db.refresh(payment)
            logger.info(f"Rejected payment: {payment_id}")
        
        return payment
    
    @staticmethod
    def get_payment_methods(db: Session, is_active: bool = True) -> list:
        return db.query(PaymentMethod).filter(PaymentMethod.is_active == is_active).all()
    
    @staticmethod
    def get_user_payments(db: Session, user_id: int, status: str = None) -> list:
        query = db.query(Payment).filter(Payment.user_id == user_id)
        
        if status:
            query = query.filter(Payment.status == status)
        
        return query.all()
    
    @staticmethod
    def get_payment_stats(db: Session) -> dict:
        total_pending = db.query(func.sum(Payment.amount)).filter(
            Payment.status == "pending"
        ).scalar()
        
        total_verified = db.query(func.sum(Payment.amount)).filter(
            Payment.status == "verified"
        ).scalar()
        
        return {
            "total_pending": float(total_pending) if total_pending else 0.0,
            "total_verified": float(total_verified) if total_verified else 0.0,
            "pending_count": db.query(func.count(Payment.id)).filter(
                Payment.status == "pending"
            ).scalar()
        }
