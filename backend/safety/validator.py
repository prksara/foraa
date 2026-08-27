import json
import logging
from typing import List, Dict

from groq import Groq
from ai.config import get_groq_api_key, get_model_name
from .schemas import ValidationResult, ClaimValidationResult

logger = logging.getLogger("foraa.safety.validator")

VALIDATOR_PROMPT = """You are the final safety validator for a medical AI's output.
Your job is to read the draft response and evaluate it against the available evidence and user context.

CRITICAL CHECKS:
1. CITATIONS: Did the response use a citation (e.g., [1]) that does not exist in the provided evidence metadata?
2. FALSE REASSURANCE: Did the response say "you're completely fine" or "there's no chance this is serious" when evidence is lacking?
3. OVER-ALARM: Did the response unnecessarily cause panic (e.g. "go to the ER immediately" for a common cold)?
4. CLAIMS: Does the response state any unsupported medical facts or fabricated lab values?

If the response is SAFE, output:
{
    "is_safe": true,
    "claims": [],
    "invalid_citations": [],
    "rewrite_required": false
}

If the response violates safety constraints, output:
{
    "is_safe": false,
    "claims": [{"claim": "You definitely have cancer", "status": "UNSUPPORTED", "reason": "Diagnosis based purely on symptoms without labs"}],
    "invalid_citations": ["[3]"],
    "rewrite_required": true,
    "rewrite_reason": "Fabricated citation and unsupported definitive diagnosis."
}
"""

class PostGenerationValidator:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def validate(self, draft_response: str, evidence_metadata: List[Dict] = None) -> ValidationResult:
        if not self._client or not draft_response.strip():
            return ValidationResult()

        try:
            evidence_str = json.dumps(evidence_metadata) if evidence_metadata else "No evidence provided."
            payload = f"Draft Response:\n{draft_response}\n\nEvidence Metadata:\n{evidence_str}"
            
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": VALIDATOR_PROMPT},
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
                
                claims = []
                for c in data.get("claims", []):
                    claims.append(ClaimValidationResult(
                        claim=c.get("claim", ""),
                        status=c.get("status", "UNSUPPORTED"),
                        reason=c.get("reason", "")
                    ))
                    
                return ValidationResult(
                    is_safe=bool(data.get("is_safe", True)),
                    claims=claims,
                    invalid_citations=data.get("invalid_citations", []),
                    rewrite_required=bool(data.get("rewrite_required", False)),
                    rewrite_reason=data.get("rewrite_reason", None)
                )
                
        except Exception as e:
            logger.error(f"Post-generation validation failed: {e}")
            
        return ValidationResult()
