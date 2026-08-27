import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

async def check_pgvector():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return
    
    # Handle the plus syntax we used for sqlalchemy
    if "postgresql+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql")

    try:
        conn = await asyncpg.connect(db_url)
        # Try to enable pgvector extension
        await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        
        # Check if it was created
        row = await conn.fetchrow("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        if row:
            print("SUCCESS: pgvector is available and installed.")
        else:
            print("FAILURE: pgvector not found in pg_extension.")
            
        await conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_pgvector())
