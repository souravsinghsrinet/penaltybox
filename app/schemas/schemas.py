from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

# User schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    group_id: Optional[int] = None
    balance: float
    created_at: datetime

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None

# Group schemas
class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    created_at: datetime
    members: List[User] = []

    class Config:
        from_attributes = True

# Rule schemas
class RuleBase(BaseModel):
    title: str
    amount: float

class RuleCreate(RuleBase):
    group_id: int

class Rule(RuleBase):
    id: int
    group_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Penalty schemas
class PenaltyBase(BaseModel):
    amount: float
    note: Optional[str] = None

class PenaltyCreate(PenaltyBase):
    user_id: int
    rule_id: int

class Penalty(PenaltyBase):
    id: int
    user_id: int
    group_id: int
    rule_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Proof schemas
class ProofBase(BaseModel):
    image_url: str

class ProofCreate(ProofBase):
    penalty_id: int

class Proof(ProofBase):
    id: int
    penalty_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Payment schemas
class PaymentBase(BaseModel):
    amount: float

class PaymentCreate(PaymentBase):
    user_id: int

class Payment(PaymentBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LeaderboardSortBy(str, Enum):
    TOTAL_PENALTIES = "total_penalties"
    TOTAL_AMOUNT = "total_amount"
    PAID_AMOUNT = "paid_amount"
    UNPAID_AMOUNT = "unpaid_amount"
