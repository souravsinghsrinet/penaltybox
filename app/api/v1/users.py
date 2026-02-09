from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import UserSimple, UserUpdate, PasswordChange
from app.api.v1.auth import get_current_admin_user, get_current_user
from app.core.security import verify_password, get_password_hash

router = APIRouter()

@router.get("", response_model=List[UserSimple])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all users (for adding to groups). Only admins can access."""
    users = db.query(User).all()
    return users


@router.put("/{user_id}", response_model=UserSimple)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user profile information. Users can only update their own profile."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if email is already taken by another user
    existing_user = db.query(User).filter(
        User.email == user_update.email,
        User.id != user_id
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user.name = user_update.name
    user.email = user_update.email
    
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/{user_id}/change-password")
def change_password(
    user_id: int,
    password_change: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change user password. Users can only change their own password."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to change this user's password")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_change.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    if len(password_change.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters long")
    
    # Update password
    user.hashed_password = get_password_hash(password_change.new_password)
    
    db.commit()
    
    return {"message": "Password changed successfully"}
