from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import UserSimple
from app.api.v1.auth import get_current_admin_user

router = APIRouter()

@router.get("/", response_model=List[UserSimple])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all users (for adding to groups). Only admins can access."""
    users = db.query(User).all()
    return users
