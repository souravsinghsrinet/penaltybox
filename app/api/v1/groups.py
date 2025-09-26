from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import Group, User
from app.schemas.schemas import GroupCreate, Group as GroupSchema
from app.api.v1.auth import oauth2_scheme

router = APIRouter()

@router.get("/", response_model=List[GroupSchema])
def get_groups(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    return db.query(Group).all()

@router.post("/", response_model=GroupSchema, status_code=status.HTTP_201_CREATED)
def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
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
    token: str = Depends(oauth2_scheme)
):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    return db_group
