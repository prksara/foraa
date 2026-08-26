import os
import uuid
from typing import Optional
from supabase import create_client, Client

class StorageService:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.client: Client = create_client(url, key)
        self.bucket = "health_documents"

    def upload_document(self, user_id: str, filename: str, file_bytes: bytes, mime_type: str) -> str:
        """
        Uploads a file to Supabase Storage in the private bucket, namespaced by user_id.
        Returns the storage path.
        """
        # Create a unique path to avoid collisions
        unique_id = str(uuid.uuid4())
        path = f"{user_id}/{unique_id}_{filename}"
        
        # Upload
        res = self.client.storage.from_(self.bucket).upload(
            path, 
            file_bytes, 
            file_options={"content-type": mime_type}
        )
        return path

    def delete_document(self, storage_path: str):
        """
        Deletes a file from Supabase Storage.
        """
        self.client.storage.from_(self.bucket).remove([storage_path])

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Gets a signed URL for a private document to allow the frontend to download it.
        """
        try:
            res = self.client.storage.from_(self.bucket).create_signed_url(storage_path, expires_in)
            return res.get("signedURL")
        except Exception as e:
            print(f"Error getting signed url: {e}")
            return None
    
    def download_document(self, storage_path: str) -> bytes:
        """
        Downloads a file's bytes from Supabase Storage.
        """
        res = self.client.storage.from_(self.bucket).download(storage_path)
        return res

storage_service = StorageService()
