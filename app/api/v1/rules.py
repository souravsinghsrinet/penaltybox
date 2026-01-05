from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import Rule, Group, User
from app.schemas.schemas import RuleCreate, RuleUpdate, Rule as RuleSchema
from app.api.v1.auth import oauth2_scheme, get_current_user, get_current_admin_user

router = APIRouter()

@router.post("/{group_id}/rules", response_model=RuleSchema, status_code=status.HTTP_201_CREATED)
def create_rule(
    group_id: int,
    rule: RuleCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can create rules
):
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Create new rule
    db_rule = Rule(
        group_id=group_id,
        title=rule.title,
        amount=rule.amount
    )
    
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.get("/{group_id}/rules", response_model=List[RuleSchema])
def get_group_rules(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Any authenticated user can view rules
):
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Get all rules for the group
    rules = db.query(Rule).filter(Rule.group_id == group_id).all()
    return rules

@router.put("/{group_id}/rules/{rule_id}", response_model=RuleSchema)
def update_rule(
    group_id: int,
    rule_id: int,
    rule_update: RuleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can update rules
):
    # Check if rule exists and belongs to the group
    rule = db.query(Rule).filter(Rule.id == rule_id, Rule.group_id == group_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found or doesn't belong to the specified group"
        )
    
    # Update rule fields if provided
    if rule_update.title is not None:
        rule.title = rule_update.title
    if rule_update.amount is not None:
        rule.amount = rule_update.amount
    
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/{group_id}/rules/{rule_id}", status_code=status.HTTP_200_OK)
def delete_rule(
    group_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can delete rules
):
    # Check if rule exists and belongs to the group
    rule = db.query(Rule).filter(Rule.id == rule_id, Rule.group_id == group_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found or doesn't belong to the specified group"
        )
    
    db.delete(rule)
    db.commit()
    return {"message": f"Rule '{rule.title}' deleted successfully"}
