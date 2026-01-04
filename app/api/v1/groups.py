from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import case, func, and_
from typing import List

from app.core.database import get_db
from app.models.models import Group, User, Penalty, user_groups
from app.schemas.schemas import (
    GroupCreate, Group as GroupSchema, GroupSimple, GroupMember,
    AddMemberRequest, RemoveMemberRequest, LeaderboardSortBy
)
from app.api.v1.auth import oauth2_scheme, get_current_user, get_current_admin_user
from datetime import datetime

router = APIRouter()

def is_group_admin(db: Session, user_id: int, group_id: int) -> bool:
    """Check if user is an admin of the specified group"""
    result = db.execute(
        user_groups.select().where(
            and_(
                user_groups.c.user_id == user_id,
                user_groups.c.group_id == group_id,
                user_groups.c.role == 'admin'
            )
        )
    ).first()
    return result is not None

def get_user_role_in_group(db: Session, user_id: int, group_id: int) -> str:
    """Get user's role in a specific group"""
    result = db.execute(
        user_groups.select().where(
            and_(
                user_groups.c.user_id == user_id,
                user_groups.c.group_id == group_id
            )
        )
    ).first()
    return result.role if result else None

@router.get("/", response_model=List[GroupSimple])
def get_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all groups that the current user is a member of"""
    # Get groups where user is a member
    user_group_ids = db.execute(
        user_groups.select().where(user_groups.c.user_id == current_user.id)
    ).fetchall()
    
    group_ids = [ug.group_id for ug in user_group_ids]
    
    if not group_ids:
        return []
    
    groups = db.query(Group).filter(Group.id.in_(group_ids)).all()
    
    # Add member and admin counts
    result = []
    for group in groups:
        # Count total members
        member_count = db.execute(
            user_groups.select().where(user_groups.c.group_id == group.id)
        ).fetchall()
        
        # Count admins
        admin_count = db.execute(
            user_groups.select().where(
                and_(
                    user_groups.c.group_id == group.id,
                    user_groups.c.role == 'admin'
                )
            )
        ).fetchall()
        
        result.append(GroupSimple(
            id=group.id,
            name=group.name,
            description=group.description,
            created_at=group.created_at,
            member_count=len(member_count),
            admin_count=len(admin_count)
        ))
    
    return result

@router.post("/", response_model=GroupSchema, status_code=status.HTTP_201_CREATED)
def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Create a new group. Only global admins can create groups. Creator is automatically added as group admin."""
    # Create the group
    db_group = Group(name=group.name, description=group.description)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    # Add creator as admin
    db.execute(
        user_groups.insert().values(
            user_id=current_admin.id,
            group_id=db_group.id,
            role='admin',
            joined_at=datetime.utcnow()
        )
    )
    db.commit()
    
    # Return group with members
    return get_group(db_group.id, db, current_admin)

@router.get("/{group_id}", response_model=GroupSchema)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get group details with all members"""
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if user is a member of this group
    user_role = get_user_role_in_group(db, current_user.id, group_id)
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    # Get all members with their roles
    members_data = db.execute(
        user_groups.select().where(user_groups.c.group_id == group_id)
    ).fetchall()
    
    members = []
    for member_data in members_data:
        user = db.query(User).filter(User.id == member_data.user_id).first()
        if user:
            members.append(GroupMember(
                id=user.id,
                name=user.name,
                email=user.email,
                role=member_data.role,
                joined_at=member_data.joined_at
            ))
    
    return GroupSchema(
        id=db_group.id,
        name=db_group.name,
        description=db_group.description,
        created_at=db_group.created_at,
        members=members
    )

@router.post("/{group_id}/members", status_code=status.HTTP_200_OK)
def add_member_to_group(
    group_id: int,
    request: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a member to group. Only group admins can add members."""
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if current user is admin of this group
    if not is_group_admin(db, current_user.id, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can add members"
        )
    
    # Check if user to add exists
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is already in the group
    existing = db.execute(
        user_groups.select().where(
            and_(
                user_groups.c.user_id == request.user_id,
                user_groups.c.group_id == group_id
            )
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group"
        )
    
    # Validate role
    if request.role not in ['admin', 'member']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'member'"
        )
    
    # Add user to group
    db.execute(
        user_groups.insert().values(
            user_id=request.user_id,
            group_id=group_id,
            role=request.role,
            joined_at=datetime.utcnow()
        )
    )
    db.commit()
    
    return {
        "message": f"User {user.name} added to group {group.name} as {request.role}",
        "user_id": user.id,
        "group_id": group_id,
        "role": request.role
    }

@router.delete("/{group_id}/members", status_code=status.HTTP_200_OK)
def remove_member_from_group(
    group_id: int,
    request: RemoveMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from group. Only group admins can remove members."""
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if current user is admin of this group
    if not is_group_admin(db, current_user.id, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can remove members"
        )
    
    # Check if user to remove exists in group
    member = db.execute(
        user_groups.select().where(
            and_(
                user_groups.c.user_id == request.user_id,
                user_groups.c.group_id == group_id
            )
        )
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this group"
        )
    
    # Prevent removing the last admin
    admin_count = db.execute(
        user_groups.select().where(
            and_(
                user_groups.c.group_id == group_id,
                user_groups.c.role == 'admin'
            )
        )
    ).fetchall()
    
    if member.role == 'admin' and len(admin_count) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last admin from the group"
        )
    
    # Remove user from group
    db.execute(
        user_groups.delete().where(
            and_(
                user_groups.c.user_id == request.user_id,
                user_groups.c.group_id == group_id
            )
        )
    )
    db.commit()
    
    user = db.query(User).filter(User.id == request.user_id).first()
    return {
        "message": f"User {user.name if user else request.user_id} removed from group {group.name}",
        "user_id": request.user_id,
        "group_id": group_id
    }


@router.get("/{group_id}/leaderboard", status_code=status.HTTP_200_OK)
def get_group_leaderboard(
    group_id: int,
    sort_by: LeaderboardSortBy = Query(
        default=LeaderboardSortBy.TOTAL_PENALTIES,
        description="Field to sort the leaderboard by"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get leaderboard for a group. Only group members can view."""
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if user is a member of this group
    user_role = get_user_role_in_group(db, current_user.id, group_id)
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    # Get all members of the group
    members_data = db.execute(
        user_groups.select().where(user_groups.c.group_id == group_id)
    ).fetchall()
    
    member_ids = [m.user_id for m in members_data]
    
    # Calculate unpaid amount using a subquery for sorting
    unpaid_amount = func.coalesce(
        func.sum(Penalty.amount), 0
    ) - func.coalesce(
        func.sum(case((Penalty.status == 'PAID', Penalty.amount), else_=0)), 0
    )

    # Base query with all needed fields
    from sqlalchemy.sql import label
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
        .outerjoin(Penalty, and_(Penalty.user_id == User.id, Penalty.group_id == group_id))
        .filter(User.id.in_(member_ids))
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
