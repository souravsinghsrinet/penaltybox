"""
Background Task Service for Image Processing
Handles async tasks like image compression, thumbnail generation, cleanup
"""
import os
import uuid
from datetime import datetime
from PIL import Image
from typing import Optional
from sqlalchemy.orm import Session

from app.models.models import BackgroundTask, TaskStatus, Proof
from app.core.storage import storage_service


class BackgroundTaskService:
    """Service for managing background tasks with logging"""
    
    @staticmethod
    def create_task(
        db: Session,
        task_type: str,
        proof_id: Optional[int] = None,
        task_metadata: Optional[dict] = None
    ) -> BackgroundTask:
        """
        Create a new background task record.
        
        Args:
            db: Database session
            task_type: Type of task (e.g., 'image_processing', 'cleanup')
            proof_id: Associated proof ID (optional)
            task_metadata: Additional task metadata (optional)
        
        Returns:
            BackgroundTask: Created task record
        """
        task = BackgroundTask(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            proof_id=proof_id,
            status=TaskStatus.STARTED,
            started_at=datetime.utcnow(),
            task_metadata=task_metadata or {}
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def complete_task(
        db: Session,
        task_id: str,
        error: Optional[str] = None
    ) -> BackgroundTask:
        """
        Mark task as completed or failed.
        
        Args:
            db: Database session
            task_id: Task UUID
            error: Error message if failed (optional)
        
        Returns:
            BackgroundTask: Updated task record
        """
        task = db.query(BackgroundTask).filter(BackgroundTask.task_id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED if error else TaskStatus.COMPLETED
            task.error = error
            task.ended_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def process_image_to_thumbnail(
        db: Session,
        proof_id: int,
        original_path: str,
        size: tuple = None
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Process uploaded image: convert to PNG thumbnail and delete original.
        
        Args:
            db: Database session
            proof_id: Proof record ID
            original_path: Relative path to original uploaded file
            size: Thumbnail dimensions (default: from .env THUMBNAIL_WIDTH/HEIGHT)
        
        Returns:
            tuple: (success: bool, thumbnail_path: str, error: str)
        """
        # Get thumbnail dimensions from environment variables
        if size is None:
            thumbnail_width = int(os.getenv('THUMBNAIL_WIDTH', '100'))
            thumbnail_height = int(os.getenv('THUMBNAIL_HEIGHT', '100'))
            size = (thumbnail_width, thumbnail_height)
        
        task = None
        try:
            # Create background task record
            task = BackgroundTaskService.create_task(
                db=db,
                task_type="image_processing",
                proof_id=proof_id,
                task_metadata={
                    "original_path": original_path,
                    "target_size": f"{size[0]}x{size[1]}"
                }
            )
            
            # Get full path to original file
            full_path = storage_service.get_file_path(original_path)
            
            # Open and process image
            with Image.open(full_path) as img:
                # Convert to RGB (in case of RGBA, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail (maintains aspect ratio within bounds)
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Generate thumbnail filename
                thumbnail_filename = f"{uuid.uuid4()}.png"
                thumbnail_temp_path = f"/tmp/{thumbnail_filename}"
                
                # Save as PNG
                img.save(thumbnail_temp_path, 'PNG', optimize=True)
            
            # Move thumbnail to storage
            thumbnail_path = storage_service.save_processed_file(
                source_path=thumbnail_temp_path,
                destination_folder="thumbnails",
                custom_filename=thumbnail_filename
            )
            
            # Clean up temp file
            if os.path.exists(thumbnail_temp_path):
                os.remove(thumbnail_temp_path)
            
            # Update proof record with new thumbnail path
            proof = db.query(Proof).filter(Proof.id == proof_id).first()
            if proof:
                # Delete original file
                storage_service.delete_file(original_path)
                
                # Update proof with thumbnail path
                proof.image_url = thumbnail_path
                db.commit()
            
            # Mark task as completed
            BackgroundTaskService.complete_task(db, task.task_id)
            
            return True, thumbnail_path, None
            
        except Exception as e:
            error_msg = f"Image processing failed: {str(e)}"
            
            # Mark task as failed
            if task:
                BackgroundTaskService.complete_task(db, task.task_id, error=error_msg)
            
            return False, None, error_msg


# Global task service instance
task_service = BackgroundTaskService()
