from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import datetime

from app.core.database import get_db
from app.core.storage import storage_service
from app.core.background_tasks import task_service
from app.models.models import Proof, Penalty, User, Rule, Group
from app.schemas.schemas import ProofCreate, Proof as ProofSchema, ProofReview
from app.api.v1.auth import oauth2_scheme, get_current_user, get_current_admin_user

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_proofs(
    status_filter: Optional[str] = None,  # PENDING, APPROVED, DECLINED
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can view all proofs
):
    """
    Get all proofs with enriched data (user, penalty, rule, group).
    Optionally filter by status.
    """
    query = db.query(Proof).join(Penalty).join(User).join(Rule).join(Group)
    
    if status_filter:
        query = query.filter(Proof.status == status_filter.upper())
    
    proofs = query.all()
    
    # Enrich with user, penalty, rule, and group data
    enriched_proofs = []
    for proof in proofs:
        penalty = proof.penalty
        user = penalty.user
        rule = penalty.rule
        group = penalty.group
        
        enriched_proofs.append({
            "id": proof.id,
            "penalty_id": proof.penalty_id,
            "image_url": proof.image_url,
            "created_at": proof.created_at,
            "status": proof.status,
            "reviewed_by": proof.reviewed_by,
            "reviewed_at": proof.reviewed_at,
            "admin_note": proof.admin_note,
            # User info
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            },
            # Penalty info
            "penalty": {
                "id": penalty.id,
                "amount": penalty.amount,
                "note": penalty.note,
                "created_at": penalty.created_at,
                "status": penalty.status
            },
            # Rule info
            "rule": {
                "id": rule.id,
                "title": rule.title,
                "penalty_amount": rule.amount
            },
            # Group info
            "group": {
                "id": group.id,
                "name": group.name
            }
        })
    
    return enriched_proofs

@router.post("/upload/{penalty_id}", response_model=ProofSchema, status_code=status.HTTP_201_CREATED)
async def upload_proof(
    penalty_id: int,
    file: UploadFile = File(...),
    reference: Optional[str] = Form(None),  # Optional reference/note (e.g., UPI transaction ID)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a payment proof (screenshot) for a penalty.
    
    Process:
    1. Validates file type (jpg, png only)
    2. Saves original file to server
    3. Creates proof record in database
    4. Triggers background task to:
       - Convert image to 100x100 PNG thumbnail
       - Delete original file
       - Update proof record with thumbnail path
    
    Args:
        penalty_id: ID of the penalty
        file: Image file (jpg or png)
        reference: Optional reference/note (e.g., UPI transaction ID)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Proof: Created proof record
    """
    # Check if penalty exists
    penalty = db.query(Penalty).filter(Penalty.id == penalty_id).first()
    if not penalty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Penalty not found"
        )
    
    # Verify the penalty belongs to the current user
    if penalty.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload proof for your own penalties"
        )
    
    # Validate file type (only jpg and png for image processing)
    allowed_types = [".jpg", ".jpeg", ".png"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Only JPG and PNG images are supported."
        )
    
    # Save the original file
    try:
        file_path = await storage_service.save_file(file, folder="proofs")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not upload file: {str(e)}"
        )
    
    # Create proof record (image_url will be updated after background processing)
    db_proof = Proof(
        penalty_id=penalty_id,
        image_url=file_path  # Initially points to original, will be updated to thumbnail
    )
    
    db.add(db_proof)
    db.commit()
    db.refresh(db_proof)
    
    # Trigger background task for image processing
    try:
        success, thumbnail_path, error = task_service.process_image_to_thumbnail(
            db=db,
            proof_id=db_proof.id,
            original_path=file_path
            # size is now read from .env (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
        )
        
        if not success:
            # Log error but don't fail the upload
            print(f"Background processing failed for proof {db_proof.id}: {error}")
    except Exception as e:
        # Log error but don't fail the upload
        print(f"Background task failed for proof {db_proof.id}: {str(e)}")
    
    # Refresh to get updated image_url (thumbnail path)
    db.refresh(db_proof)
    
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
    review_data: ProofReview,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can approve proofs
):
    """
    Approve a proof and mark the penalty as PAID.
    Admin can optionally add a note.
    """
    proof = db.query(Proof).filter(Proof.id == proof_id).first()
    if not proof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proof not found"
        )
    
    # Update proof status
    proof.status = "APPROVED"
    proof.reviewed_by = current_admin.id
    proof.reviewed_at = datetime.utcnow()
    proof.admin_note = review_data.admin_note
    
    # Update penalty status to PAID
    penalty = db.query(Penalty).filter(Penalty.id == proof.penalty_id).first()
    if penalty:
        penalty.status = "PAID"
    
    db.commit()
    
    return {"message": "Proof approved and penalty marked as PAID", "proof_id": proof.id}

@router.post("/{proof_id}/decline", status_code=status.HTTP_200_OK)
async def decline_proof(
    proof_id: int,
    review_data: ProofReview,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Only admins can decline proofs
):
    """
    Decline a proof with an optional admin note explaining the reason.
    The penalty remains UNPAID.
    """
    proof = db.query(Proof).filter(Proof.id == proof_id).first()
    if not proof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proof not found"
        )
    
    # Update proof status
    proof.status = "DECLINED"
    proof.reviewed_by = current_admin.id
    proof.reviewed_at = datetime.utcnow()
    proof.admin_note = review_data.admin_note
    
    db.commit()
    
    return {"message": "Proof declined", "proof_id": proof.id}

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
    
    # Remove the file using storage service
    if proof.image_url:
        storage_service.delete_file(proof.image_url)
    
    # Delete the database record
    db.delete(proof)
    db.commit()
    
    return None
