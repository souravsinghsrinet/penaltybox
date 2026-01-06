from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Table, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base

# Enum for background task status
class TaskStatus(str, enum.Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# Association table for many-to-many relationship between users and groups
user_groups = Table(
    'user_groups',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('role', String, default='member'),  # 'admin' or 'member'
    Column('joined_at', DateTime, default=datetime.utcnow)
)

# Association table for many-to-many relationship between penalties and payments
# Allows one payment to cover multiple penalties (bulk payment)
# and one penalty to be split across multiple payments
penalty_payments = Table(
    'penalty_payments',
    Base.metadata,
    Column('penalty_id', Integer, ForeignKey('penalties.id'), primary_key=True),
    Column('payment_id', Integer, ForeignKey('payments.id'), primary_key=True),
    Column('amount', Float),  # Amount of this payment allocated to this specific penalty
    Column('created_at', DateTime, default=datetime.utcnow)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)  # Global admin flag for app-level permissions
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    groups = relationship("Group", secondary=user_groups, back_populates="members")
    penalties = relationship("Penalty", back_populates="user")
    # Payment relationship defined in Payment model with explicit foreign_keys

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)  # Added description field
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    members = relationship("User", secondary=user_groups, back_populates="groups")
    penalties = relationship("Penalty", back_populates="group")
    rules = relationship("Rule", back_populates="group")

class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    title = Column(String, index=True)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group = relationship("Group", back_populates="rules")
    penalties = relationship("Penalty", back_populates="rule")

class Penalty(Base):
    __tablename__ = "penalties"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    rule_id = Column(Integer, ForeignKey("rules.id"))
    amount = Column(Float)
    note = Column(String, nullable=True)
    status = Column(String, default="UNPAID")  # UNPAID, PAID
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="penalties")
    group = relationship("Group", back_populates="penalties")
    rule = relationship("Rule", back_populates="penalties")
    proofs = relationship("Proof", back_populates="penalty")
    payments = relationship("Payment", secondary=penalty_payments, back_populates="penalties")

class Proof(Base):
    __tablename__ = "proofs"

    id = Column(Integer, primary_key=True, index=True)
    penalty_id = Column(Integer, ForeignKey("penalties.id"))
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    penalty = relationship("Penalty", back_populates="proofs")
    background_tasks = relationship("BackgroundTask", back_populates="proof")

class BackgroundTask(Base):
    __tablename__ = "background_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, nullable=False, index=True)
    task_type = Column(String, nullable=False)  # 'image_processing', 'cleanup', etc.
    proof_id = Column(Integer, ForeignKey("proofs.id"), nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.STARTED)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    task_metadata = Column(JSON, nullable=True)  # Additional task-specific data (renamed from 'metadata')

    # Relationships
    proof = relationship("Proof", back_populates="background_tasks")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)  # Total payment amount
    payment_method = Column(String, default="CASH")  # CASH, UPI, BANK_TRANSFER, etc.
    reference_id = Column(String, nullable=True)  # Transaction ID for online payments
    approved_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who approved (for cash)
    notes = Column(String, nullable=True)  # Admin notes about the payment
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_admin_id])
    penalties = relationship("Penalty", secondary=penalty_payments, back_populates="payments")
