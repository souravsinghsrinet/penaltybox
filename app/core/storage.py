"""
Storage Service - Abstraction layer for file storage
Supports local storage with easy migration to S3/cloud storage
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import shutil


class StorageService:
    """
    File storage abstraction layer.
    Configure via environment variables for future cloud migration.
    
    Environment Variables:
    - STORAGE_TYPE: 'local' or 's3' (default: local)
    - STORAGE_PATH: Base path for local storage (default: ./uploads)
    - AWS_S3_BUCKET: S3 bucket name (for future use)
    - AWS_ACCESS_KEY_ID: AWS credentials (for future use)
    - AWS_SECRET_ACCESS_KEY: AWS credentials (for future use)
    """
    
    def __init__(self):
        self.storage_type = os.getenv("STORAGE_TYPE", "local")
        self.base_path = os.getenv("STORAGE_PATH", "./uploads")
        
        # Ensure base directory exists
        if self.storage_type == "local":
            Path(self.base_path).mkdir(parents=True, exist_ok=True)
            Path(os.path.join(self.base_path, "proofs")).mkdir(parents=True, exist_ok=True)
            Path(os.path.join(self.base_path, "thumbnails")).mkdir(parents=True, exist_ok=True)
    
    async def save_file(
        self, 
        file: UploadFile, 
        folder: str = "proofs",
        custom_filename: Optional[str] = None
    ) -> str:
        """
        Save uploaded file to storage.
        
        Args:
            file: FastAPI UploadFile object
            folder: Subfolder within base path (e.g., 'proofs', 'thumbnails')
            custom_filename: Optional custom filename, otherwise generates UUID
        
        Returns:
            str: Relative file path (e.g., 'proofs/uuid.jpg')
        """
        if self.storage_type == "local":
            return await self._save_file_local(file, folder, custom_filename)
        elif self.storage_type == "s3":
            # Future implementation
            raise NotImplementedError("S3 storage not yet implemented")
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    async def _save_file_local(
        self, 
        file: UploadFile, 
        folder: str,
        custom_filename: Optional[str] = None
    ) -> str:
        """Save file to local filesystem"""
        # Generate filename
        if custom_filename:
            filename = custom_filename
        else:
            file_extension = os.path.splitext(file.filename)[1]
            filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create full path
        folder_path = os.path.join(self.base_path, folder)
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return relative path
        return os.path.join(folder, filename)
    
    def save_processed_file(
        self,
        source_path: str,
        destination_folder: str = "thumbnails",
        custom_filename: Optional[str] = None
    ) -> str:
        """
        Save a processed file (e.g., thumbnail) to storage.
        
        Args:
            source_path: Full path to source file
            destination_folder: Destination subfolder
            custom_filename: Optional custom filename
        
        Returns:
            str: Relative file path
        """
        if self.storage_type == "local":
            return self._save_processed_file_local(source_path, destination_folder, custom_filename)
        elif self.storage_type == "s3":
            raise NotImplementedError("S3 storage not yet implemented")
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def _save_processed_file_local(
        self,
        source_path: str,
        destination_folder: str,
        custom_filename: Optional[str] = None
    ) -> str:
        """Copy processed file to destination in local storage"""
        # Generate filename
        if custom_filename:
            filename = custom_filename
        else:
            filename = os.path.basename(source_path)
        
        # Create destination path
        folder_path = os.path.join(self.base_path, destination_folder)
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        destination_path = os.path.join(folder_path, filename)
        
        # Copy file
        shutil.copy2(source_path, destination_path)
        
        # Return relative path
        return os.path.join(destination_folder, filename)
    
    def delete_file(self, relative_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            relative_path: Relative file path (e.g., 'proofs/uuid.jpg')
        
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if self.storage_type == "local":
            return self._delete_file_local(relative_path)
        elif self.storage_type == "s3":
            raise NotImplementedError("S3 storage not yet implemented")
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def _delete_file_local(self, relative_path: str) -> bool:
        """Delete file from local filesystem"""
        try:
            file_path = os.path.join(self.base_path, relative_path)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {relative_path}: {str(e)}")
            return False
    
    def get_file_path(self, relative_path: str) -> str:
        """
        Get full file path for a relative path.
        
        Args:
            relative_path: Relative file path (e.g., 'proofs/uuid.jpg')
        
        Returns:
            str: Full file path
        """
        if self.storage_type == "local":
            return os.path.join(self.base_path, relative_path)
        elif self.storage_type == "s3":
            # Return S3 URL
            raise NotImplementedError("S3 storage not yet implemented")
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists in storage"""
        if self.storage_type == "local":
            file_path = os.path.join(self.base_path, relative_path)
            return os.path.exists(file_path)
        elif self.storage_type == "s3":
            raise NotImplementedError("S3 storage not yet implemented")
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")


# Global storage service instance
storage_service = StorageService()
