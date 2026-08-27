import json
import logging
from typing import Dict, Any

from groq import Groq
from ai.config import get_groq_api_key, get_model_name
from .schemas import IntentAnalysis, QueryCategory, QueryComplexity

logger = logging.getLogger("foraa.reasoning.classifier")

CLASSIFIER_PROMPT = """You are the initial routing classifier for a medical AI reasoning engine.
Given the user's message, classify the query using the following rules.

Output a valid JSON object matching this schema:
{
    "categories": ["list of relevant categories"],
    "complexity": "SIMPLE or COMPLEX",
    "needs_evidence": true/false,
    "needs_profile": true/false,
    "needs_reports": true/false
}

Categories to choose from: 
GENERAL_HEALTH, SYMPTOM, MEDICATION, LAB_RESULT, MEDICAL_REPORT, NUTRITION, FITNESS, MENTAL_WELLNESS, PREVENTION, LIFESTYLE, HEALTH_HISTORY, FOLLOW_UP, URGENT, OTHER

Complexity:
- SIMPLE: Casual chat, greetings, direct simple questions that do not require medical synthesis or retrieving past medical records (e.g., "Hi", "What is my age again?").
- COMPLEX: Any query involving symptoms, interpreting reports, resolving medication questions, or requiring medical evidence and deductive reasoning.

needs_evidence: True ONLY if answering requires medical science/evidence (e.g. treatments, side effects, disease information). False for personal data questions ("What did I eat yesterday?").
needs_profile: True if knowing the user's age, sex, conditions, allergies, or medications is necessary to answer safely.
needs_reports: True if the user asks about a test, lab result, or uploaded medical report.

Output ONLY JSON.
"""

class QueryClassifier:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def classify(self, user_message: str) -> IntentAnalysis:
        default_intent = IntentAnalysis(
            categories=[QueryCategory.OTHER],
            complexity=QueryComplexity.COMPLEX, # Safe default
            needs_evidence=True,
            needs_profile=True,
            needs_reports=False
        )
        
        if not self._client or not user_message.strip():
            return default_intent

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": CLASSIFIER_PROMPT},
                    {"role": "user", "content": user_message.strip()}
                ],
                temperature=0.0,
                max_tokens=250,
            )
            
            content = completion.choices[0].message.content
            if content:
                # Clean up json format
                import re
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                if content.startswith("```json"): content = content[7:]
                if content.startswith("```"): content = content[3:]
                if content.endswith("```"): content = content[:-3]
                
                data = json.loads(content.strip())
                
                # Parse back to Pydantic schema safely
                return IntentAnalysis(
                    categories=[QueryCategory(c) for c in data.get("categories", ["OTHER"]) if c in QueryCategory.__members__],
                    complexity=QueryComplexity(data.get("complexity", "COMPLEX")),
                    needs_evidence=bool(data.get("needs_evidence", True)),
                    needs_profile=bool(data.get("needs_profile", True)),
                    needs_reports=bool(data.get("needs_reports", False))
                )
                
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            
        return default_intent
