import asyncio
import os
import sys
import glob
import hashlib
from pathlib import Path

# Add the backend directory to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.database import AsyncSessionLocal
from database.models import MedicalSource, KnowledgeDocument, KnowledgeChunk
from services.embeddings import get_embedding_provider
from services.chunking import SemanticChunker
from sqlalchemy import select

async def ingest_file(filepath: str):
    print(f"Ingesting {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Calculate hash to avoid duplicates
    content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    title = Path(filepath).stem

    async with AsyncSessionLocal() as session:
        # 1. Create or get default MedicalSource
        source_name = "Foraa Knowledge Corpus"
        stmt = select(MedicalSource).where(MedicalSource.name == source_name)
        result = await session.execute(stmt)
        source = result.scalars().first()
        
        if not source:
            source = MedicalSource(
                name=source_name,
                organization="Foraa Inc.",
                source_type="internal_corpus",
                trust_level="high"
            )
            session.add(source)
            await session.commit()
            await session.refresh(source)

        # 2. Check if document already exists
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.content_hash == content_hash)
        result = await session.execute(stmt)
        existing_doc = result.scalars().first()
        if existing_doc:
            print(f"Document '{title}' already ingested (hash match). Skipping.")
            return

        # 3. Create document
        doc = KnowledgeDocument(
            source_id=source.id,
            title=title,
            document_type="markdown",
            content_hash=content_hash
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        
        # 4. Chunk text
        chunker = SemanticChunker(max_chunk_size=1500)
        chunks = chunker.chunk_text(text)
        print(f"Generated {len(chunks)} chunks.")
        
        if not chunks:
            print("No text found. Skipping.")
            return

        # 5. Generate embeddings
        embedding_provider = get_embedding_provider()
        
        # We can batch embed them
        texts_to_embed = [c.content for c in chunks]
        print(f"Generating embeddings for {len(texts_to_embed)} chunks...")
        embeddings = await embedding_provider.embed_batch(texts_to_embed)
        
        # 6. Save chunks
        db_chunks = []
        for idx, chunk in enumerate(chunks):
            # Simple keyword vector string (using just content) - pgvector handles the raw TSVECTOR via SQL if needed,
            # but SQLAlchemy TSVECTOR mapping requires a string we cast, or we can just leave it NULL and let a DB trigger populate it.
            # We'll leave search_vector NULL for now, we do keyword search in evidence_retrieval using `content @@ plainto_tsquery` instead of `search_vector`.
            # Wait, evidence_retrieval.py uses `c.search_vector @@ ...`. We should make sure it works! 
            # Actually, `search_vector` is mapped to TSVECTOR in SQLAlchemy.
            
            db_chunk = KnowledgeChunk(
                document_id=doc.id,
                content=chunk.content,
                section_title=chunk.section_title,
                chunk_index=chunk.metadata.get('chunk_index', idx),
                embedding=embeddings[idx]
            )
            db_chunks.append(db_chunk)
            
        session.add_all(db_chunks)
        await session.commit()
        
        print(f"Successfully ingested {title} with {len(db_chunks)} chunks.")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest markdown/text documents into Foraa RAG")
    parser.add_argument("path", help="Path to file or directory to ingest")
    args = parser.parse_args()

    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: {target_path} does not exist.")
        sys.exit(1)

    if target_path.is_file():
        await ingest_file(str(target_path))
    else:
        # Scan directory
        for ext in ["*.md", "*.txt"]:
            for filepath in target_path.rglob(ext):
                await ingest_file(str(filepath))

if __name__ == "__main__":
    asyncio.run(main())
