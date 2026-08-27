import json
import logging
from typing import List

from groq import Groq
from ai.config import get_groq_api_key, get_model_name
from .schemas import ContradictionItem

logger = logging.getLogger("foraa.reasoning.contradiction")

CONTRADICTION_PROMPT = """You are a medical contradiction detector.
Analyze the user's message alongside their health context and medical evidence to find contradictions.
Example contradictions:
- User says they take 50mg, but context says 100mg.
- User says condition is resolved, but context says it is active.
- User report shows high iron, but they say they have iron deficiency.

If NO contradictions exist, output an empty JSON array: []

Otherwise, output a JSON array of objects:
[
  {
    "description": "User states they take 50mg Aspirin, but profile lists 100mg.",
    "conflicting_items": ["User Message", "Active Medications"],
    "severity": "HIGH",
    "resolution_required": true
  }
]
"""

class ContradictionDetector:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def detect(self, user_message: str, context_text: str) -> List[ContradictionItem]:
        if not self._client:
            return []

        try:
            payload = f"User Message:\n{user_message}\n\nContext:\n{context_text}"
            
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": CONTRADICTION_PROMPT},
                    {"role": "user", "content": payload}
                ],
                temperature=0.0,
                max_tokens=250,
            )
            
            content = completion.choices[0].message.content
            if content:
                import re
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                if content.startswith("```json"): content = content[7:]
                if content.startswith("```"): content = content[3:]
                if content.endswith("```"): content = content[:-3]
                
                data = json.loads(content.strip())
                
                return [
                    ContradictionItem(
                        description=c.get("description", ""),
                        conflicting_items=c.get("conflicting_items", []),
                        severity=c.get("severity", "LOW"),
                        resolution_required=bool(c.get("resolution_required", False))
                    )
                    for c in data
                ]
                
        except Exception as e:
            logger.error(f"Contradiction detection failed: {e}")
            
        return []
