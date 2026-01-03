from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import Rule, Group
from app.schemas.schemas import RuleCreate, Rule as RuleSchema
from app.api.v1.auth import oauth2_scheme

router = APIRouter()

@router.post("/{group_id}/rules", response_model=RuleSchema, status_code=status.HTTP_201_CREATED)
def create_rule(
    group_id: int,
    rule: RuleCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
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
    token: str = Depends(oauth2_scheme)
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

@router.delete("/{group_id}/rules/{rule_id}", status_code=status.HTTP_200_OK)
def delete_rule(
    group_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
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
