from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.models import Penalty, User, Group, Rule, Payment, penalty_payments
from app.schemas.schemas import PenaltyCreate, Penalty as PenaltySchema
from app.api.v1.auth import oauth2_scheme, get_current_user, get_current_admin_user

router = APIRouter()

@router.post("", response_model=PenaltySchema, status_code=status.HTTP_201_CREATED)
def create_penalty(
    penalty: PenaltyCreate,
    group_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can create penalties
):
    # Verify group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Verify user exists and belongs to the group (many-to-many relationship)
    user = db.query(User).filter(User.id == penalty.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is a member of the group
    if group not in user.groups:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this group"
        )
    
    # Verify rule exists and belongs to the group
    rule = db.query(Rule).filter(Rule.id == penalty.rule_id, Rule.group_id == group_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found in this group"
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

@router.get("", response_model=List[PenaltySchema])
def get_penalties(
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get penalties with optional group_id filter
    Includes user name and rule title
    Sorted by created_at in descending order (newest first)
    """
    from app.models.models import Rule
    
    query = db.query(Penalty)
    
    if group_id is not None:
        query = query.filter(Penalty.group_id == group_id)
    
    # Sort by created_at in descending order (newest first)
    penalties = query.order_by(Penalty.created_at.desc()).all()
    
    # Enrich penalties with user names and rule titles
    result = []
    for penalty in penalties:
        penalty_dict = {
            "id": penalty.id,
            "user_id": penalty.user_id,
            "group_id": penalty.group_id,
            "rule_id": penalty.rule_id,
            "amount": penalty.amount,
            "note": penalty.note,
            "status": penalty.status,
            "created_at": penalty.created_at,
            "user_name": None,
            "rule_title": None
        }
        
        # Get user name
        user = db.query(User).filter(User.id == penalty.user_id).first()
        if user:
            penalty_dict["user_name"] = user.name
        
        # Get rule title
        rule = db.query(Rule).filter(Rule.id == penalty.rule_id).first()
        if rule:
            penalty_dict["rule_title"] = rule.title
        
        result.append(penalty_dict)
    
    return result

@router.get("/user/{user_id}", response_model=List[PenaltySchema])
def get_user_penalties(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Any authenticated user can view
):
    """
    Get penalties for a specific user
    Includes user name and rule title
    Sorted by created_at in descending order (newest first)
    """
    from app.models.models import Rule
    
    penalties = db.query(Penalty).filter(Penalty.user_id == user_id).order_by(Penalty.created_at.desc()).all()
    
    # Enrich penalties with user names and rule titles
    result = []
    for penalty in penalties:
        penalty_dict = {
            "id": penalty.id,
            "user_id": penalty.user_id,
            "group_id": penalty.group_id,
            "rule_id": penalty.rule_id,
            "amount": penalty.amount,
            "note": penalty.note,
            "status": penalty.status,
            "created_at": penalty.created_at,
            "user_name": None,
            "rule_title": None
        }
        
        # Get user name
        user = db.query(User).filter(User.id == penalty.user_id).first()
        if user:
            penalty_dict["user_name"] = user.name
        
        # Get rule title
        rule = db.query(Rule).filter(Rule.id == penalty.rule_id).first()
        if rule:
            penalty_dict["rule_title"] = rule.title
        
        result.append(penalty_dict)
    
    return result

@router.put("/{penalty_id}/status")
def update_penalty_status(
    penalty_id: int,
    status: str,
    admin_note: Optional[str] = Query(None, description="Optional note from admin about the payment"),
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
    
    old_status = penalty.status
    penalty.status = status
    
    # If marking as PAID, create a payment record (for cash payments)
    if status == "PAID" and old_status != "PAID":
        # Create payment record
        payment = Payment(
            user_id=penalty.user_id,
            amount=penalty.amount,
            payment_method="CASH",
            approved_by_admin_id=current_admin.id,
            notes=admin_note or f"Cash payment for penalty #{penalty.id}"
        )
        db.add(payment)
        db.flush()  # Get the payment ID
        
        # Link payment to penalty via junction table
        penalty_payment_stmt = penalty_payments.insert().values(
            penalty_id=penalty.id,
            payment_id=payment.id,
            amount=penalty.amount,
        )
        db.execute(penalty_payment_stmt)
    
    db.commit()
    
    if status == "PAID" and old_status != "PAID":
        return {
            "status": "success",
            "message": f"Penalty status updated to {status}. Payment record created."
        }
    else:
        return {
            "status": "success",
            "message": f"Penalty status updated to {status}"
        }
