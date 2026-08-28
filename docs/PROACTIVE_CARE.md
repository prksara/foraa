# Foraa Proactive Care Engine

## Overview
The Proactive Care Engine shifts Foraa from being purely reactive to an active participant in the user's health journey.

## Workflow
1. **Trigger:** The engine is triggered asynchronously in the background via `asyncio.create_task()` whenever a user adds new health data (Measurements, Timeline Events, Goals).
2. **Data Aggregation:** `InsightsEngine.evaluate_recent_data` aggregates the user's recent data (7 days by default) along with their active goals and base profile.
3. **LLM Evaluation:** Passes the aggregated context to Llama-3.1-8b-instant, asking it to detect correlations, progress against goals, or potential health risks.
4. **Insight Generation:** Returns structured JSON containing `insights` and `notifications`.
5. **Deduplication:** The engine checks recent insights in the database to prevent spamming the user with duplicate alerts.
6. **Persistence:** The unique insights and notifications are saved to `HealthInsight` and `Notification` models, respectively.

## User Experience
- The `Home` Dashboard renders active goals with progress bars.
- "Recent Insights" are surfaced directly on the dashboard.
- Users receive non-intrusive notifications for high-priority health reminders.
