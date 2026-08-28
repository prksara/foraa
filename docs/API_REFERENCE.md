# API Reference - Foraa Phase 10

## Health Endpoints
- `GET /health/summary` - Returns core metrics and profile data.
- `GET /health/insights` - Returns a list of `HealthInsight` objects.
- `GET /health/notifications` - Returns active notifications.
- `PUT /health/notifications/{id}/read` - Marks a notification as read.
- `GET /health/goals` - Fetch active and completed goals.
- `POST /health/goals` - Create a new goal.
- `PUT /health/goals/{id}` - Update a goal (e.g., add progress).
- `GET /health/memory` - View explicitly stored AI memories.
- `DELETE /health/memory/{id}` - Revoke an AI memory fact.

## Settings Endpoints
- `GET /settings/preferences` - Returns user preference state.
- `PUT /settings/preferences` - Updates `ai_data_pref`, `notif_health`, `notif_product`, etc.

## Background Services
- `InsightsEngine.evaluate_recent_data(db, user_id)`: Asynchronous task to evaluate health patterns without blocking API responses.
