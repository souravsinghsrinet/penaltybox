from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import Penalty, User, Group
from app.schemas.schemas import PenaltyCreate, Penalty as PenaltySchema
from app.api.v1.auth import oauth2_scheme, get_current_user, get_current_admin_user

router = APIRouter()

@router.post("/", response_model=PenaltySchema, status_code=status.HTTP_201_CREATED)
def create_penalty(
    penalty: PenaltyCreate,
    group_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can create penalties
):
    # Verify user exists and belongs to the group
    user = db.query(User).filter(User.id == penalty.user_id).first()
    if not user or user.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id or user not in group"
        )
    
    db_penalty = Penalty(
        **penalty.dict(),
        group_id=group_id,
        status="UNPAID"
    )
    db.add(db_penalty)
    db.commit()
    db.refresh(db_penalty)
    return db_penalty

@router.get("/user/{user_id}", response_model=List[PenaltySchema])
def get_user_penalties(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Any authenticated user can view
):
    penalties = db.query(Penalty).filter(Penalty.user_id == user_id).all()
    return penalties

@router.put("/{penalty_id}/status")
def update_penalty_status(
    penalty_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can update status
):
    penalty = db.query(Penalty).filter(Penalty.id == penalty_id).first()
    if not penalty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Penalty not found"
        )
    
    if status not in ["PAID", "UNPAID"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be either PAID or UNPAID"
        )
    
    penalty.status = status
    db.commit()
    return {"status": "success", "message": f"Penalty status updated to {status}"}
