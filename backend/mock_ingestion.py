import asyncio
import os
import json
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from services.embeddings import get_embedding_provider
from database.models import MedicalSource, KnowledgeDocument, KnowledgeChunk

load_dotenv()

async def mock_ingest():
    db_url = os.environ.get("DATABASE_URL")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    embedding_provider = get_embedding_provider()

    async with async_session() as session:
        # 1. Create a Source
        source = MedicalSource(
            name="American Heart Association",
            organization="AHA",
            source_type="guideline",
            base_url="https://www.heart.org",
            description="Guidelines and statements from the American Heart Association.",
            trust_level="high"
        )
        session.add(source)
        await session.flush()
        
        # 2. Create a Document
        doc = KnowledgeDocument(
            source_id=source.id,
            title="2021 ACC/AHA/SCAI Guideline for Coronary Artery Revascularization",
            url="https://www.ahajournals.org/doi/10.1161/CIR.0000000000001038",
            document_type="clinical_guideline",
            status="active"
        )
        session.add(doc)
        await session.flush()

        # 3. Create Chunks
        chunks_data = [
            "In patients with multivessel coronary artery disease and diabetes, CABG is generally preferred over PCI to improve survival.",
            "For patients with acute myocardial infarction, timely reperfusion therapy with primary PCI is recommended within 90 minutes of medical contact.",
            "Aspirin should be administered promptly to all patients with suspected acute coronary syndromes unless contraindicated."
        ]
        
        for i, text_content in enumerate(chunks_data):
            embedding = await embedding_provider.embed_text(text_content)
            chunk = KnowledgeChunk(
                document_id=doc.id,
                content=text_content,
                section_title="Recommendations",
                chunk_index=i,
                embedding=embedding,
                # For exact match we construct a tsvector from text using func.to_tsvector in actual DB insert, 
                # but since we defined search_vector as a column, we can let Postgres handle it if we use raw SQL or update it later.
                # A common pattern is a trigger, but for now we'll do an update right after.
            )
            session.add(chunk)
            
        await session.commit()
        
        # Update TSVECTOR
        await session.execute(text("""
            UPDATE knowledge_chunks
            SET search_vector = to_tsvector('english', content)
            WHERE search_vector IS NULL
        """))
        await session.commit()

        print("Mock ingestion complete.")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(mock_ingest())
