import json
import logging
from typing import List, Dict

from groq import Groq
from ai.config import get_groq_api_key, get_model_name

logger = logging.getLogger("foraa.safety.medication")

MEDICATION_PROMPT = """You are a medication safety pre-checker.
Read the user's message and their active medications and allergies context.
Determine if the message involves:
1. Stopping a prescribed medication.
2. Changing the dose of a prescribed medication.
3. Combining medications that could interact dangerously.
4. Asking about a medication the user is allergic to.

If ANY of these apply, output a valid JSON object:
{
    "is_safe": false,
    "confidence_level": "HIGH",
    "alerts": ["Amoxicillin contraindication due to Penicillin allergy"],
    "interaction_risk": "SEVERE",
    "recommendation_override": "Flag as Caution"
}
Options for confidence_level: HIGH, MODERATE, LOW
Options for interaction_risk: NONE, MILD, MODERATE, SEVERE

Otherwise, output:
{
    "is_safe": true,
    "medication_alerts": [],
    "requires_professional_review": false
}
"""

class MedicationSafetyChecker:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def check(self, user_message: str, context_text: str = "") -> Dict:
        default_result = {"is_safe": True, "medication_alerts": [], "requires_professional_review": False}
        
        if not self._client or not user_message.strip():
            return default_result

        try:
            payload = f"User Message:\n{user_message}\n\nHealth Context (Medications/Allergies):\n{context_text}"
            
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": MEDICATION_PROMPT},
                    {"role": "user", "content": payload}
                ],
                temperature=0.0,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            
            content = completion.choices[0].message.content
            if content:
                import re
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                if content.startswith("```json"): content = content[7:]
                if content.startswith("```"): content = content[3:]
                if content.endswith("```"): content = content[:-3]
                
                data = json.loads(content.strip())
                return {
                    "is_safe": bool(data.get("is_safe", True)),
                    "medication_alerts": data.get("medication_alerts", []),
                    "requires_professional_review": bool(data.get("requires_professional_review", False))
                }
                
        except Exception as e:
            logger.error(f"Medication safety check failed: {e}")
            
        return default_result
