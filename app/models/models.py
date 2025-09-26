from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group = relationship("Group", back_populates="members")
    penalties = relationship("Penalty", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    members = relationship("User", back_populates="group")
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
