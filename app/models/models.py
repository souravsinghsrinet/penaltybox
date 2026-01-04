from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

# Association table for many-to-many relationship between users and groups
user_groups = Table(
    'user_groups',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('role', String, default='member'),  # 'admin' or 'member'
    Column('joined_at', DateTime, default=datetime.utcnow)
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
    payments = relationship("Payment", back_populates="user")

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

class Proof(Base):
    __tablename__ = "proofs"

    id = Column(Integer, primary_key=True, index=True)
    penalty_id = Column(Integer, ForeignKey("penalties.id"))
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    penalty = relationship("Penalty", back_populates="proofs")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="payments")
