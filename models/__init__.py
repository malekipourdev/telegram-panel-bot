from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Enum, JSON, LargeBinary, Text, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BIGINT, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    is_admin = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True)
    referrer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    balance = Column(Numeric(10, 2), default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    referral_link = relationship("ReferralLink", uselist=False, back_populates="user")
    clients = relationship("Client", back_populates="user")
    payments = relationship("Payment", back_populates="user", foreign_keys="Payment.user_id")
    referrals = relationship("ReferralReward", back_populates="referrer", foreign_keys="ReferralReward.referrer_user_id")


class ReferralLink(Base):
    __tablename__ = "referral_links"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    invite_code = Column(String(50), unique=True, nullable=False, index=True)
    click_count = Column(Integer, default=0)
    referral_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="referral_link")


class ReferralReward(Base):
    __tablename__ = "referral_rewards"

    id = Column(Integer, primary_key=True)
    referrer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reward_amount = Column(Numeric(10, 2), nullable=False)
    is_claimed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    claimed_at = Column(DateTime, nullable=True)

    referrer = relationship("User", back_populates="referrals", foreign_keys=[referrer_user_id])

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # === ADD THIS NEW FIELD ===
    subscription_id = Column(Integer, ForeignKey("user_service_subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    email = Column(String(255), nullable=False, index=True)
    uuid = Column(String(36), unique=True, nullable=False)
    inbound_id = Column(Integer, nullable=False)
    status = Column(String(50), default="active", index=True)
    total_gb = Column(BIGINT, nullable=False)
    used_gb = Column(BIGINT, default=0)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="clients")
    
    # === ADD THIS NEW RELATIONSHIP ===
    subscription = relationship("UserServiceSubscription", back_populates="clients")

class PaymentStatusEnum(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REFUNDED = "refunded"


class PaymentTypeEnum(enum.Enum):
    BALANCE_INCREASE = "balance_increase"
    SERVICE_PURCHASE = "service_purchase"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="pending", index=True)
    payment_type = Column(String(50), default="balance_increase", index=True)
    related_client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    receipt_image_url = Column(String(500), nullable=True)
    bank_card_number = Column(String(20), nullable=True)
    bank_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", back_populates="payments", foreign_keys=[user_id])


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    card_number = Column(String(20), nullable=False)
    card_holder_name = Column(String(255), nullable=False)
    bank_name = Column(String(100), nullable=False)
    amount_per_payment = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ServicePackage(Base):
    __tablename__ = "service_packages"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    gb_amount = Column(BIGINT, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserServiceSubscription(Base):
    __tablename__ = "user_service_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_package_id = Column(Integer, ForeignKey("service_packages.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(50), default="active", index=True)
    expiry_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # === ADD THIS NEW RELATIONSHIP ===
    clients = relationship("Client", back_populates="subscription")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="open", index=True)
    assigned_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=True)
    changes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
