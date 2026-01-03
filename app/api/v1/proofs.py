from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os

from app.core.database import get_db
from app.core.file_handler import save_upload_file, remove_file
from app.models.models import Proof, Penalty, User
from app.schemas.schemas import ProofCreate, Proof as ProofSchema
from app.api.v1.auth import oauth2_scheme, get_current_user, get_current_admin_user

router = APIRouter()

@router.post("/upload/{penalty_id}", response_model=ProofSchema, status_code=status.HTTP_201_CREATED)
async def upload_proof(
    penalty_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Any authenticated user can upload proof
):
    """
    Upload a proof (screenshot) for a penalty payment
    """
    # Check if penalty exists
    penalty = db.query(Penalty).filter(Penalty.id == penalty_id).first()
    if not penalty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Penalty not found"
        )
    
    # Verify the penalty belongs to the current user (users can only upload proof for their own penalties)
    if penalty.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload proof for your own penalties"
        )
    
    # Validate file type
    allowed_types = [".jpg", ".jpeg", ".png", ".pdf"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Must be one of: {', '.join(allowed_types)}"
        )
    
    # Save the file
    try:
        file_path = save_upload_file(file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not upload file"
        )
    
    # Create proof record
    db_proof = Proof(
        penalty_id=penalty_id,
        image_url=file_path
    )
    
    db.add(db_proof)
    db.commit()
    db.refresh(db_proof)
    
    # Note: Admin will review and approve, then update status to PAID
    # Don't automatically mark as PAID on upload
    
    return db_proof

@router.get("/penalty/{penalty_id}", response_model=List[ProofSchema])
async def get_proofs_for_penalty(
    penalty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Any authenticated user can view proofs
):
    """
    Get all proofs for a specific penalty
    """
    proofs = db.query(Proof).filter(Proof.penalty_id == penalty_id).all()
    return proofs

@router.post("/{proof_id}/approve", status_code=status.HTTP_200_OK)
async def approve_proof(
    proof_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can approve proofs
):
    """
    Approve a proof and mark the penalty as PAID
    """
    proof = db.query(Proof).filter(Proof.id == proof_id).first()
    if not proof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proof not found"
        )
    
    # Update penalty status to PAID
    penalty = db.query(Penalty).filter(Penalty.id == proof.penalty_id).first()
    if penalty:
        penalty.status = "PAID"
        db.commit()
    
    return {"message": "Proof approved and penalty marked as PAID"}

@router.delete("/{proof_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proof(
    proof_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can delete proofs
):
    """
    Delete a proof and its associated file
    """
    proof = db.query(Proof).filter(Proof.id == proof_id).first()
    if not proof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proof not found"
        )
    
    # Remove the file
    if proof.image_url:
        remove_file(proof.image_url)
    
    # Delete the database record
    db.delete(proof)
    db.commit()
    
    return None
