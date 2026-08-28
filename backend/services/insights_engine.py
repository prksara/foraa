import json
import hashlib
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, Measurement, HealthEvent, HealthInsight, Notification
from ai.config import get_groq_api_key, get_model_name
from groq import Groq

logger = logging.getLogger("foraa.services.insights")

PROACTIVE_INSIGHT_PROMPT = """You are a careful, conservative health AI insight engine.
Your job is to look at recent health measurements and events, and generate 0, 1, or 2 personalized insights.

Guidelines:
1. ONLY generate insights if there is a clear trend (e.g. 3 consecutive BP readings that are high) or a significant change.
2. DO NOT diagnose. Use phrasing like "Your recent blood pressure readings have been consistently elevated" rather than "You have hypertension."
3. DO NOT generate insights if the data is normal and unremarkable, unless it's a positive reinforcement of a goal.
4. Output as JSON with an array of "insights", where each insight has:
   - "type": One of [TREND, CHANGE, GOAL_PROGRESS, POTENTIAL_CONCERN, INFO]
   - "message": A short, clear, supportive 1-2 sentence message.
   - "confidence": Float between 0.0 and 1.0 (only output if confident > 0.8)

Example JSON:
{
  "insights": [
    {
      "type": "TREND",
      "message": "Your fasting glucose has remained stable below 100 mg/dL for the past 3 readings. Great job maintaining it!",
      "confidence": 0.95
    }
  ]
}

If no insights are warranted, output: {"insights": []}
"""

class InsightsEngine:
    def __init__(self):
        api_key = get_groq_api_key()
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = get_model_name()

    def _generate_hash(self, user_id: str, type: str, message: str) -> str:
        # A simple hash to avoid storing the exact same insight message twice for the same user
        raw = f"{user_id}:{type}:{message}".encode('utf-8')
        return hashlib.sha256(raw).hexdigest()

    async def evaluate_recent_data(self, db: AsyncSession, user_id: str):
        if not self._client:
            return

        # Fetch recent data to evaluate
        meas_stmt = select(Measurement).where(Measurement.user_id == user_id).order_by(Measurement.created_at.desc()).limit(10)
        meas_res = await db.execute(meas_stmt)
        measurements = meas_res.scalars().all()

        events_stmt = select(HealthEvent).where(HealthEvent.user_id == user_id).order_by(HealthEvent.event_date.desc()).limit(5)
        events_res = await db.execute(events_stmt)
        events = events_res.scalars().all()

        if not measurements and not events:
            return

        # Prepare context for LLM
        context_parts = []
        if measurements:
            context_parts.append("Recent Measurements:")
            for m in measurements:
                date_str = m.created_at.strftime("%Y-%m-%d") if m.created_at else "unknown"
                context_parts.append(f"- {date_str}: {m.type} = {m.value} {m.unit}")
        if events:
            context_parts.append("Recent Events:")
            for e in events:
                date_str = e.event_date.strftime("%Y-%m-%d") if e.event_date else "unknown"
                context_parts.append(f"- {date_str}: [{e.event_type}] {e.title}")
        
        data_context = "\n".join(context_parts)
        
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": PROACTIVE_INSIGHT_PROMPT},
                    {"role": "user", "content": f"User Data:\n{data_context}"},
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            content = completion.choices[0].message.content
            if content:
                result = json.loads(content)
                insights_data = result.get("insights", [])
                
                for item in insights_data:
                    # Validate
                    type_ = item.get("type", "INFO")
                    message = item.get("message", "")
                    confidence = item.get("confidence", 1.0)
                    
                    if not message or confidence < 0.8:
                        continue
                        
                    insight_hash = self._generate_hash(user_id, type_, message)
                    
                    # Check if exists
                    check_stmt = select(HealthInsight).where(HealthInsight.deduplication_hash == insight_hash)
                    check_res = await db.execute(check_stmt)
                    if check_res.scalar_one_or_none():
                        continue # Already generated this exact insight
                        
                    # Create Insight
                    new_insight = HealthInsight(
                        user_id=user_id,
                        type=type_,
                        message=message,
                        confidence=confidence,
                        deduplication_hash=insight_hash
                    )
                    db.add(new_insight)
                    
                    # Also create a notification
                    notification = Notification(
                        user_id=user_id,
                        type="INSIGHT",
                        title="New Health Insight",
                        message=message,
                        severity="normal",
                        source_id=new_insight.id
                    )
                    db.add(notification)
                    
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to evaluate insights: {e}")
