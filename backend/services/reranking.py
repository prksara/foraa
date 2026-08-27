import json
import logging
from typing import List

from database.models import KnowledgeChunk
from services.evidence_retrieval import EvidenceItem
from ai.service import AIService

logger = logging.getLogger("foraa.reranking")

RERANK_PROMPT = """You are a medical evidence reranker.
Given a user query and a list of retrieved evidence passages, assign a relevance score from 0.0 to 1.0 for each passage based on how well it answers or relates to the user's query. 0.0 means completely irrelevant, 1.0 means perfectly answers the query.

Output ONLY a JSON array of objects with "id" and "score" keys.

Example:
[
  {"id": 0, "score": 0.95},
  {"id": 1, "score": 0.2}
]
"""

class Reranker:
    def __init__(self, ai_service: AIService = None):
        self.ai_service = ai_service or AIService()

    def rerank(self, query: str, items: List[EvidenceItem]) -> List[EvidenceItem]:
        """
        Reranks a list of EvidenceItems based on their relevance to the query.
        Falls back to the original ordering if LLM reranking fails.
        """
        if not items:
            return items

        # Construct payload
        evidence_text = ""
        for idx, item in enumerate(items):
            evidence_text += f"\n--- Passage ID {idx} ---\nTitle: {item.title}\nContent: {item.content}\n"

        user_message = f"Query: {query}\n\nEvidence:\n{evidence_text}"
        
        # Sort by default initially
        items.sort(key=lambda x: x.relevance_score, reverse=True)

        try:
            # We don't want to use standard generate_response because it has the persona prompt
            # We will use the underlying client directly for a one-off structured output
            completion = self.ai_service._client.chat.completions.create(
                model=self.ai_service._model,
                messages=[
                    {"role": "system", "content": RERANK_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.0,
                max_tokens=300
            )
            
            content = completion.choices[0].message.content
            
            # Clean up potential markdown blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            scores = json.loads(content.strip())
            
            # Update scores
            score_map = {obj["id"]: obj["score"] for obj in scores if "id" in obj and "score" in obj}
            
            for idx, item in enumerate(items):
                if idx in score_map:
                    # Give it a reranked score
                    item.relevance_score = float(score_map[idx])
                    item.retrieval_method = "hybrid+llm_reranked"
                    
            # Re-sort based on new scores
            items.sort(key=lambda x: x.relevance_score, reverse=True)
            
        except Exception as e:
            logger.warning(f"LLM Reranking failed, using original retrieval scores: {e}")
            
        return items
