import json
import logging

from groq import Groq
from ai.config import get_groq_api_key, get_model_name
from .schemas import ValidationStatus

logger = logging.getLogger("foraa.reasoning.validator")

VALIDATOR_PROMPT = """You are a final safety and logic validator for a medical AI's output.
Your job is to read the draft response and determine if it violates any safety constraints.

Constraints:
1. Did the response invent a citation that was not provided?
2. Did the response invent a lab value or medical fact not in the context?
3. Did the response state a definitive diagnosis based purely on symptoms?
4. Did the response prescribe a medication dose change without a doctor's explicit prior order in the context?
5. Did the response fail to escalate a clear emergency?

If the response is SAFE and VALID, output:
{"is_valid": true, "reason": ""}

If the response VIOLATES constraints, output:
{"is_valid": false, "reason": "State which constraint was violated and why"}

Output ONLY valid JSON.
"""

class ResponseValidator:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def validate(self, draft_response: str) -> (ValidationStatus, str):
        """
        Validates the draft response.
        Returns (ValidationStatus.VALID, "") if ok, or (ValidationStatus.INVALID_RETRY, "reason") if failed.
        """
        if not self._client or not draft_response.strip():
            return ValidationStatus.VALID, ""

        try:
            payload = f"Draft Response:\n{draft_response}"
            
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": VALIDATOR_PROMPT},
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
                
                is_valid = bool(data.get("is_valid", True))
                reason = data.get("reason", "")
                
                if is_valid:
                    return ValidationStatus.VALID, ""
                else:
                    return ValidationStatus.INVALID_RETRY, reason
                
        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            
        # Fail open if the validator itself crashes to not break the app
        return ValidationStatus.VALID, ""
