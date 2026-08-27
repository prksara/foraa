import json
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import HealthEvent

logger = logging.getLogger("foraa.memory_extraction")

class MemoryExtractor:
    def __init__(self, ai_service):
        self.ai_service = ai_service

    async def extract_health_events(
        self, 
        message_content: str, 
        user_id: str, 
        source_id: str,
        db: AsyncSession
    ) -> List[HealthEvent]:
        """
        Evaluates a user message to extract clinically relevant health facts
        into a structured list of HealthEvent objects, then persists them to the DB.
        """
        system_prompt = """
You are a highly precise medical context extraction engine for a longitudinal health record.
Your goal is to extract permanent, clinically relevant health information from user chat messages.
This information will be stored in a permanent health timeline.

Rules:
1. ONLY extract meaningful health facts: diagnoses, symptoms, measurements, medications, allergies, health goals, or lifestyle facts.
2. DO NOT extract greetings ("hello", "thanks"), general questions ("what is vitamin D?"), or transient chatter.
3. If the user statement is NOT a permanent/relevant health fact, return an empty array for extractions.
4. Extract structured data accurately based on the user's explicit statements.

Output strictly as JSON matching this schema:
{
  "extractions": [
    {
      "event_type": "symptom", // Can be: symptom, diagnosis, medication, allergy, measurement, lifestyle, goal, observation, other
      "title": "Short descriptive title (e.g. Diagnosed with Asthma)",
      "description": "More detailed description if needed",
      "structured_data": {} // Optional key-value pairs (e.g. {"value": 74, "unit": "kg"})
    }
  ]
}
Return only the raw JSON. Do not use markdown blocks.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract health facts from this message:\n\n\"{message_content}\""}
        ]

        extracted_events = []
        try:
            full_response = ""
            for chunk in self.ai_service.generate_stream(messages):
                full_response += chunk

            cleaned = full_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
                
            result = json.loads(cleaned.strip())
            
            for ext in result.get("extractions", []):
                event = HealthEvent(
                    user_id=user_id,
                    event_type=ext.get("event_type", "other"),
                    title=ext.get("title", "Health Event"),
                    description=ext.get("description"),
                    source_type="conversation",
                    source_id=source_id,
                    confidence=0.9, # AI extraction confidence
                    structured_data=ext.get("structured_data", {})
                )
                db.add(event)
                extracted_events.append(event)
            
            if extracted_events:
                await db.commit()
                for e in extracted_events:
                    await db.refresh(e)
                logger.info(f"Extracted {len(extracted_events)} health events for user {user_id}")
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from AI memory extraction: {full_response}")
        except Exception as e:
            logger.error(f"Error during memory extraction: {e}")
            
        return extracted_events
