import json
import logging
import re
from typing import Dict, Any, Optional
from groq import Groq
from ai.config import get_groq_api_key, get_model_name

logger = logging.getLogger("foraa.services.health_log_parser")

LOG_PARSER_PROMPT = """You are an entity extraction engine for a health app.
The user is explicitly stating a health measurement, symptom, or lifestyle entry.
Extract the relevant details into a valid JSON object.

Allowed output schema:
{
    "category": "measurement" | "lifestyle" | "symptom",
    "type": "weight" | "height" | "heart_rate" | "blood_pressure" | "temperature" | "blood_glucose" | "oxygen_saturation" | "hydration" | "sleep" | "exercise" | "nutrition" | "symptom_name",
    "value": float (if applicable),
    "secondary_value": float (if applicable, e.g. diastolic),
    "unit": string (e.g. "kg", "lbs", "mmHg", "hours", "L", "bpm"),
    "title": string (if it is a symptom or lifestyle event)
}

Example 1:
User: "I weigh 150 lbs"
Output: {"category": "measurement", "type": "weight", "value": 150, "unit": "lbs"}

Example 2:
User: "My blood pressure is 120/80"
Output: {"category": "measurement", "type": "blood_pressure", "value": 120, "secondary_value": 80, "unit": "mmHg"}

Example 3:
User: "I just slept 7 hours"
Output: {"category": "lifestyle", "type": "sleep", "value": 7, "unit": "hours"}

Example 4:
User: "I have a severe headache"
Output: {"category": "symptom", "type": "symptom_name", "title": "severe headache"}

Output ONLY valid JSON.
"""

class HealthLogParser:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def _rule_based_fallback(self, text: str) -> Optional[Dict[str, Any]]:
        """Fallback parser using regex patterns for reliable extraction."""
        t = text.lower().strip()

        # Blood pressure
        bp_match = re.search(r'(?:bp|blood\s*pressure)\s*(?:is|:)?\s*(-?\d+)\s*(?:/|over)\s*(-?\d+)', t)
        if bp_match:
            return {
                "category": "measurement",
                "type": "blood_pressure",
                "metric_type": "blood_pressure",
                "value": float(bp_match.group(1)),
                "secondary_value": float(bp_match.group(2)),
                "unit": "mmHg"
            }

        # Weight
        wt_match = re.search(r'(?:weigh|weight)\s*(?:is|:)?\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z]+)?', t)
        if wt_match:
            unit = wt_match.group(2) or "lbs"
            return {
                "category": "measurement",
                "type": "weight",
                "metric_type": "weight",
                "value": float(wt_match.group(1)),
                "unit": unit
            }

        # Heart rate
        hr_match = re.search(r'(?:heart\s*rate|hr|pulse)\s*(?:is|:)?\s*(-?\d+)\s*([a-zA-Z]+)?', t)
        if hr_match:
            return {
                "category": "measurement",
                "type": "heart_rate",
                "metric_type": "heart_rate",
                "value": float(hr_match.group(1)),
                "unit": hr_match.group(2) or "bpm"
            }

        # Sleep
        sleep_match = re.search(r'(?:slept|sleep)\s*(?:for)?\s*(-?\d+(?:\.\d+)?)\s*(?:hours|hrs|hr)?', t)
        if sleep_match:
            val = float(sleep_match.group(1))
            return {
                "category": "lifestyle",
                "type": "sleep",
                "metric_type": "sleep",
                "value": val,
                "unit": "hours",
                "summary": f"Slept for {val} hours"
            }

        return None

    def parse(self, text: str) -> Optional[Dict[str, Any]]:
        if not text or not text.strip():
            return None

        if self._client:
            try:
                completion = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": LOG_PARSER_PROMPT},
                        {"role": "user", "content": text.strip()}
                    ],
                    temperature=0.0,
                    max_tokens=150,
                )
                
                content = completion.choices[0].message.content
                if content:
                    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                    if content.startswith("```json"): content = content[7:]
                    if content.startswith("```"): content = content[3:]
                    if content.endswith("```"): content = content[:-3]
                    
                    data = json.loads(content.strip())
                    if "type" in data and "metric_type" not in data:
                        data["metric_type"] = data["type"]
                    return data
            except Exception as e:
                logger.warning(f"LLM health log parsing failed ({e}), using fallback parser.")

        return self._rule_based_fallback(text)
