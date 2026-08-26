import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

def main():
    try:
        # Check if bucket exists
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        if "health_documents" not in bucket_names:
            print("Creating bucket 'health_documents'...")
            supabase.storage.create_bucket("health_documents", options={"public": False})
            print("Bucket created.")
        else:
            print("Bucket 'health_documents' already exists.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
