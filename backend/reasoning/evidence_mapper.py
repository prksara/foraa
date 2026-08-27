import json
import logging
from typing import List, Dict

from groq import Groq
from ai.config import get_groq_api_key, get_model_name

logger = logging.getLogger("foraa.reasoning.evidence_mapper")

MAPPER_PROMPT = """You are a medical evidence mapper.
Given a draft answer or a list of claims, and the available medical evidence + user context, map each claim to its supporting source.
If a claim has NO support in the provided evidence or context, you MUST flag it.

Output a JSON array of objects with this schema:
[
  {
    "claim": "You have a peanut allergy.",
    "supported_by": ["USER_CONTEXT"],
    "is_supported": true
  },
  {
    "claim": "Low ferritin causes fatigue.",
    "supported_by": ["MEDICAL_EVIDENCE: Guideline 12"],
    "is_supported": true
  }
]
"""

class EvidenceMapper:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def map_evidence(self, claims: List[str], evidence_text: str, context_text: str) -> List[Dict]:
        if not self._client or not claims:
            return []

        try:
            payload = f"Claims:\n{json.dumps(claims)}\n\nMedical Evidence:\n{evidence_text}\n\nUser Context:\n{context_text}"
            
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": MAPPER_PROMPT},
                    {"role": "user", "content": payload}
                ],
                temperature=0.0,
                max_tokens=400,
            )
            
            content = completion.choices[0].message.content
            if content:
                import re
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                if content.startswith("```json"): content = content[7:]
                if content.startswith("```"): content = content[3:]
                if content.endswith("```"): content = content[:-3]
                
                return json.loads(content.strip())
                
        except Exception as e:
            logger.error(f"Evidence mapping failed: {e}")
            
        return []
