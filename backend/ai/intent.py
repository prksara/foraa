import json
import logging
from typing import Dict, Any, List

from groq import Groq
from .config import get_groq_api_key, get_model_name

logger = logging.getLogger("foraa.ai.intent")

INTENT_PROMPT = """You are a fast intent classifier for a health AI.
Given the user's message, output a JSON object with the following keys:
- "categories": A list of strings. Choose from: [general_health, symptoms, nutrition, fitness, medications, lab_results, conditions, prevention, mental_wellbeing, report_interpretation, personal_health, emergency_or_urgent, greeting, other]
- "needs_evidence": A boolean. True ONLY if the query explicitly asks about a specific disease, medical condition, treatment, drug, or makes a factual medical claim requiring scientific evidence to verify. Set to False for greetings, general chatting, small talk, personal UI questions, or basic wellness questions that don't need clinical references.
- "needs_profile": A boolean. True if the query requires knowing the user's personal context (allergies, medications, goals, age, sex) to answer properly.
- "context_selection": A list of strings. Select which data modules are necessary for the query. Choose from: ["profile", "conditions", "allergies", "medications", "goals", "measurements", "timeline"]. Only select the modules explicitly relevant to the query. If the user asks for a general summary, include all relevant ones. If needs_profile is false, output [].

Only output valid JSON. Do not include markdown formatting or explanations.

Example 1:
User: "Hi there! How are you?"
Output: {"categories": ["greeting"], "needs_evidence": false, "needs_profile": false, "context_selection": []}

Example 2:
User: "Based on my peanut allergy, what protein can I eat?"
Output: {"categories": ["nutrition", "personal_health"], "needs_evidence": false, "needs_profile": true, "context_selection": ["allergies", "profile"]}

Example 3:
User: "What is the recommended dose of Aspirin for a heart attack?"
Output: {"categories": ["medications", "emergency_or_urgent"], "needs_evidence": true, "needs_profile": false, "context_selection": []}
"""

class IntentAnalyzer:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        # Using the same configured model as the rest of the application
        self._model = get_model_name()

    def analyze(self, user_message: str) -> Dict[str, Any]:
        """
        Synchronously analyzes the intent. In a high-traffic app this would be async, 
        but Groq python client is sync by default unless AsyncGroq is used.
        Our AIService currently uses sync Groq client too.
        """
        default_intent = {
            "categories": ["other"],
            "needs_evidence": True, # Fail safe
            "needs_profile": True,   # Fail safe
            "context_selection": ["profile", "conditions", "allergies", "medications", "goals", "measurements", "timeline"] # Fail safe
        }
        
        if not self._client or not user_message.strip():
            return default_intent

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": INTENT_PROMPT},
                    {"role": "user", "content": user_message.strip()},
                ],
                temperature=0.0,
                max_tokens=150,
            )
            
            content = completion.choices[0].message.content
            if content:
                # Strip think blocks which break JSON parsing
                import re
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                
                # Strip backticks if the model wraps the JSON
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                
                return json.loads(content.strip())
                
        except Exception as e:
            print(f"Intent analysis failed with model {self._model}: {e}")
            logger.error(f"Intent analysis failed with model {self._model}: {e}")
            
        return default_intent
