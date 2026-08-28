import asyncio
from database.database import init_db, get_db, engine
from sqlalchemy import text

async def run():
    print("Running init_db...")
    await init_db()
    print("DB init complete.")
    
    # Also alter health_goals
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE health_goals ADD COLUMN IF NOT EXISTS progress FLOAT"))
            await conn.execute(text("ALTER TABLE health_goals ADD COLUMN IF NOT EXISTS start_date DATE"))
        print("Altered health_goals successfully.")
    except Exception as e:
        print("Error altering health_goals:", e)

if __name__ == "__main__":
    asyncio.run(run())
