from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import json
from services.embeddings import get_embedding_provider

class EvidenceItem(BaseModel):
    source_name: str
    title: str
    url: Optional[str]
    publication_date: Optional[str]
    section: Optional[str]
    content: str
    relevance_score: float
    source_quality: str
    retrieval_method: str
    citation_reference: str

class EvidencePack(BaseModel):
    query: str
    retrieved_items: List[EvidenceItem]
    source_count: int
    retrieval_metadata: dict

class EvidenceRetrievalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_provider = get_embedding_provider()

    async def search(self, query: str, limit: int = 5) -> EvidencePack:
        # 1. Embed the query
        query_embedding = await self.embedding_provider.embed_text(query)
        
        # 2. Hybrid search SQL
        # We combine pgvector cosine distance (<=>) and full text search rank (ts_rank)
        # Cosine distance: 0 is exact match, 2 is completely opposite. Similarity = 1 - distance.
        sql = text("""
            WITH semantic_search AS (
                SELECT 
                    c.id, 
                    1 - (c.embedding <=> CAST(:embedding AS vector)) AS semantic_score
                FROM knowledge_chunks c
                ORDER BY c.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit * 2
            ),
            keyword_search AS (
                SELECT 
                    c.id, 
                    ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', :query)) AS keyword_score
                FROM knowledge_chunks c
                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', :query)
                ORDER BY keyword_score DESC
                LIMIT :limit * 2
            )
            SELECT 
                c.id,
                c.content,
                c.section_title,
                d.title,
                d.url,
                d.publication_date,
                s.name as source_name,
                s.trust_level,
                COALESCE(ss.semantic_score, 0) as sem_score,
                COALESCE(ks.keyword_score, 0) as kw_score,
                -- Combined score: roughly normalize and add
                (COALESCE(ss.semantic_score, 0) * 0.7) + (COALESCE(ks.keyword_score, 0) * 0.3) as final_score
            FROM knowledge_chunks c
            JOIN knowledge_documents d ON c.document_id = d.id
            JOIN medical_sources s ON d.source_id = s.id
            LEFT JOIN semantic_search ss ON c.id = ss.id
            LEFT JOIN keyword_search ks ON c.id = ks.id
            WHERE ss.id IS NOT NULL OR ks.id IS NOT NULL
            ORDER BY final_score DESC
            LIMIT :limit
        """)

        # Execute query
        embedding_str = str(query_embedding)
        result = await self.db.execute(
            sql, 
            {"embedding": embedding_str, "query": query, "limit": limit}
        )
        rows = result.fetchall()

        items = []
        for i, row in enumerate(rows):
            pub_date = row.publication_date.isoformat() if row.publication_date else None
            # Decide primary retrieval method for transparency
            method = "hybrid"
            if row.sem_score > 0 and row.kw_score == 0:
                method = "semantic"
            elif row.kw_score > 0 and row.sem_score == 0:
                method = "keyword"
                
            item = EvidenceItem(
                source_name=row.source_name,
                title=row.title,
                url=row.url,
                publication_date=pub_date,
                section=row.section_title,
                content=row.content,
                relevance_score=float(row.final_score),
                source_quality=row.trust_level,
                retrieval_method=method,
                citation_reference=f"[{i+1}] {row.source_name} - {row.title}"
            )
            items.append(item)

        pack = EvidencePack(
            query=query,
            retrieved_items=items,
            source_count=len(set([i.source_name for i in items])),
            retrieval_metadata={"limit": limit, "returned": len(items)}
        )
        return pack
