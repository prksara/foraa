import json
import logging
from typing import Optional

from groq import Groq
from ai.config import get_groq_api_key, get_model_name
from .schemas import MissingInformation

logger = logging.getLogger("foraa.reasoning.missing_information")

MISSING_INFO_PROMPT = """You are a missing information detector for a medical AI.
Determine if critical information is missing from the user's message or context that is REQUIRED to answer safely.
Examples of critical missing info:
- User asks about medication dosage, but doesn't state their age/weight or current dose.
- User asks about a symptom's cause, but doesn't state duration or severity.

If NOTHING critical is missing, output:
{
  "missing_items": [],
  "status": "irrelevant"
}

If something is missing, output:
{
  "missing_items": ["duration of symptoms", "fever presence"],
  "status": "required"
}
"""

class MissingInformationDetector:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def detect(self, user_message: str, context_text: str) -> Optional[MissingInformation]:
        if not self._client:
            return None

        try:
            payload = f"User Message:\n{user_message}\n\nContext:\n{context_text}"
            
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": MISSING_INFO_PROMPT},
                    {"role": "user", "content": payload}
                ],
                temperature=0.0,
                max_tokens=150,
            )
            
            content = completion.choices[0].message.content
            if content:
                import re
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                if content.startswith("```json"): content = content[7:]
                if content.startswith("```"): content = content[3:]
                if content.endswith("```"): content = content[:-3]
                
                data = json.loads(content.strip())
                
                return MissingInformation(
                    missing_items=data.get("missing_items", []),
                    status=data.get("status", "irrelevant")
                )
                
        except Exception as e:
            logger.error(f"Missing info detection failed: {e}")
            
        return None
