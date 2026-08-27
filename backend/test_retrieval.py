import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from services.evidence_retrieval import EvidenceRetrievalService

load_dotenv()

async def test_search():
    db_url = os.environ.get("DATABASE_URL")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        retrieval_service = EvidenceRetrievalService(session)
        
        print("Testing Keyword Search for 'Aspirin'...")
        pack = await retrieval_service.search("Aspirin for acute coronary syndromes", limit=3)
        print(f"Returned {len(pack.retrieved_items)} items.")
        for item in pack.retrieved_items:
            print(f"- {item.source_name}: {item.title} (Score: {item.relevance_score:.4f}, Method: {item.retrieval_method})")
            print(f"  Content snippet: {item.content[:50]}...")
            print("---")
            
        print("\nTesting Semantic Search for 'heart bypass surgery' (should match CABG)...")
        pack2 = await retrieval_service.search("heart bypass surgery", limit=3)
        print(f"Returned {len(pack2.retrieved_items)} items.")
        for item in pack2.retrieved_items:
            print(f"- {item.source_name}: {item.title} (Score: {item.relevance_score:.4f}, Method: {item.retrieval_method})")
            print(f"  Content snippet: {item.content[:50]}...")
            print("---")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_search())
