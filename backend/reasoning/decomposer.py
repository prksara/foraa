import json
import logging
from typing import List

from groq import Groq
from ai.config import get_groq_api_key, get_model_name
from .schemas import SubQuestion

logger = logging.getLogger("foraa.reasoning.decomposer")

DECOMPOSER_PROMPT = """You are a medical reasoning decomposer.
Your job is to break down complex user questions into smaller, atomic sub-questions that must be answered to form a complete, safe, and accurate final response.

If the question is simple, you can output a single sub-question.
If the question involves multiple symptoms, a lab result plus a symptom, or a medication interaction, break it down logically.

Output ONLY a JSON array of objects with the following schema:
[
  {
    "id": "q1",
    "text": "What does a low ferritin level indicate?",
    "type": "EVIDENCE_LOOKUP",
    "evidence_required": true,
    "context_required": false
  },
  {
    "id": "q2",
    "text": "Is the user currently taking any iron supplements?",
    "type": "USER_CONTEXT",
    "evidence_required": false,
    "context_required": true
  }
]

Sub-question types: EVIDENCE_LOOKUP, USER_CONTEXT, REPORT_ANALYSIS, SYNTHESIS, CLARIFICATION.
Output ONLY JSON.
"""

class QuestionDecomposer:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def decompose(self, user_message: str) -> List[SubQuestion]:
        default_subq = [SubQuestion(id="q1", text=user_message, type="SYNTHESIS", evidence_required=True, context_required=True)]
        
        if not self._client or not user_message.strip():
            return default_subq

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": DECOMPOSER_PROMPT},
                    {"role": "user", "content": user_message.strip()}
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
                
                data = json.loads(content.strip())
                
                questions = []
                for idx, item in enumerate(data):
                    questions.append(SubQuestion(
                        id=item.get("id", f"q{idx}"),
                        text=item.get("text", ""),
                        type=item.get("type", "SYNTHESIS"),
                        evidence_required=bool(item.get("evidence_required", False)),
                        context_required=bool(item.get("context_required", False))
                    ))
                return questions if questions else default_subq
                
        except Exception as e:
            logger.error(f"Decomposition failed: {e}")
            
        return default_subq
