import json
import logging
from typing import List

from groq import Groq
from ai.config import get_groq_api_key, get_model_name

logger = logging.getLogger("foraa.reasoning.context_relevance")

RELEVANCE_PROMPT = """You are a medical context filter.
You will be given the user's message and a list of health context keys (e.g., conditions, medications, allergies, goals).
Your job is to return ONLY the keys that are medically relevant to answering the user's message.

For example, if the user asks about an allergic reaction to a new food, their "allergies" and "active_medications" are relevant, but their "goals" (e.g., run a 5k) are probably not.

Output ONLY a JSON array of strings containing the relevant keys.
Example: ["allergies", "active_conditions"]
"""

class ContextRelevanceScorer:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def score(self, user_message: str, available_keys: List[str]) -> List[str]:
        if not self._client or not available_keys:
            return available_keys

        try:
            payload = f"User Message: {user_message}\n\nAvailable Keys: {json.dumps(available_keys)}"
            
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": RELEVANCE_PROMPT},
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
                
                selected_keys = json.loads(content.strip())
                # Filter out hallucinations
                return [k for k in selected_keys if k in available_keys]
                
        except Exception as e:
            logger.error(f"Context relevance scoring failed: {e}")
            
        # Fail safe: return all
        return available_keys
