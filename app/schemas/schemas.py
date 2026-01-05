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

class UserSimple(BaseModel):
    """Simple user info without circular references"""
    id: int
    name: str
    email: EmailStr
    is_admin: bool

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    is_admin: bool
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
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class GroupMember(BaseModel):
    """Member info with their role in the group"""
    id: int
    name: str
    email: EmailStr
    role: str  # 'admin' or 'member'
    joined_at: datetime

    class Config:
        from_attributes = True

class GroupSimple(GroupBase):
    """Simple group info without members list"""
    id: int
    created_at: datetime
    member_count: int = 0
    admin_count: int = 0

    class Config:
        from_attributes = True

class Group(GroupBase):
    """Full group info with members"""
    id: int
    created_at: datetime
    members: List[GroupMember] = []

    class Config:
        from_attributes = True

class AddMemberRequest(BaseModel):
    user_id: int
    role: str = "member"  # 'admin' or 'member'

class RemoveMemberRequest(BaseModel):
    user_id: int

# Rule schemas
class RuleBase(BaseModel):
    title: str
    amount: float

class RuleCreate(RuleBase):
    pass

class RuleUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None

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
