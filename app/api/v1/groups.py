from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import case
from typing import List

from app.core.database import get_db
from app.models.models import Group, User, Penalty
from app.schemas.schemas import GroupCreate, Group as GroupSchema, LeaderboardSortBy
from app.api.v1.auth import oauth2_scheme, get_current_user, get_current_admin_user

router = APIRouter()

@router.get("/", response_model=List[GroupSchema])
def get_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Any authenticated user can view groups
):
    return db.query(Group).all()

@router.post("/", response_model=GroupSchema, status_code=status.HTTP_201_CREATED)
def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can create groups
):
    db_group = Group(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.get("/{group_id}", response_model=GroupSchema)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Any authenticated user can view
):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    return db_group

@router.post("/{group_id}/members", status_code=status.HTTP_200_OK)
def add_member_to_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can add members
):
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is already in a group
    if user.group_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already in a group"
        )
    
    # Add user to group
    user.group_id = group_id
    db.commit()
    db.refresh(user)
    
    return {"message": f"User {user.name} added to group {group.name} successfully"}


@router.get("/{group_id}/leaderboard", status_code=status.HTTP_200_OK)
def get_group_leaderboard(
    group_id: int,
    sort_by: LeaderboardSortBy = Query(
        default=LeaderboardSortBy.TOTAL_PENALTIES,
        description="Field to sort the leaderboard by"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Any authenticated user can view leaderboard
):
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Get all members and their penalty data
    from sqlalchemy import func
    from sqlalchemy.sql import label
    
    # Calculate unpaid amount using a subquery for sorting
    unpaid_amount = func.coalesce(
        func.sum(Penalty.amount), 0
    ) - func.coalesce(
        func.sum(case((Penalty.status == 'PAID', Penalty.amount), else_=0)), 0
    )

    # Base query with all needed fields
    base_query = (
        db.query(
            User.id,
            User.name,
            User.email,
            label('total_penalties', func.count(Penalty.id)),
            label('total_amount', func.coalesce(func.sum(Penalty.amount), 0)),
            label('paid_amount', func.coalesce(func.sum(
                case((Penalty.status == 'PAID', Penalty.amount), else_=0)
            ), 0)),
            label('unpaid_amount', unpaid_amount)
        )
        .outerjoin(Penalty)
        .filter(User.group_id == group_id)
        .group_by(User.id)
    )

    # Apply sorting based on the sort_by parameter
    if sort_by == LeaderboardSortBy.TOTAL_PENALTIES:
        base_query = base_query.order_by(func.count(Penalty.id).desc())
    elif sort_by == LeaderboardSortBy.TOTAL_AMOUNT:
        base_query = base_query.order_by(func.coalesce(func.sum(Penalty.amount), 0).desc())
    elif sort_by == LeaderboardSortBy.PAID_AMOUNT:
        base_query = base_query.order_by(
            func.coalesce(
                func.sum(case((Penalty.status == 'PAID', Penalty.amount), else_=0)), 0
            ).desc()
        )
    elif sort_by == LeaderboardSortBy.UNPAID_AMOUNT:
        base_query = base_query.order_by(unpaid_amount.desc())

    leaderboard = base_query.all()
    
    # Format the response
    result = []
    for user in leaderboard:
        result.append({
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "total_penalties": user.total_penalties,
            "total_amount": float(user.total_amount),
            "paid_amount": float(user.paid_amount),
            "unpaid_amount": float(user.unpaid_amount)
        })
    
    return {
        "group_id": group_id,
        "group_name": group.name,
        "sort_by": sort_by,
        "leaderboard": result
    }
