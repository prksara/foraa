from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from database.models import Measurement, Lifestyle

class TrendAnalysisService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def get_measurement_trend(self, metric_type: str, days: int = 30) -> Dict[str, Any]:
        """
        Calculate trend for numerical measurements (e.g., weight, blood_pressure, heart_rate).
        For blood pressure, we separate systolic and diastolic based on secondary_value.
        """
        now = datetime.utcnow()
        current_period_start = now - timedelta(days=days)
        previous_period_start = current_period_start - timedelta(days=days)

        # Base query for the user and metric type
        base_query = select(Measurement).where(
            Measurement.user_id == self.user_id,
            Measurement.type == metric_type
        ).order_by(Measurement.measured_at.asc())

        # Fetch current period data
        current_query = base_query.where(Measurement.measured_at >= current_period_start)
        current_result = await self.db.execute(current_query)
        current_data = current_result.scalars().all()

        # Fetch previous period data
        previous_query = base_query.where(
            Measurement.measured_at >= previous_period_start,
            Measurement.measured_at < current_period_start
        )
        previous_result = await self.db.execute(previous_query)
        previous_data = previous_result.scalars().all()

        if not current_data:
            return {
                "metric": metric_type,
                "data_points": [],
                "current_avg": None,
                "previous_avg": None,
                "percent_change": None,
                "direction": "stable",
                "min": None,
                "max": None
            }

        # Calculate for primary value (e.g., weight, systolic BP)
        current_values = [m.value for m in current_data]
        previous_values = [m.value for m in previous_data]

        current_avg = sum(current_values) / len(current_values)
        previous_avg = sum(previous_values) / len(previous_values) if previous_values else None

        percent_change = None
        direction = "stable"
        if previous_avg and previous_avg != 0:
            percent_change = ((current_avg - previous_avg) / previous_avg) * 100
            if percent_change > 1:
                direction = "up"
            elif percent_change < -1:
                direction = "down"

        data_points = [{"date": m.measured_at.isoformat(), "value": m.value, "secondary_value": m.secondary_value} for m in current_data]

        return {
            "metric": metric_type,
            "data_points": data_points,
            "current_avg": round(current_avg, 2),
            "previous_avg": round(previous_avg, 2) if previous_avg else None,
            "percent_change": round(percent_change, 2) if percent_change else None,
            "direction": direction,
            "min": round(min(current_values), 2),
            "max": round(max(current_values), 2),
            "unit": current_data[0].unit if current_data else ""
        }

    async def get_lifestyle_trend(self, category: str, days: int = 30) -> Dict[str, Any]:
        """
        Calculate trends for lifestyle metrics that contain numeric summaries (e.g. sleep hours).
        Extracts numeric values from 'summary' (e.g. '7.5 hours').
        """
        now = datetime.utcnow()
        current_period_start = now - timedelta(days=days)
        previous_period_start = current_period_start - timedelta(days=days)

        base_query = select(Lifestyle).where(
            Lifestyle.user_id == self.user_id,
            Lifestyle.category == category
        ).order_by(Lifestyle.created_at.asc())

        current_query = base_query.where(Lifestyle.created_at >= current_period_start)
        current_result = await self.db.execute(current_query)
        current_data = current_result.scalars().all()

        previous_query = base_query.where(
            Lifestyle.created_at >= previous_period_start,
            Lifestyle.created_at < current_period_start
        )
        previous_result = await self.db.execute(previous_query)
        previous_data = previous_result.scalars().all()

        import re

        def extract_numeric(text: str) -> Optional[float]:
            if not text: return None
            match = re.search(r'([0-9]*\.?[0-9]+)', text)
            return float(match.group(1)) if match else None

        # Filter out entries where we can't extract a numeric value
        current_parsed = [(d.created_at, extract_numeric(d.summary)) for d in current_data]
        current_parsed = [d for d in current_parsed if d[1] is not None]

        previous_parsed = [extract_numeric(d.summary) for d in previous_data]
        previous_parsed = [v for v in previous_parsed if v is not None]

        if not current_parsed:
            return {
                "metric": category,
                "data_points": [],
                "current_avg": None,
                "previous_avg": None,
                "percent_change": None,
                "direction": "stable",
                "min": None,
                "max": None
            }

        current_values = [d[1] for d in current_parsed]
        current_avg = sum(current_values) / len(current_values)
        previous_avg = sum(previous_parsed) / len(previous_parsed) if previous_parsed else None

        percent_change = None
        direction = "stable"
        if previous_avg and previous_avg != 0:
            percent_change = ((current_avg - previous_avg) / previous_avg) * 100
            if percent_change > 1:
                direction = "up"
            elif percent_change < -1:
                direction = "down"

        data_points = [{"date": d[0].isoformat(), "value": d[1]} for d in current_parsed]

        return {
            "metric": category,
            "data_points": data_points,
            "current_avg": round(current_avg, 2),
            "previous_avg": round(previous_avg, 2) if previous_avg else None,
            "percent_change": round(percent_change, 2) if percent_change else None,
            "direction": direction,
            "min": round(min(current_values), 2),
            "max": round(max(current_values), 2),
            "unit": "parsed"
        }
