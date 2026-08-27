import json
import logging
from typing import List, Dict

from groq import Groq
from ai.config import get_groq_api_key, get_model_name
from .schemas import SafetyClassificationResult, SafetyLevel, ConfidenceCategory

logger = logging.getLogger("foraa.safety.classifier")

RED_FLAG_CATEGORIES = [
    "SEVERE_BREATHING_DIFFICULTY",
    "SEVERE_CHEST_SYMPTOMS",
    "LOSS_OF_CONSCIOUSNESS",
    "SEVERE_NEUROLOGICAL_SYMPTOMS",
    "SUDDEN_SEVERE_SYMPTOMS",
    "MAJOR_BLEEDING",
    "SEVERE_ALLERGIC_REACTION",
    "POISONING_OVERDOSE",
    "SERIOUS_INJURY",
    "SUICIDAL_SELF_HARM",
    "MEDICATION_ADVERSE_REACTION"
]

SAFETY_PROMPT = """You are the pre-generation Safety Classifier for a medical AI.
You must read the user's message and determine if it represents an URGENT or EMERGENCY medical situation.

Rules:
1. Do NOT keyword-match harmless context (e.g. "My chest muscles hurt from pushups" is SAFE_GENERAL).
2. Look for severe, sudden, or life-threatening symptoms.
3. If the user mentions suicidal thoughts or self-harm, classify as EMERGENCY.

Output a valid JSON object:
{
    "level": "SAFE_GENERAL",
    "reasons": ["List of reasons for this classification"],
    "detected_signals": ["Any matching red flag categories"],
    "confidence_category": "HIGH",
    "recommended_action": "e.g. Advise calling 911, or None",
    "response_constraints": ["e.g. Do not attempt diagnosis. Be extremely concise."]
}
Options for level: SAFE_GENERAL, CAUTION, NEEDS_CLARIFICATION, PROFESSIONAL_REVIEW, URGENT, EMERGENCY
Options for confidence_category: HIGH, MODERATE, LOW

Available Red Flag Signals: {signals}
"""

class SafetyClassifier:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def classify(self, user_message: str, context_text: str = "") -> SafetyClassificationResult:
        default_result = SafetyClassificationResult(level=SafetyLevel.SAFE_GENERAL)
        
        if not self._client or not user_message.strip():
            return default_result

        try:
            prompt = SAFETY_PROMPT.replace("{signals}", str(RED_FLAG_CATEGORIES))
            payload = f"User Message:\n{user_message}\n\nHealth Context (if any):\n{context_text}"
            
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": prompt},
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
                
                # Safely parse back to schema
                return SafetyClassificationResult(
                    level=SafetyLevel(data.get("level", "SAFE_GENERAL")),
                    reasons=data.get("reasons", []),
                    detected_signals=data.get("detected_signals", []),
                    confidence_category=ConfidenceCategory(data.get("confidence_category", "HIGH")),
                    recommended_action=data.get("recommended_action", None),
                    response_constraints=data.get("response_constraints", [])
                )
                
        except Exception as e:
            logger.error(f"Safety classification failed: {e}")
            
        return default_result
